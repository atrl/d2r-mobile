package org.d2r.android.port;

import java.io.*;
import java.net.*;
import java.security.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;

/** Immutable, SHA-256 pinned data release. APK updates do not redownload this data. */
final class GitHubData {
    static final long TOTAL = 6147543691L;
    private static final String BASE = "https://github.com/atrl/d2r-mobile/releases/download/v0.1.0-preview.5/d2r-package.zip.";
    private static final String[] HASHES = {
        "2f5011d292e05f45b6e513bf89361eaaf8d5e9ad5d45eb393459d52d1ef31926",
        "45b8e7c84c4c28341e4bd5d16f0ca0a9c03652101824170be43050e7805d22a5",
        "840592731609d9e47abd61f7d9bfb94c8e848613cfb342a2afe29953df96dece",
        "e6d5b6241ae8da95e886c46ecc816fb9cd210868c39ad0e88e5da7184f0db544"};
    interface Sink { boolean cancelled(); void progress(long bytes); default void phase(String phase, int attempt) {} }
    static void check(Sink sink) throws IOException {
        if (sink.cancelled()) throw new IOException("Download cancelled; tap Download game data to resume.");
    }
    static void fetch(URL url, File file, long size, String hash, Sink sink) throws Exception {
        check(sink);
        long offset = file.isFile() ? file.length() : 0;
        if (offset > size) { if (!file.delete()) throw new IOException("Cannot reset download"); offset = 0; }
        if (offset < size) {
            check(sink);
            sink.progress(offset);
            sink.phase("connecting", 0);
            HttpURLConnection c = (HttpURLConnection)url.openConnection();
            c.setConnectTimeout(15000); c.setReadTimeout(30000);
            c.setRequestProperty("Accept-Encoding", "identity");
            if (offset > 0) c.setRequestProperty("Range", "bytes=" + offset + "-");
            try {
                int status = c.getResponseCode();
                if (status == 200) offset = 0; // Server ignored Range: replace, never append.
                else if (status != 206 || !(("bytes " + offset + "-" + (size - 1) + "/" + size).equals(c.getHeaderField("Content-Range"))))
                    throw new IOException("Download HTTP " + status + " (invalid range)");
                try (InputStream in = c.getInputStream(); FileOutputStream out = new FileOutputStream(file, offset > 0)) {
                    byte[] buffer = new byte[256 * 1024]; int n;
                    while ((n = in.read(buffer)) != -1) {
                        check(sink);
                        if (offset + n > size) throw new IOException("Download exceeds expected size");
                        out.write(buffer, 0, n); offset += n; sink.progress(offset);
                    }
                }
            } finally { c.disconnect(); }
        }
        if (file.length() != size) throw new IOException("Incomplete download; retry to resume");
        sink.progress(size);
        sink.phase("verifying", 0);
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        try (InputStream in = new FileInputStream(file)) {
            byte[] buffer = new byte[256 * 1024]; int n;
            while ((n = in.read(buffer)) != -1) { check(sink); digest.update(buffer, 0, n); }
        }
        StringBuilder actual = new StringBuilder();
        for (byte b : digest.digest()) actual.append(String.format(Locale.ROOT, "%02x", b & 255));
        if (!hash.equals(actual.toString())) {
            if (!file.delete()) throw new IOException("Corrupt download could not be removed");
            throw new IOException("Download checksum mismatch; retry to download again");
        }
    }
    static void fetchWithRetry(URL url, File file, long size, String hash, Sink sink) throws Exception {
        for (int attempt = 0; ; attempt++) {
            try { fetch(url, file, size, hash, sink); return; }
            catch (IOException error) {
                check(sink);
                if (attempt == 2) throw error;
                sink.phase("retrying", attempt + 2);
                Thread.sleep(1000L * (attempt + 1));
            }
        }
    }
    static File[] download(File directory, Sink sink) throws Exception {
        if (!directory.isDirectory() && !directory.mkdirs()) throw new IOException("Cannot create download folder");
        File[] parts = new File[4];
        URL[] urls = new URL[4];
        long[] sizes = {1900000000L, 1900000000L, 1900000000L, 447543691L};
        for (int i = 0; i < parts.length; i++) {
            String suffix = String.format(Locale.ROOT, "%03d", i + 1);
            parts[i] = new File(directory, "d2r-package.zip." + suffix);
            urls[i] = new URL(BASE + suffix);
        }
        fetchParts(urls, parts, sizes, HASHES, sink);
        return parts;
    }
    // Independent files permit four connections without changing the package or its resume offsets.
    static void fetchParts(URL[] urls, File[] parts, long[] sizes, String[] hashes, Sink sink) throws Exception {
        if (urls.length != parts.length || sizes.length != parts.length || hashes.length != parts.length)
            throw new IllegalArgumentException("Part metadata length mismatch");
        check(sink);
        long[] downloaded = new long[parts.length];
        for (int i = 0; i < parts.length; i++)
            downloaded[i] = parts[i].isFile() && parts[i].length() <= sizes[i] ? parts[i].length() : 0;
        Object progressLock = new Object();
        AtomicBoolean stopping = new AtomicBoolean();
        AtomicReference<Exception> failure = new AtomicReference<>();
        ExecutorService pool = Executors.newFixedThreadPool(4);
        CompletionService<Void> finished = new ExecutorCompletionService<>(pool);
        try {
            for (int i = 0; i < parts.length; i++) {
                final int part = i;
                finished.submit(() -> {
                    try {
                        fetchWithRetry(urls[part], parts[part], sizes[part], hashes[part], new Sink() {
                            public boolean cancelled() { return stopping.get() || Thread.currentThread().isInterrupted() || sink.cancelled(); }
                            public void progress(long bytes) {
                                synchronized (progressLock) {
                                    downloaded[part] = bytes;
                                    long total = 0;
                                    for (long n : downloaded) total += n;
                                    sink.progress(total);
                                }
                            }
                            public void phase(String phase, int attempt) {
                                synchronized (progressLock) {
                                    // A verified part must not replace active download progress with a global verification message.
                                    if ("verifying".equals(phase))
                                        for (int j = 0; j < parts.length; j++) if (downloaded[j] != sizes[j]) return;
                                    sink.phase(phase, attempt);
                                }
                            }
                        });
                        return null;
                    } catch (Exception error) { failure.compareAndSet(null, error); stopping.set(true); throw error; }
                });
            }
            for (int i = 0; i < parts.length; i++) {
                try { finished.take().get(); }
                catch (ExecutionException error) {
                    if (failure.get() != null) throw failure.get();
                    if (error.getCause() instanceof Exception) throw (Exception)error.getCause();
                    throw new IOException("Download worker failed", error.getCause());
                }
            }
        } finally {
            stopping.set(true);
            pool.shutdownNow();
            // Wait for socket timeouts/worker cleanup before allowing another download to touch these files.
            boolean interrupted = false;
            while (!pool.isTerminated()) {
                try { pool.awaitTermination(1, TimeUnit.SECONDS); }
                catch (InterruptedException error) { interrupted = true; }
            }
            if (interrupted) Thread.currentThread().interrupt();
        }
    }
    static InputStream open(File[] parts) throws IOException {
        Vector<InputStream> streams = new Vector<>();
        try { for (File part : parts) streams.add(new FileInputStream(part)); }
        catch (IOException e) { for (InputStream stream : streams) stream.close(); throw e; }
        return new SequenceInputStream(streams.elements());
    }
}
