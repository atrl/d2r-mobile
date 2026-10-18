package org.d2r.android.port;

import java.io.*;
import java.net.*;
import java.security.*;
import java.util.*;

/** Immutable, SHA-256 pinned data release. APK updates do not redownload this data. */
final class GitHubData {
    static final long TOTAL = 6147543691L;
    private static final String BASE = "https://github.com/atrl/d2r-mobile/releases/download/v0.1.0-preview.5/d2r-package.zip.";
    private static final String[] HASHES = {
        "2f5011d292e05f45b6e513bf89361eaaf8d5e9ad5d45eb393459d52d1ef31926",
        "45b8e7c84c4c28341e4bd5d16f0ca0a9c03652101824170be43050e7805d22a5",
        "840592731609d9e47abd61f7d9bfb94c8e848613cfb342a2afe29953df96dece",
        "e6d5b6241ae8da95e886c46ecc816fb9cd210868c39ad0e88e5da7184f0db544"};
    interface Sink { boolean cancelled(); void progress(long bytes); }
    static void check(Sink sink) throws IOException {
        if (sink.cancelled()) throw new IOException("Download cancelled; tap Download game data to resume.");
    }
    static void fetch(URL url, File file, long size, String hash, Sink sink) throws Exception {
        long offset = file.isFile() ? file.length() : 0;
        if (offset > size) { if (!file.delete()) throw new IOException("Cannot reset download"); offset = 0; }
        if (offset < size) {
            check(sink);
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
                Thread.sleep(1000L * (attempt + 1));
            }
        }
    }
    static File[] download(File directory, Sink sink) throws Exception {
        if (!directory.isDirectory() && !directory.mkdirs()) throw new IOException("Cannot create download folder");
        File[] parts = new File[4];
        for (int i = 0; i < parts.length; i++) {
            String suffix = String.format(Locale.ROOT, "%03d", i + 1);
            parts[i] = new File(directory, "d2r-package.zip." + suffix);
            final long base = i * 1900000000L;
            fetchWithRetry(new URL(BASE + suffix), parts[i], i == 3 ? 447543691L : 1900000000L, HASHES[i], new Sink() {
                public boolean cancelled() { return sink.cancelled(); }
                public void progress(long bytes) { sink.progress(base + bytes); }
            });
        }
        return parts;
    }
    static InputStream open(File[] parts) throws IOException {
        Vector<InputStream> streams = new Vector<>();
        try { for (File part : parts) streams.add(new FileInputStream(part)); }
        catch (IOException e) { for (InputStream stream : streams) stream.close(); throw e; }
        return new SequenceInputStream(streams.elements());
    }
}
