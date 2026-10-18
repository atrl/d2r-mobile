# Android distribution

Install `D2R-Android-port.apk` from the newest preview and select **Download game data**. The app downloads 6.15 GB from the pinned preview.5 data release, verifies every part with SHA-256, and imports automatically without manual merging. Allow 13 GB free space, use Wi-Fi, and keep the app in the foreground. Tap Download again to cancel; retry resumes partial downloads. Cached parts are deleted after successful import.

APK updates preserve imported data and saves. Use **Check GitHub updates** for newer APKs. Data and APK releases are independent; preview.5 must remain available because the downloader references its assets. A future incompatible data update requires an app update; existing data is not silently replaced.

This remains a compatibility preview. ARM64 installation and complete import have been tested in an Android 15 emulator, but combat, long-session stability and vivo fold hardware validation remain incomplete. See [research evidence](research/apple-guest-input.md) and [Chinese distribution details](ANDROID_DISTRIBUTION.zh-CN.md).
