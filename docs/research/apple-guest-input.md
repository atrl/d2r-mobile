# Apple Guest input experiment / Apple Guest 输入实验

Status: module recovery and thread-base retargeting completed; Android loading and gameplay **not verified**.
状态：已完成模块还原及线程基址转换；**尚未验证 Android 装载和游戏运行**。

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

## Thread-base retargeting result / 线程基址转换结果

`retarget_apple_guest.py` now recognizes the complete MRS + ADRP + LDR + ADD key-slot sequence, verifies its key-page target, rejects unknown patterns, and replaces only the MRS with a branch to an appended Android context thunk. Existing code addresses, jump-table pads and gate return addresses remain unchanged. The thunk follows `patch_nso.py`'s Android context ABI and preserves its 128-byte scratch red zone. It does not reconstruct original NSOs or change resource content.

已转换 main 的 25,127 处、sdk 的 12,085 处线程访问，生成两个 AArch64 ELF 共享库。转换器检查完整键槽寻址模式，而不是全局替换指令编码；保留原跳转表和门返回地址。产物仅保存在本地，`conversion.json` 明确记录 `runtime_verified: false`。

Two additional tests passed using Unicorn 2.1.4: execute the thunk for every destination register x0–x30, asserting all other integer registers, SP, NZCV and the 128-byte red zone remain unchanged; exercise conversion and malformed-sequence rejection with a synthetic module. This verifies the thunk against a synthetic context-entry contract, not the Android dynamic linker, real TLS resolver or full game.

新增两项测试通过：模拟执行全部 31 种目标寄存器，检查其余通用寄存器、栈指针、条件标志和栈下暂存区；检查合成模块转换与非法模式拒绝。模拟上下文入口不等于实际 Android TLS 或游戏验证。

```sh
# Research test dependency; install in your development environment.
python3 -m pip install unicorn==2.1.4
python3 -m unittest discover -s dm/android/tests -p test_apple_retarget.py
python3 dm/android/tools/retarget_apple_guest.py /path/to/Guest /path/to/matching-metadata /tmp/android-modules
```

Full resource download and CASC/shader reconstruction are the next inputs to resolve. The current Android frontend also assumes a third `subsdk0` module; the two-module community input requires a validated loader/package path before use.

## Resource index recovery / 资源索引重建

The IPA's non-ASTC `romfs_overlay` includes a matching `.build.config` and `00-00000007.data`. Its decoded TVFS MD5 matches the config and contains 133,200 single-span file records. `recover_casc_manifest.py` reads encoding-spec **byte offsets**, resolves resource keys, and can rebuild `build_manifest.psv` by decoding each resource and computing its content MD5. Unknown formats fail explicitly. It validates resource EKey prefixes, decoded sizes and BLTE block checksums.

已解析社区覆盖层的完整索引：133,200 个文件，其中 162 个着色器包位于 `00-00000003.data`（85 个）和 `00-00000005.data`（77 个）。覆盖层自身的 825 个文件已实际解码并通过资源键、长度检查。31 个覆盖文件的 CFT 内容长度不同于原 VFS 跨度长度；重建采用实际容器内容长度，再通过解码核验，不把原跨度长度当作新内容长度。

The full archive is still downloading; no full resource manifest has yet been produced. Two synthetic tests cover raw/zlib/BLTE resources, encoding-table byte offsets, changed overlay sizes, truncation and invalid spans. The generated content hashes are computed from decoded resources, not claimed as independently supplied publisher hashes. Recovered numeric file IDs are local enumeration IDs; the manifest serves the existing path-based build tools, not a faithful reconstruction of original extraction metadata.

`build_shaders.py --main-image` accepts the recovered flat main image, checks embedded control hashes against the source shader map, and extracts shader jobs without an NSO container. Nine unique embedded jobs have been extracted locally. This is preparation for translation, not SPIR-V compilation or rendering validation.

```sh
python3 dm/android/tools/recover_casc_manifest.py /path/to/romfs
# Only after all referenced data files are present:
python3 dm/android/tools/recover_casc_manifest.py /path/to/romfs --manifest /path/to/romfs/data/build_manifest.psv
python3 dm/android/tools/build_shaders.py /path/to/romfs /path/to/main.apple-patched.bin /tmp/shaders --main-image --validate
```

## Two-module Android packaging / Android 双模块包

The package builder, Java importer and native launcher now accept main/sdk-only inputs while requiring all three files whenever any subsdk0 file is present. The existing three-module path remains supported. Bundle validation also permits empty gate tables, matching the actual importer contract. Java regression tests exercise complete two-module imports and rejection of partial subsdk0. Six Python bundle tests pass; all 16 existing CI checks pass. The game-host Android APK compiled successfully on Linux. No target Android device gameplay has been verified.

打包、导入、启动三处已支持完整双模块输入；三模块输入继续支持，残缺第三模块仍然拒绝。已编译真实游戏宿主 APK，但没有将此构建发布为可玩版本。完整资源和着色器转换仍在进行。

## Import and embedded shader checks / 导入依赖与内嵌着色器检查

`audit_guest_imports.py` walks actual guest relocation tables and the compiled Android host's `dm_hle` / `dm_force` sections, resolving their ELF relative relocations. For the recovered input it found 656 main imports and 13 sdk imports; no unresolved strong imports and no unreferenced force-table entries. This is static name coverage, not a check of calling conventions, execution paths or Android linker behavior.

静态核对真实重定位和编译后宿主注册表，未发现缺失强符号，也没有未被引用的强制接管条目。检查结果仅证明符号名称覆盖，不证明 ABI 或运行行为。

The nine recovered embedded shader jobs were translated with the repository's Android Ryujinx translator using .NET SDK 10.0.402. All 9/9 SPIR-V modules passed the NDK `spirv-val --target-env vulkan1.1` check and all 9 reflection pairs were produced. This covers only embedded jobs; the 162 resource shader packages still await archive download and extraction. GPU rendering has not been tested.

内嵌着色器已实际完成转换：9/9 SPIR-V 通过 Vulkan 1.1 校验，9/9 反射文件齐全。其余 162 个资源着色器包尚待完整资源下载和提取；未验证 GPU 画面。

```sh
python3 dm/android/tools/audit_guest_imports.py /path/to/apple-images dm/android/build/game-host/libdmandroid.so
```

The three synthetic conversion suites are included in Android CI. CI installs Unicorn 2.1.4 and never downloads community game inputs; those remain local conversion inputs.
转换的三组合成测试已接入 Android CI，固定使用 Unicorn 2.1.4；CI 不下载游戏输入。

## Touch overlay packaging / 触控覆盖层打包

The community runtime overlay includes root-level `ctrl_touch` and `touch_strings.tsv`. Previously the Android packer only collected `data/` and flattened resource paths, while the launcher did not set `DM_ROMFS_OVERLAY`; that would omit the sidecars and leave host touch-layout switching disabled. The packer now preserves relative resource paths and includes a complete marker/wording pair (plus the optional textbox table). The imported-package launcher enables the merged overlay when the marker exists and requires its wording table. Synthetic packaging regression, all 19 local CI checks, APK compilation and static import coverage pass. Actual on-device touch behavior remains unverified.

已补齐覆盖层根目录的触控标记及文字表，保留打包相对路径，并在导入包启动时启用该覆盖层。触控标记存在但文字表缺失时明确报错。真机触控交互尚未验证。

## Complete shader-set translation / 完整着色器集合转换

All 162 resource shader packages have now been extracted from the downloaded ZIP entry prefixes and checked against their TVFS EKey prefixes and decoded sizes. The combined packages plus recovered embedded shaders produce 6,931 unique jobs. Both subgroup-32 and subgroup-64 variants completed: 6,931/6,931 SPIR-V modules passed Vulkan 1.1 validation and 6,931/6,931 reflection pairs were generated for each variant. The existing capability-repair pass amended storage-image declarations in 15 modules per variant.

已提取全部 162 个资源着色器包，与内嵌着色器合并后得到 6,931 个独立任务。32/64 两种分组配置均完整转换并通过 Vulkan 1.1 校验，反射文件全部齐全。该结果仍不等于 GPU 画面或游戏运行验证；提取时完整 ZIP 尚未下载完毕，全包 SHA-256 校验和完整资源清单重建仍待后续流水线完成。
