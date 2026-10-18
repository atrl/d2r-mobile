#!/usr/bin/env python3
"""本地安装整合包：已签名 APK + 已准备好的 Android 数据包，不上传游戏内容。
Local install bundle: signed APK + prepared Android package; never uploads game content.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile
import zipfile

from build_package import required_game_files
from verify_apk import verify


def validate_package(path):
    """校验结构、数量及 CRC；这不是游戏兼容性或运行验证。
    Validate structure, counts and CRC; this is not game compatibility or runtime validation.
    """
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if len(names) > 100000 or len(names) != len(set(names)):
            raise ValueError('duplicate entries or too many entries')
        for name in names:
            if '\\' in name or name.startswith('/') or '..' in PurePosixPath(name).parts or ':' in name:
                raise ValueError('unsafe package path')
        if 'manifest.json' not in names or archive.getinfo('manifest.json').file_size > 1024 * 1024:
            raise ValueError('missing or oversized Android manifest; iOS prepared packages are not compatible')
        manifest = json.loads(archive.read('manifest.json'))
        if manifest.get('format') != 1:
            raise ValueError('unsupported Android package format')
        required = {'game/' + name for name in required_game_files({n[5:] for n in names if n.startswith('game/')})}
        required.update({'shaders/host-subgroup-size.txt', 'derived.tsv'})
        if not required.issubset(names):
            raise ValueError('missing required Android modules, layouts, shader profile or derived.tsv')
        if any(archive.getinfo(name).file_size == 0 for name in required if not name.endswith('.gates.tsv')):
            raise ValueError('empty required entry')
        if not any(name.startswith('shaders/') and name.endswith('.spv') for name in names):
            raise ValueError('missing Vulkan SPIR-V shaders')
        if not any(name.startswith('romfs/data/') and name.endswith('.data') for name in names):
            raise ValueError('missing game resource archives')
        for group in ('game', 'romfs', 'shaders'):
            files = [entry for entry in entries if not entry.is_dir() and entry.filename.startswith(group + '/')]
            if len(files) != manifest.get('counts', {}).get(group) or sum(e.file_size for e in files) != manifest.get('bytes', {}).get(group):
                raise ValueError('manifest count/size mismatch: ' + group)
        profile = archive.getinfo('shaders/host-subgroup-size.txt')
        if profile.file_size > 32 or int(archive.read(profile)) != manifest.get('subgroup_size'):
            raise ValueError('shader subgroup mismatch')
        bad = archive.testzip()
        if bad:
            raise ValueError('CRC failure: ' + bad)
    return manifest


def bundle(apk, package, output):
    """流式写 Zip64 并原子完成；失败时不留下看似完整的安装包。
    Stream Zip64 and finish atomically; failures never leave an apparently complete bundle.
    """
    if output.exists() or output.resolve() in (apk.resolve(), package.resolve()):
        raise ValueError('output already exists or aliases an input')
    output.parent.mkdir(parents=True, exist_ok=True)
    instructions = (
        '安装：先解压本 ZIP，安装 D2R-Android-port.apk，再在启动器选择“导入数据包”，选择 d2r-package.zip。\n'
        '更新：启动器 → 检查 GitHub 更新 → 下载 APK → 覆盖安装；不必重新导入兼容数据包。请保留存档备份。\n'
        '这不是单 APK 安装：大容量游戏数据单独导入。格式校验不代表真机实玩通过。仅在本机保管自己的游戏数据。\n\n'
        'Extract this ZIP, install D2R-Android-port.apk, then use Import package to select d2r-package.zip.\n'
        'Update via Check GitHub updates; install over the existing app to retain compatible data and saves. Keep save backups.\n'
        'Large game data is imported separately. Format validation does not prove gameplay. Keep your game data locally.\n')
    with tempfile.TemporaryDirectory(dir=output.parent, prefix='.d2r-bundle-') as temporary:
        staged = Path(temporary) / 'bundle.zip'
        sums = []
        with zipfile.ZipFile(staged, 'w', zipfile.ZIP_STORED, allowZip64=True) as archive:
            for source, name in ((apk, 'D2R-Android-port.apk'), (package, 'd2r-package.zip')):
                digest = hashlib.sha256()
                with source.open('rb') as reader, archive.open(name, 'w', force_zip64=True) as writer:
                    while chunk := reader.read(1024 * 1024):
                        writer.write(chunk)
                        digest.update(chunk)
                sums.append(digest.hexdigest() + '  ' + name)
            archive.writestr('SHA256SUMS', '\n'.join(sums) + '\n')
            archive.writestr('INSTALL.txt', instructions)
        staged.replace(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    verify(args.apk, release=True)
    validate_package(args.package)
    bundle(args.apk, args.package, args.output)
    print('Local install bundle:', args.output)


if __name__ == '__main__':
    main()
