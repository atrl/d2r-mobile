package org.d2r.android.port;
import java.io.*;
import java.net.*;
import java.nio.file.*;
import java.security.*;
import com.sun.net.httpserver.HttpServer;

public class GitHubDataTest {
    static void parallelParts() throws Exception {
        java.util.concurrent.ExecutorService handlers = java.util.concurrent.Executors.newCachedThreadPool();
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.setExecutor(handlers);
        java.util.concurrent.CountDownLatch overlap = new java.util.concurrent.CountDownLatch(2);
        java.util.concurrent.atomic.AtomicInteger active = new java.util.concurrent.atomic.AtomicInteger();
        java.util.concurrent.atomic.AtomicInteger peak = new java.util.concurrent.atomic.AtomicInteger();
        java.util.concurrent.atomic.AtomicBoolean concurrent = new java.util.concurrent.atomic.AtomicBoolean();
        java.util.concurrent.atomic.AtomicBoolean cancel = new java.util.concurrent.atomic.AtomicBoolean();
        byte[][] payload = new byte[4][16384];
        URL[] urls = new URL[4]; File[] files = new File[4]; long[] sizes = new long[4]; String[] hashes = new String[4];
        File dir = Files.createTempDirectory("parallel-parts").toFile();
        for (int i = 0; i < 4; i++) {
            java.util.Arrays.fill(payload[i], (byte)(i + 1));
            final int part = i;
            server.createContext("/" + i, ex -> {
                int n = active.incrementAndGet(); peak.accumulateAndGet(n, Math::max);
                try {
                    overlap.countDown();
                    if (overlap.await(3, java.util.concurrent.TimeUnit.SECONDS)) concurrent.set(true);
                    String range = ex.getRequestHeaders().getFirst("Range");
                    int offset = range == null ? 0 : Integer.parseInt(range.substring(6, range.length()-1));
                    if (offset > 0) ex.getResponseHeaders().set("Content-Range", "bytes " + offset + "-16383/16384");
                    ex.sendResponseHeaders(offset > 0 ? 206 : 200, 16384-offset);
                    for (int pos = offset; pos < 16384; pos += 1024) {
                        ex.getResponseBody().write(payload[part], pos, Math.min(1024, 16384-pos));
                        ex.getResponseBody().flush(); Thread.sleep(10);
                    }
                } catch (InterruptedException error) { Thread.currentThread().interrupt(); }
                catch (IOException error) { /* Client cancellation may close the response. */ }
                finally { active.decrementAndGet(); ex.close(); }
            });
            urls[i] = new URL("http://127.0.0.1:" + server.getAddress().getPort() + "/" + i);
            files[i] = new File(dir, "part" + i); sizes[i] = payload[i].length;
            StringBuilder hash = new StringBuilder();
            for (byte b : MessageDigest.getInstance("SHA-256").digest(payload[i])) hash.append(String.format("%02x", b & 255));
            hashes[i] = hash.toString();
            Files.write(files[i].toPath(), java.util.Arrays.copyOf(payload[i], 13));
        }
        server.start();
        java.util.List<Long> updates = new java.util.ArrayList<>();
        GitHubData.Sink sink = new GitHubData.Sink() {
            public boolean cancelled() { return cancel.get(); }
            public void progress(long bytes) { updates.add(bytes); }
        };
        try {
            GitHubData.fetchParts(urls, files, sizes, hashes, sink);
            if (!concurrent.get() || peak.get() != 2) throw new AssertionError("two-connection bound: " + peak);
            if (updates.get(0) != 52L || updates.get(updates.size()-1) != 65536L) throw new AssertionError("aggregate progress");
            for (int i=0;i<4;i++) if (!java.util.Arrays.equals(payload[i], Files.readAllBytes(files[i].toPath()))) throw new AssertionError("parallel resume integrity");
            try (InputStream in = GitHubData.open(files)) {
                for (int i=0;i<4;i++) for (int j=0;j<16384;j++) if (in.read()!=i+1) throw new AssertionError("parallel completion changed part order");
            }
            // An error must join all writers before returning; a later download may safely reuse the files.
            for (File f:files) f.delete();
            String[] bad = hashes.clone(); bad[0] = "bad hash";
            try { GitHubData.fetchParts(urls, files, sizes, bad, sink); throw new AssertionError("accepted bad part"); }
            catch (IOException expected) {}
            int before = updates.size(); Thread.sleep(100);
            if (updates.size()!=before) throw new AssertionError("worker still reporting after failure");
            GitHubData.fetchParts(urls, files, sizes, hashes, sink);
            for (File f:files) f.delete();
            GitHubData.Sink cancelling = new GitHubData.Sink() {
                public boolean cancelled() { return cancel.get(); }
                public void progress(long bytes) { if(bytes>0) cancel.set(true); }
            };
            try { GitHubData.fetchParts(urls, files, sizes, hashes, cancelling); throw new AssertionError("parallel cancellation ignored"); }
            catch (IOException expected) {}
            long retained = 0; for (File f:files) retained += f.length();
            if (retained<=0 || retained>=65536) throw new AssertionError("partial cancellation state");
            cancel.set(false); GitHubData.fetchParts(urls, files, sizes, hashes, sink);
            System.out.println("Parallel bound, resume, progress, ordered import, failure cleanup and cancellation passed");
        } finally {
            server.stop(0); handlers.shutdownNow();
            for (File f:files) f.delete(); dir.delete();
        }
    }
    public static void main(String[] args) throws Exception {
        parallelParts();
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
        java.util.List<String> phases = new java.util.ArrayList<>();
        java.util.List<Long> progress = new java.util.ArrayList<>();
        GitHubData.Sink sink = new GitHubData.Sink() {
            public boolean cancelled() { return false; }
            public void progress(long n) { progress.add(n); }
            public void phase(String phase, int attempt) { phases.add(phase + ":" + attempt); }
        };
        String base = "http://127.0.0.1:" + server.getAddress().getPort();
        try {
            for (String path : new String[]{"/part", "/ignore"}) {
                Files.write(file.toPath(), java.util.Arrays.copyOf(data, 7));
                GitHubData.fetch(new URL(base+path),file,data.length,hash.toString(),sink);
                if (!java.util.Arrays.equals(data, Files.readAllBytes(file.toPath()))) throw new AssertionError("resume/replace");
            }
            if (!progress.contains(7L) || !progress.contains((long)data.length)
                    || !phases.contains("connecting:0") || !phases.contains("verifying:0"))
                throw new AssertionError("missing resume progress or phase status");
            phases.clear();
            // Completed cache is reused without opening any network connection.
            GitHubData.fetch(new URL("http://127.0.0.1:1"),file,data.length,hash.toString(),sink);
            if (!phases.equals(java.util.Arrays.asList("verifying:0"))) throw new AssertionError("cached part status");
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
            if (!phases.contains("retrying:2")) throw new AssertionError("retry status missing");
            if (attempts.get()!=2) throw new AssertionError("transient failure not retried");
            System.out.println("Resume, ignored range, corrupt cache, invalid range, cancel, concatenation passed");
        } finally { server.stop(0); file.delete(); dir.delete(); }
    }
}
