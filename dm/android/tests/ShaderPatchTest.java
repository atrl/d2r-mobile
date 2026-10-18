package org.d2r.android.port;
import java.io.*;
import java.nio.file.*;
import java.util.zip.*;
public final class ShaderPatchTest {
    static void archive(File file, boolean complete, String extra) throws Exception {
        try (ZipOutputStream z = new ZipOutputStream(new FileOutputStream(file))) {
            if(extra!=null) {z.putNextEntry(new ZipEntry(extra));z.write(1);z.closeEntry();}
            z.putNextEntry(new ZipEntry("host-subgroup-size.txt"));z.write("64\n".getBytes("UTF-8"));z.closeEntry();
            z.putNextEntry(new ZipEntry("host-profile.json"));z.write("{}".getBytes("UTF-8"));z.closeEntry();
            for(int i=0;i<(complete?6931:1);i++) for(String suffix:new String[]{"spv","meta"}) {
                z.putNextEntry(new ZipEntry(String.format("%016x.%s",i,suffix)));z.write(i);z.closeEntry();
            }
        }
    }
    public static void main(String[] args) throws Exception {
        File root=Files.createTempDirectory("shader-test").toFile(), zip=new File(root,"patch.zip"), shaders=new File(root,"shaders");shaders.mkdir();
        File original=new File(shaders,"host-subgroup-size.txt");Files.write(original.toPath(),"32\n".getBytes("UTF-8"));
        for(String bad:new String[]{"../escape","subdir/file",null}) {
            archive(zip,false,bad);
            try {ShaderPatch.install(zip,shaders);throw new AssertionError("Invalid patch accepted");} catch(IOException expected) {}
            if(new File(shaders,"subgroup64").exists()||new File(shaders,"subgroup64.pending").exists())throw new AssertionError("Partial publication");
        }
        archive(zip,true,null);ShaderPatch.install(zip,shaders);
        if(new File(shaders,"subgroup64").list().length!=13864)throw new AssertionError("Missing files");
        if(!new String(Files.readAllBytes(original.toPath()),"UTF-8").equals("32\n"))throw new AssertionError("Original changed");
        ShaderPatch.install(zip,shaders);
        System.out.println("Shader patch: traversal, incomplete, atomic publication and original preservation verified");
    }
}
