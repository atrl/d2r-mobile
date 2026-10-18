package org.d2r.android.port;

import java.io.*;
import java.util.*;
import java.util.zip.*;

/** Separate cache variant: failed extraction never alters the original shaders. */
final class ShaderPatch {
    static final long SIZE = 142166085L;
    static final String HASH = "98078bfa0f0c25f23c9a10e5be48ee356e5e937937a76392544fc38d99c2a796";
    static final String URL = "https://github.com/atrl/d2r-mobile/releases/download/data-shaders64-v1/d2r-shaders64-v1.zip";
    static void install(File archive, File shaders) throws IOException {
        File target = new File(shaders, "subgroup64"), staging = new File(shaders, "subgroup64.pending");
        if (target.isDirectory()) return;
        delete(staging);
        if (!staging.mkdirs()) throw new IOException("Cannot create shader staging folder");
        try {
            Set<String> names = new HashSet<>(); long total = 0;
            try (ZipInputStream zip = new ZipInputStream(new BufferedInputStream(new FileInputStream(archive)))) {
                ZipEntry entry; byte[] buffer = new byte[262144];
                while ((entry = zip.getNextEntry()) != null) {
                    String name = entry.getName();
                    if (!(name.matches("[0-9a-f]{16}\\.(spv|meta)") || name.equals("host-profile.json") || name.equals("host-subgroup-size.txt"))
                            || !names.add(name) || names.size() > 13864)
                        throw new IOException("Invalid shader archive entry: " + name);
                    long size = 0;
                    try (OutputStream out = new FileOutputStream(new File(staging, name))) {
                        int n;
                        while ((n = zip.read(buffer)) != -1) {
                            size += n; total += n;
                            if (size > 32L * 1024 * 1024 || total > 500L * 1024 * 1024) throw new IOException("Shader archive exceeds size limit");
                            out.write(buffer, 0, n);
                        }
                    }
                }
            }
            if (names.size() != 13864) throw new IOException("Incomplete shader archive");
            for (String name : names) if (name.endsWith(".spv") && !names.contains(name.substring(0,16) + ".meta"))
                throw new IOException("Missing shader reflection");
            try (BufferedReader profile = new BufferedReader(new FileReader(new File(staging, "host-subgroup-size.txt")))) {
                if (!"64".equals(profile.readLine()) || profile.readLine() != null) throw new IOException("Wrong shader profile");
            }
            if (!staging.renameTo(target)) throw new IOException("Cannot publish shader cache");
        } finally { delete(staging); }
    }
    private static void delete(File file) throws IOException {
        if (!file.exists()) return;
        File[] children = file.listFiles();
        if (children != null) for (File child : children) delete(child);
        if (!file.delete()) throw new IOException("Cannot remove staging file");
    }
}
