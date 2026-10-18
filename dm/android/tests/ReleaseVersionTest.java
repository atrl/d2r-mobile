// 发布排序回归：预览版、正式版、未知版本及数字溢出。
// Release-order regressions: previews, stable releases, unknown versions and numeric overflow.
package org.d2r.android.port;
public final class ReleaseVersionTest {
    private static void ordered(String older, String newer) {
        if (ReleaseVersion.parse(older).compareTo(ReleaseVersion.parse(newer)) >= 0) throw new AssertionError(older);
    }
    public static void main(String[] args) {
        ordered("v0.1.0-preview.2", "v0.1.0-preview.10");
        ordered("v0.1.0-preview.10", "v0.1.0");
        ordered("v0.1.0", "v0.1.1-preview.1");
        ordered("v0.9.0", "v0.10.0");
        if (ReleaseVersion.parse("0.1.0-preview.3-android-port").compareTo(ReleaseVersion.parse("v0.1.0-preview.3")) != 0)
            throw new AssertionError("installed suffix");
        for (String bad : new String[]{null, "ci-abcd", "v0.1.0/evil", "v999999999999999999999.1.0", "v1.0.0-unknown"})
            if (ReleaseVersion.parse(bad) != null) throw new AssertionError(bad);
        System.out.println("Release version ordering OK");
    }
}
