package org.d2r.android.port;

import android.app.ActivityManager;
import android.app.ApplicationExitInfo;
import android.content.Context;
import android.os.Build;
import java.io.File;
import java.io.RandomAccessFile;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

/** Local, bounded diagnostics. No saves, account identifiers or automatic upload. */
final class StartupDiagnostics {
    static String collect(Context context) {
        StringBuilder report = new StringBuilder("D2R startup diagnostics\n");
        report.append("Device: ").append(Build.MANUFACTURER).append(' ').append(Build.MODEL)
            .append("\nAndroid: ").append(Build.VERSION.RELEASE).append(" API ").append(Build.VERSION.SDK_INT)
            .append("\nABIs: ").append(Arrays.toString(Build.SUPPORTED_ABIS)).append('\n');
        android.util.DisplayMetrics display=context.getResources().getDisplayMetrics();
        report.append("Resource display: ").append(display.widthPixels).append('x').append(display.heightPixels).append(" density=").append(display.densityDpi).append('\n');
        try {
            report.append("APK: ").append(context.getPackageManager()
                .getPackageInfo(context.getPackageName(), 0).versionName).append('\n');
            ActivityManager manager = (ActivityManager) context.getSystemService(Context.ACTIVITY_SERVICE);
            ActivityManager.MemoryInfo memory = new ActivityManager.MemoryInfo();
            manager.getMemoryInfo(memory);
            report.append("RAM total/available: ").append(memory.totalMem).append('/').append(memory.availMem).append('\n');
            if (Build.VERSION.SDK_INT >= 30) {
                for (ApplicationExitInfo exit : manager.getHistoricalProcessExitReasons(context.getPackageName(), 0, 5)) {
                    report.append("Exit time=").append(exit.getTimestamp()).append(" reason=").append(exit.getReason())
                        .append(" status=").append(exit.getStatus()).append(" process=").append(exit.getProcessName())
                        .append(" description=").append(exit.getDescription()).append('\n');
                }
            }
        } catch (Exception error) { report.append("System diagnostics unavailable: ").append(error).append('\n'); }
        append(report, new File(context.getFilesDir(), "temp/launch-settings.conf"), 8192);
        append(report, new File(context.getFilesDir(), "temp/gpu-driver.conf"), 4096);
        File external = context.getExternalFilesDir(null);
        if (external != null) {
            append(report, new File(external, "d2r-package/manifest.json"), 8192);
            report.append("\nBase shader profile:");
            append(report, new File(external, "d2r-package/shaders/host-subgroup-size.txt"), 32);
            report.append("\nSystem GPU compatibility profile:");
            append(report, new File(external, "d2r-package/shaders/subgroup64/host-subgroup-size.txt"), 32);
        }
        append(report, new File(context.getFilesDir(), "game.log"), 65536);
        append(report, new File(context.getFilesDir(), "game.previous.log"), 65536);
        append(report, new File(context.getFilesDir(), "game.older.log"), 65536);
        return report.toString();
    }

    private static void append(StringBuilder report, File file, int limit) {
        report.append("\n--- ").append(file.getName()).append(" ---\n");
        if (!file.isFile()) { report.append("Not present\n"); return; }
        try (RandomAccessFile in = new RandomAccessFile(file, "r")) {
            long size = in.length();
            report.append("Bytes: ").append(size).append(" modified: ").append(file.lastModified()).append('\n');
            if (size > limit) report.append("[last ").append(limit).append(" bytes]\n");
            in.seek(Math.max(0, size - limit));
            byte[] bytes = new byte[(int)Math.min(size, limit)];
            in.readFully(bytes);
            report.append(new String(bytes, StandardCharsets.UTF_8)).append('\n');
        } catch (Exception error) { report.append(error).append('\n'); }
    }
}
