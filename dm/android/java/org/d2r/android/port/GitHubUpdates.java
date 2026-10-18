// 用户主动检查本 fork 的 GitHub 发布；浏览器下载，系统验证签名并安装。
// Check this fork's GitHub releases on request; the browser downloads and Android verifies and installs the APK.
package org.d2r.android.port;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import org.json.JSONArray;
import org.json.JSONObject;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

final class GitHubUpdates {
    private static final String REPO = "https://github.com/atrl/d2r-mobile";
    private final Activity activity;
    private boolean checking;
    GitHubUpdates(Activity activity) { this.activity = activity; }
    private String text(String key) {
        return activity.getString(activity.getResources().getIdentifier(key, "string", activity.getPackageName()));
    }
    private void open(String url) {
        try { activity.startActivity(new Intent(Intent.ACTION_VIEW, Uri.parse(url))); }
        catch (RuntimeException error) {
            new AlertDialog.Builder(activity).setMessage(text("dmAndroidUpdateBrowser") + "\n" + url)
                .setPositiveButton(android.R.string.ok, null).show();
        }
    }
    void check() {
        if (checking) return;
        checking = true;
        android.widget.Toast.makeText(activity, text("dmAndroidUpdateChecking"), android.widget.Toast.LENGTH_SHORT).show();
        new Thread(() -> {
            String message;
            String download = null;
            HttpURLConnection connection = null;
            try {
                String installed = activity.getPackageManager().getPackageInfo(activity.getPackageName(), 0).versionName;
                ReleaseVersion current = ReleaseVersion.parse(installed);
                if (current == null) throw new IllegalStateException("unversioned build");
                connection = (HttpURLConnection)new URL("https://api.github.com/repos/atrl/d2r-mobile/releases?per_page=100").openConnection();
                connection.setConnectTimeout(15000);
                connection.setReadTimeout(15000);
                connection.setInstanceFollowRedirects(false);
                connection.setRequestProperty("Accept", "application/vnd.github+json");
                connection.setRequestProperty("User-Agent", "D2R-Android-Updater");
                if (connection.getResponseCode() != 200) throw new IllegalStateException("GitHub HTTP " + connection.getResponseCode());
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                try (InputStream input = connection.getInputStream()) {
                    byte[] buffer = new byte[8192];
                    int count;
                    while ((count = input.read(buffer)) != -1) {
                        if (bytes.size() + count > 4 * 1024 * 1024) throw new IllegalStateException("response too large");
                        bytes.write(buffer, 0, count);
                    }
                }
                JSONArray releases = new JSONArray(new String(bytes.toByteArray(), StandardCharsets.UTF_8));
                ReleaseVersion best = current;
                String bestTag = null;
                for (int i = 0; i < releases.length(); i++) {
                    JSONObject release = releases.getJSONObject(i);
                    String tag = release.optString("tag_name");
                    ReleaseVersion version = ReleaseVersion.parse(tag);
                    if (release.optBoolean("draft") || version == null || version.compareTo(best) <= 0) continue;
                    // 本仓库使用预览发布，所以不能用只返回正式版的 /latest。
                    // This repository ships previews, so /latest (stable only) is unsuitable.
                    JSONArray assets = release.optJSONArray("assets");
                    if (assets == null) continue;
                    for (int j = 0; j < assets.length(); j++) {
                        JSONObject asset = assets.getJSONObject(j);
                        String url = asset.optString("browser_download_url");
                        if ("D2R-Android-port.apk".equals(asset.optString("name"))
                                && "uploaded".equals(asset.optString("state"))
                                && asset.optLong("size") > 0
                                && url.equals(REPO + "/releases/download/" + tag + "/D2R-Android-port.apk")) {
                            best = version; bestTag = tag; download = url;
                        }
                    }
                }
                message = bestTag == null ? String.format(text("dmAndroidUpdateCurrent"), installed)
                    : String.format(text("dmAndroidUpdateFound"), installed, bestTag);
            } catch (Exception error) {
                message = text("dmAndroidUpdateFailed");
            } finally {
                if (connection != null) connection.disconnect();
            }
            final String result = message;
            final String target = download;
            activity.runOnUiThread(() -> {
                checking = false;
                if (activity.isFinishing() || activity.isDestroyed()) return;
                AlertDialog.Builder dialog = new AlertDialog.Builder(activity).setTitle(text("dmAndroidUpdateTitle"))
                    .setMessage(result).setNegativeButton(android.R.string.cancel, null)
                    .setNeutralButton(text("dmAndroidUpdateReleases"), (d, w) -> open(REPO + "/releases"));
                if (target != null) dialog.setPositiveButton(text("dmAndroidUpdateDownload"), (d, w) -> open(target));
                else dialog.setPositiveButton(android.R.string.ok, null);
                dialog.show();
            });
        }, "github-update").start();
    }
}
