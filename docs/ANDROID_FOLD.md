# Android / vivo X Fold5 preview

本仓库直接 fork 自 jhaizhou-ops/d2r-mobile，Android 支持移植自 sydeEvans/d2r-android；来源和基点记录在 `.github/upstreams.json`。保留 MIT 和第三方许可证。

## 下载与安装

从 https://github.com/atrl/d2r-mobile/releases 下载最新预览版的 `D2R-Android-port.apk`，在 Android 中允许浏览器/文件管理器安装该 APK。不要下载 GitHub 自动生成的 Source code 当作安装包。

APK 不含游戏数据。安装后可以打开启动器和“折叠屏与触控自检”；导入自己的完整数据包后才能启动游戏。数据准备见 [数据包说明](ANDROID_PACKAGE.zh-CN.md)，Release 同时提供本地打包套件。密钥、游戏本体和存档不得上传到本仓库或 CI。

本 fork 使用独立且持久的发布证书。同一 fork 的后续发布可以覆盖升级；其他作者相同包名的 APK 使用不同证书，不能直接覆盖。迁移前先在旧应用导出存档，卸载后安装本 fork，再导入数据与存档。不要为安装而直接删除唯一存档。

## 折叠屏行为

目标设备为 vivo X Fold5；系统版本、OriginOS 合盖续用策略和实际驱动仍需真机记录。默认游戏横屏、16:9 等比居中，允许系统调整窗口；不强行铺满内屏或改变游戏内部比例。内外屏切换重建呈现窗口，不主动重启游戏。触控布局根据当前尺寸、密度和安全区域调整；切换时释放旧触点。

启动器提供无需数据的自检页：折叠/展开、旋转、点击四角，查看窗口和 surface 回调计数、绿色等比边框以及黄色触点。此页使用 Android Canvas，只验证窗口与输入，**不能证明 Vulkan 或游戏实玩通过**。

默认沿用上游掌机档分辨率。图形驱动可选择系统或内置 Turnip，兼容性仍需实测；不以其他设备上的 60 FPS 数据作为本设备性能承诺。

## 验收状态

- 已通过：14 项本地自动检查（含存档/数据包格式、触点取消、视口边界、贴图复制布局与签名失败保护）、Android 完整构建；签名 APK 的包名、ABI、版本、证书、对齐和折叠 Activity 声明核验通过。
- GitHub Actions 已完成一次完整构建；每个发布标签还会独立构建并再次校验 APK。
- 待真机：安装/覆盖升级、内外屏/旋转/后台恢复、真实 Vulkan surface 生命周期。
- 待自备游戏数据：连续折叠/展开 20 次不丢进度，存读档、场景切换、30 分钟游玩，记录帧时间和温度。
- 系统杀进程后的恢复依赖已有存档，不承诺未存进度恢复。
- Linux CI 不代表 iOS/macOS 回归通过，也不代表完整游戏兼容性。

## 构建与发布

Linux x86_64 / Python 3.12：运行 `python3 dm/android/tools/bootstrap.py`，安装固定 Python 依赖 `lz4==4.4.4 capstone==5.0.7`，再运行 `python3 dm/android/tools/ci_checks.py` 和 `python3 dm/android/tools/build.py --game-run`。

发布由 `v*` 标签触发，带持久签名、关闭调试、递增 versionCode，生成 APK、数据准备套件、签名摘要与 SHA256SUMS。所有自动发布默认为预览版。CI 调试 APK 与 release 签名不同，不作为日常升级通道。

发布证书保存在 GitHub Secrets `D2R_KEYSTORE_BASE64`、`D2R_STORE_PASSWORD`、`D2R_KEY_PASSWORD`，别名 `d2r-release`。离线备份必须保留，不能每次重新生成。缺失签名配置时发布失败，不回退 debug 签名。

每周一 UTC 02:20 检查原版与 Android 分支。无冲突时生成合并候选 PR；有冲突时生成草稿报告 PR，不覆盖现有改动。Android 参考分支只报告差异，逐项移植；审核后更新 `.github/upstreams.json` 的 `android_reviewed`。自动 PR 显式触发无发布密钥的 CI，不自动合并。

## 上游集成注意事项

原版新版本增加了异步 Metal 翻译队列、贴图副本和图片层间距。Android 保留原版命令录制与贴图副本，但翻译在调用线程同步完成，GPU 仍使用已有 Vulkan 异步提交队列；栅栏使用 Vulkan 的实际提交编号，避免把一条客体命令误认为一条 GPU 提交。新增图片层间距接入原版 `nvn_copy_pitch` 校验。

后台存盘改用当前原版的 `dm_save_wait`，保留暂停状态恢复逻辑。Darwin 指令计数在 Android 上禁用，不报告假性能数据。原版 Mac/iOS 代码保留，但没有在本次 Linux 环境完成这两个平台构建。

其他 ANDROID 文档是移植来源的历史设计与测试记录；其中 OPPO 等设备的数据不代表本 fork 或 X Fold5 已验证。本文件记录当前交付边界。
