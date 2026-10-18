package org.d2r.android.port;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.security.*;
import com.sun.net.httpserver.HttpServer;

public class GitHubDataTest {
    public static void main(String[] args) throws Exception {
        byte[] data = "a real streamed package fixture".getBytes("UTF-8");
        StringBuilder hash = new StringBuilder();
        for (byte b : MessageDigest.getInstance("SHA-256").digest(data)) hash.append(String.format("%02x", b & 255));
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/part", ex -> {
            String range = ex.getRequestHeaders().getFirst("Range");
            int offset = range == null ? 0 : Integer.parseInt(range.substring(6, range.length()-1));
            if (offset > 0) ex.getResponseHeaders().set("Content-Range", "bytes " + offset + "-" + (data.length-1) + "/" + data.length);
            ex.sendResponseHeaders(offset > 0 ? 206 : 200, data.length-offset);
            ex.getResponseBody().write(data, offset, data.length-offset); ex.close();
        });
        server.createContext("/ignore", ex -> { ex.sendResponseHeaders(200, data.length); ex.getResponseBody().write(data); ex.close(); });
        server.createContext("/bad", ex -> { ex.getResponseHeaders().set("Content-Range", "bytes 0-2/3"); ex.sendResponseHeaders(206,3); ex.getResponseBody().write(new byte[3]); ex.close(); });
        java.util.concurrent.atomic.AtomicInteger attempts = new java.util.concurrent.atomic.AtomicInteger();
        server.createContext("/flaky", ex -> {
            if (attempts.incrementAndGet() == 1) { ex.sendResponseHeaders(503,-1); ex.close(); return; }
            ex.sendResponseHeaders(200,data.length); ex.getResponseBody().write(data); ex.close();
        });
        server.start();
        File dir = Files.createTempDirectory("data-download-test").toFile();
        File file = new File(dir, "part");
        GitHubData.Sink sink = new GitHubData.Sink() { public boolean cancelled() { return false; } public void progress(long n) {} };
        String base = "http://127.0.0.1:" + server.getAddress().getPort();
        try {
            for (String path : new String[]{"/part", "/ignore"}) {
                Files.write(file.toPath(), java.util.Arrays.copyOf(data, 7));
                GitHubData.fetch(new URL(base+path),file,data.length,hash.toString(),sink);
                if (!java.util.Arrays.equals(data, Files.readAllBytes(file.toPath()))) throw new AssertionError("resume/replace");
            }
            // Completed cache is reused without opening any network connection.
            GitHubData.fetch(new URL("http://127.0.0.1:1"),file,data.length,hash.toString(),sink);
            Files.write(file.toPath(), new byte[data.length]);
            try { GitHubData.fetch(new URL(base+"/part"),file,data.length,hash.toString(),sink); throw new AssertionError("accepted corruption"); }
            catch (IOException expected) { if (file.exists()) throw new AssertionError("kept corrupt cache"); }
            Files.write(file.toPath(), new byte[7]);
            try { GitHubData.fetch(new URL(base+"/bad"),file,data.length,hash.toString(),sink); throw new AssertionError("accepted wrong range"); }
            catch (IOException expected) { if (file.length()!=7) throw new AssertionError("changed partial data"); }
            try { GitHubData.fetch(new URL(base+"/part"),file,data.length,hash.toString(),new GitHubData.Sink() { public boolean cancelled(){return true;} public void progress(long n){} }); throw new AssertionError("ignored cancellation"); }
            catch (IOException expected) {}
            File second = new File(dir,"second"); Files.write(file.toPath(),new byte[]{1,2}); Files.write(second.toPath(),new byte[]{3});
            try(InputStream in = GitHubData.open(new File[]{file,second})) { for(int n=1;n<=3;n++) if(in.read()!=n) throw new AssertionError("part order"); if(in.read()!=-1)throw new AssertionError(); }
            second.delete(); file.delete();
            GitHubData.fetchWithRetry(new URL(base+"/flaky"),file,data.length,hash.toString(),sink);
            if (attempts.get()!=2) throw new AssertionError("transient failure not retried");
            System.out.println("Resume, ignored range, corrupt cache, invalid range, cancel, concatenation passed");
        } finally { server.stop(0); file.delete(); dir.delete(); }
    }
}
