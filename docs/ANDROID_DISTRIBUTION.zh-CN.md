# 整合安装与 GitHub 更新

[English](ANDROID_DISTRIBUTION.md)

## GitHub 调查（2026-10-18）

- [sydeEvans/d2r-android](https://github.com/sydeEvans/d2r-android/releases/tag/v0.6.1)：公开 APK 约 19 MB，配套 ZIP 是电脑打包工具，不是游戏数据。
- [jiayx/d2r-mobile-build](https://github.com/jiayx/d2r-mobile-build)：有社区预处理输入方案。[格式说明](https://github.com/jiayx/d2r-mobile-build/blob/main/docs/PREPARED_INPUT.md)里的 source-payload.zip 包含 Apple 程序及 Metal 库，不能直接导入 Android；资源另外分发。没有下载或验证其中游戏内容，也没有将其重新发布到本 fork。
- wdjwxh/D2R-Mobile-Android、akari-sora/d2r-mobile、MrCKR/d2r-android-adapter、gbcmikeblue/d2r-android、vickwv/d2r-mobile：本轮 GitHub Releases API 没有返回公开发布包。这不等于其外部渠道也没有包。

本轮没有找到并验证能直接用于本 fork 的完整 Android 数据包。社区已经打包，不代表其 iOS 程序和着色器可以在 Android 使用。这里提供整合流程，不宣称已经交付包含游戏的完整安装包。

## 本地生成一份安装整合包

准备本 fork 的签名 Release APK，以及自己的完整 `d2r-package.zip`（已有兼容 Android 包可以复用，无需重新解密本体）。使用项目 Android 工具链：

```sh
python3 dm/android/tools/make_install_bundle.py \
  --apk /path/D2R-Android-port.apk \
  --package /path/d2r-package.zip \
  --output /path/D2R-install-bundle.zip
```

工具验证 APK 的发布签名、Android 数据包结构、必需文件、清单计数/大小和 CRC，再流式生成支持大文件的 Zip64 安装套件：APK、数据 ZIP、安装说明、SHA256SUMS。不会执行游戏或验证其场景兼容性。缺少数据、iOS 包、错误签名会失败；不会用空占位数据伪装完整包。需要额外空间保存整合包；不覆盖已有输出。

手机先解压整合包、安装 APK，再用启动器导入其中的 `d2r-package.zip`。这是单个下载归档，不是把数 GB 游戏资源塞进 APK；Android 的可执行模块和大容量数据仍按现有导入流程分开放置。游戏内容留在本机；公开 CI/Release 继续只发布程序和工具。

## 手机检查更新

启动器 → **检查 GitHub 更新**，后台访问 `atrl/d2r-mobile` Releases，比较已安装版本与带完整 APK 附件的发布。包含 `vX.Y.Z-preview.N` 预览版；同版本正式版排在预览版之后。未知版本、网络失败和 GitHub 限流会显示提示，不伪称已经最新。

发现新版后点击下载，在浏览器下载 APK，再交给 Android 安装器覆盖安装。系统执行签名校验；此功能不静默安装、不卸载应用，也不重导入游戏数据。只从固定 fork 选择 APK，保留原有数据和存档。没有浏览器时显示地址；无法访问 GitHub 时可在能访问的电脑上下载后传到手机。

构建、格式测试和版本排序测试不等同于 Fold5 上的浏览器下载、安装及游戏实测。版本更新功能只更新程序；数据格式或改写规则发生不兼容变化时，仍可能需要重新准备数据包，须查看发布说明。
