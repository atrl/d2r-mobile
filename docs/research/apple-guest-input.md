# Apple Guest input experiment / Apple Guest 输入实验

Status: module recovery verified; Android conversion and gameplay **not verified**.
状态：已验证模块还原；**尚未完成 Android 转换，也未验证游戏运行**。

The community's 5,424,765,988-byte split resource ZIP contains 18 `.data` files, a README and checksums. Its ZIP directory was inspected using HTTP ranges; the complete resource bodies were not downloaded or decoded. This is substantial game resource data, but the directory does not contain the Android guest libraries or a ready-to-import Android package.

社区的 5.42 GB 分卷包确实包含游戏资源。已远程检查 ZIP 目录，其中有 18 个 `.data` 文件及说明、校验文件；没有下载并解码全部资源内容。资源包并不等于包含 Android 游戏代码和着色器的完整安装包。

The separate [community IPA release](https://github.com/jiayx/d2r-mobile-build/releases/tag/v1.0.18-build.10.1) contains `Guest.framework`. Its 69,753,472-byte Guest binary was extracted locally with ZIP CRC verification. That checks archive integrity, not publisher authenticity. REA 6.5.0 `inspect-artifact` independently recognized Mach-O and recorded the same SHA-256. Its artifact provider did not run function-level analysis; no decompilation success is claimed.

另一个社区 IPA 中包含游戏程序 `Guest.framework`。已实际提取并通过 ZIP CRC 检查。REA 的文件检查确认了 Mach-O 格式和哈希；没有把文件识别当作反编译成功。

`dm/tools/guest_dylib.py` packs each module into x0, writable image, and x1 regions. `dm/android/tools/inspect_apple_guest.py` reverses this layout with bounds checks, reconstructing **Apple-patched** images. This is not recovery of the original NSOs. Two synthetic tests exercise the actual upstream packer, truncated/invalid input and unsafe module names. No game binaries are included in this branch.

按上游实际封装规则，已还原 main（54,378,496 字节）和 sdk（15,204,352 字节）。它们仍然带有 Apple 平台改写，不能直接作为 Android 模块导入。合成数据测试使用真实上游封装器进行往返检查；本分支不包含游戏二进制。

See [measured metadata](apple-guest-observation.json): six embedded shader control hashes match `dm/gfx/nvn/shader_map.tsv`, and all four counter shader control magics exist. This establishes that those inputs survived Apple packaging; it does not establish complete shader extraction, successful SPIR-V translation, or rendering correctness.

实测 6 处内嵌着色器控制数据哈希匹配项目记录，4 处计算着色器标识存在。因此可继续研究利用这些输入生成 Vulkan 着色器，不能直接断言必须重新获取原始 NSO；目前也不能宣称完整转换成功。

## Remaining conversion work / 剩余转换工作

- `patch_nso.py:thread_base` emits one Apple thread-register instruction but a longer Android context sequence. Candidate encodings occur 25,127 times in main and 12,085 times in sdk; these counts can include non-instruction bytes. Validated patch-site metadata and control-flow analysis are required before rewriting. Blind global replacement is unsuitable.
- Recover and validate fixups, gate tables, key offsets, movie/subsdk0 dependencies, and loader expectations. Do not forge `android-context-v1` markers to bypass `guest_elf.py` checks.
- Match CASC metadata to the resource archive and extract shader packages; validate translation with the existing Android capability profile. Metal libraries are not directly usable as Vulkan shaders.
- Validate the resulting package on Android, then check launch, saves, sustained frame timing and vivo fold/unfold behavior. No such runtime result exists for this input yet.

仍需确认线程补丁位置及分支语义、重定位与门表、电影模块依赖、CASC 索引配套关系，生成并验证完整 Vulkan 着色器，最后进行 Android 真机启动与折叠屏测试。REA 能协助分析，不能替代这些平台适配与运行验证。

## Reproduce / 复现

```sh
python3 -m unittest discover -s dm/android/tests -p test_apple_guest.py
python3 dm/android/tools/inspect_apple_guest.py /path/to/Guest
# Optional local extraction; output directory must not already exist.
python3 dm/android/tools/inspect_apple_guest.py /path/to/Guest --extract /tmp/apple-images
npx -y rea-agents@6.5.0 inspect-artifact /path/to/Guest --json
```

Sources: [community releases](https://github.com/jiayx/d2r-mobile-build/releases), [upstream packer](https://github.com/jhaizhou-ops/d2r-mobile/blob/9393b00ea9aca52d9254214da93738f26582562f/dm/tools/guest_dylib.py), [REA](https://github.com/morluto/rea).
