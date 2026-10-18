// 本 fork 的发布版本排序；预览版低于同版本正式版，不按字符串比较数字。
// Order this fork's release versions; previews precede stable releases and numbers compare numerically.
package org.d2r.android.port;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

final class ReleaseVersion implements Comparable<ReleaseVersion> {
    private static final Pattern FORMAT = Pattern.compile("v?(\\d+)\\.(\\d+)\\.(\\d+)(?:-preview\\.(\\d+))?(?:-android-port)?");
    private final long[] parts;
    private ReleaseVersion(long[] parts) { this.parts = parts; }
    static ReleaseVersion parse(String value) {
        Matcher match = FORMAT.matcher(value == null ? "" : value);
        if (!match.matches()) return null;
        try {
            return new ReleaseVersion(new long[]{Long.parseLong(match.group(1)), Long.parseLong(match.group(2)),
                Long.parseLong(match.group(3)), match.group(4) == null ? Long.MAX_VALUE : Long.parseLong(match.group(4))});
        } catch (NumberFormatException error) { return null; }
    }
    @Override public int compareTo(ReleaseVersion other) {
        for (int i = 0; i < parts.length; i++) {
            int result = Long.compare(parts[i], other.parts[i]);
            if (result != 0) return result;
        }
        return 0;
    }
}
