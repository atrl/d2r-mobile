# Install bundles and GitHub updates

[简体中文](ANDROID_DISTRIBUTION.zh-CN.md)

## GitHub investigation (2026-10-18)

[sydeEvans v0.6.1](https://github.com/sydeEvans/d2r-android/releases/tag/v0.6.1) ships an approximately 19 MB APK and a PC tooling kit, not game data. [jiayx/d2r-mobile-build](https://github.com/jiayx/d2r-mobile-build) documents community prepared inputs, but its [payload format](https://github.com/jiayx/d2r-mobile-build/blob/main/docs/PREPARED_INPUT.md) contains Apple programs and Metal libraries, with resources distributed separately. It cannot be imported as an Android package. Game content from these sources has not been downloaded, validated or republished here.

The GitHub Releases API returned no public releases for wdjwxh/D2R-Mobile-Android, akari-sora/d2r-mobile, MrCKR/d2r-android-adapter, gbcmikeblue/d2r-android or vickwv/d2r-mobile. External distribution channels may differ. No complete Android data package compatible with this fork was found and verified in this investigation.

## Create a local install bundle

Use this fork's signed release APK and your complete prepared Android data package. An existing compatible Android package avoids extracting the original game again. With the project's Android toolchain installed:

```sh
python3 dm/android/tools/make_install_bundle.py \
  --apk /path/D2R-Android-port.apk \
  --package /path/d2r-package.zip \
  --output /path/D2R-install-bundle.zip
```

The tool verifies the APK certificate, required Android package entries, manifest sizes/counts and CRC, then streams a Zip64 bundle containing the APK, data ZIP, installation instructions and SHA256SUMS. It does not execute or validate gameplay. Missing data, Apple packages and wrong APK certificates fail; existing output is not overwritten. Allow space for the additional bundle.

Extract on the phone, install the APK and import the enclosed d2r-package.zip through the launcher. This is a single download archive, not a multi-GB APK. Existing import logic places executable modules and bulk data in their respective storage locations. Game content stays local; public CI/releases continue to distribute only the runtime and tools. This workflow is not a delivered full-game bundle.

## Update on the phone

Choose **Check GitHub updates** in the launcher. A background request compares installed versions with releases carrying complete APK assets from atrl/d2r-mobile. Previews (`vX.Y.Z-preview.N`) are included; a stable release follows previews of the same version. Unknown versions, network errors and GitHub rate limits show an error rather than a false up-to-date result.

Download through the browser and open the APK in Android's installer to update. Android enforces signing compatibility. The app does not silently install, uninstall or reimport data. Only this fork's APK URLs are accepted. If no browser is available, the address is displayed; if GitHub is inaccessible, download on another computer and transfer the APK.

Builds, archive tests and version-order tests do not prove Fold5 browser/install/game behavior. App updates retain compatible imported data and saves; a future incompatible package format or rewrite-rule change may still require rebuilding game data. Read the release notes.
