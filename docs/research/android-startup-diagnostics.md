# Android startup diagnostics

A user reports that starting the game returns to launcher settings after data download completes. The cause is not yet known; emulator gameplay does not establish vivo compatibility.

The launcher now offers a selectable local diagnostic report and a Storage Access Framework text export. Collection runs off the UI thread. It includes device model/API/ABI, APK version, available RAM, the latest five Android process exit records (API 30+), launch/driver settings, package manifest and the last 64 KiB of game.log. File reads are bounded; missing files and unavailable system records are reported. No saves or game assets are exported, and nothing is automatically uploaded. Logs may contain local paths or character names; users choose whether to share the report.

Export immediately after the failed start, before another attempt overwrites game.log. Android exit records can include older deliberate stops: timestamps and descriptions must be correlated with the failed attempt, not treated as proof by themselves.

Validation: Linux CI checks (20) pass; release APK builds with Android API 35 and Java 8. Android 15 emulator: signed APK cover-install succeeded; report dialog rendered, then the system document picker exported a 67,054-byte UTF-8 file containing device details, process exit history and game.log. Initial pull before the asynchronous write completed found no file; the completed export was pulled and verified. Real vivo failure diagnosis remains pending the report.
