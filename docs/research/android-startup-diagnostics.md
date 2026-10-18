# Android startup diagnostics

A user reports that starting the game returns to launcher settings after data download completes. The cause is not yet known; emulator gameplay does not establish vivo compatibility.

The launcher now offers a selectable local diagnostic report and a Storage Access Framework text export. Collection runs off the UI thread. It includes device model/API/ABI, APK version, available RAM, the latest five Android process exit records (API 30+), launch/driver settings, package manifest and the last 64 KiB of game.log. File reads are bounded; missing files and unavailable system records are reported. No saves or game assets are exported, and nothing is automatically uploaded. Logs may contain local paths or character names; users choose whether to share the report.

Export immediately after the failed start, before another attempt overwrites game.log. Android exit records can include older deliberate stops: timestamps and descriptions must be correlated with the failed attempt, not treated as proof by themselves.

Validation: Linux CI checks (20) pass; release APK builds with Android API 35 and Java 8. Android 15 emulator: signed APK cover-install succeeded; report dialog rendered, then the system document picker exported a 67,054-byte UTF-8 file containing device details, process exit history and game.log. Initial pull before the asynchronous write completed found no file; the completed export was pulled and verified. Real vivo failure diagnosis remains pending the report.

## Published preview.10 follow-up (2026-10-18)

Downloaded the public release APK (20,027,855 bytes), checked SHA256SUMS and apksigner verification. SHA-256: `2f9334f76ce17bea083af775113aea244e06d76d7db730386100a4278992027c`.

On the persistent Android 15 x86_64 emulator with ARM64 translation, a cold emulator restart followed by `adb install --no-incremental -r` succeeded. Package manager reports versionCode 10037 and versionName 0.1.0-preview.10-android-port. Launch reached the existing TestHero character selection; a short tap on Enter Game reached camp. The nearly empty health globe and depleted potion slots from the prior combat session were visible after load. This establishes that this published APK loads the existing save and enters gameplay in this emulator; it is not vivo compatibility evidence.

Evidence on the test host: `/tmp/d2r-preview10-start.png`, `/tmp/d2r-preview10-camp.png`, `/tmp/d2r-preview10-game.log`. The inventory control subsequently produced `PlayerInventoryExpansionLayout` in the native log. Backgrounding suspended graphics and audio. That background save request reported commits=0, so this follow-up does not establish a new save commit.

An earlier cover-install attempt lost the whole emulator process, with gfxstream null-context errors in its host log. The subsequent cold-restart installation succeeded. This host failure is separate from the user's vivo symptom and does not identify its cause. The user's startup report remains required. No claim of complete game, foldable hardware, sustained performance or multiplayer acceptance is made.
