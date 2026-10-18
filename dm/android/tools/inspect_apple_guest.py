#!/usr/bin/env python3
"""检查上游 Guest.framework 的模块布局；可还原 Apple 已改写映像，不能直接运行于 Android。
Inspect upstream Guest.framework layout; optionally recover Apple-patched images, not Android executables.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import struct

PAGE = 0x4000


def inspect(data):
    """按 guest_dylib.py 的三个分区重组，拒绝越界、重复和缺失的分区。
    Reassemble the three regions from guest_dylib.py; reject out-of-bounds, duplicate or missing regions.
    """
    if len(data) < 32:
        raise ValueError('truncated Mach-O header')
    magic, cpu, subtype, kind, count, size, flags, reserved = struct.unpack_from('<8I', data)
    if magic != 0xfeedfacf or cpu != 0x100000c or kind != 6:
        raise ValueError('expected a thin ARM64 Mach-O dylib')
    end = 32 + size
    if end > len(data) or count > size // 8:
        raise ValueError('invalid load command range')
    sections = {}
    pos = 32
    for _ in range(count):
        if pos + 8 > end:
            raise ValueError('truncated load command')
        command, length = struct.unpack_from('<II', data, pos)
        if length < 8 or pos + length > end:
            raise ValueError('invalid load command size')
        if command == 0x19:
            if length < 72:
                raise ValueError('truncated segment')
            fields = struct.unpack_from('<II16s4Q4I', data, pos)
            segment = fields[2].rstrip(b'\0').decode('ascii')
            fileoff, filesize, nsections = fields[5], fields[6], fields[9]
            if fileoff + filesize > len(data) or 72 + 80 * nsections > length:
                raise ValueError('invalid segment range')
            for i in range(nsections):
                section, owner, address, size, offset = struct.unpack_from('<16s16sQQI', data, pos + 72 + 80 * i)
                key = (segment, section.rstrip(b'\0').decode('ascii'))
                if owner.rstrip(b'\0').decode('ascii') != segment or key in sections:
                    raise ValueError('invalid or duplicate section')
                if offset < fileoff or offset + size > fileoff + filesize:
                    raise ValueError('section outside file-backed segment')
                sections[key] = (offset, size)
        pos += length
    if pos != end:
        raise ValueError('load command size mismatch')
    names = sorted(segment[4:-1] for segment, section in sections if segment.startswith('__DM') and segment.endswith('W') and section == '__img')
    if not names:
        raise ValueError('no upstream guest modules')
    result = {}
    for name in names:
        if not re.fullmatch(r"[A-Za-z0-9_]+", name):
            raise ValueError("invalid module name")
        keys = [('__TEXT', '__dm' + name + 'x0'), ('__DM' + name + 'W', '__img'), ('__TEXT', '__dm' + name + 'x1')]
        if not all(key in sections for key in keys):
            raise ValueError('incomplete module: ' + name)
        regions = [sections[key] for key in keys]
        if any(size % PAGE for offset, size in regions):
            raise ValueError('unexpected module alignment')
        image = b''.join(data[offset:offset + size] for offset, size in regions)
        patch_offset = regions[0][1] + regions[1][1]
        # 此计数只定位指令编码候选，不把数据字节或静态读数当作运行证据。
        # Count instruction-encoding candidates only; data bytes and static counts are not execution evidence.
        candidates = []
        for begin, finish in ((0, regions[0][1]), (patch_offset, len(image))):
            candidates.extend(i for i in range(begin, finish, 4)
                              if struct.unpack_from('<I', image, i)[0] & 0xffffffe0 == 0xd53bd060)
        result[name] = {'image': image, 'patch_offset': patch_offset, 'regions': regions,
                        'apple_thread_register_candidates': len(candidates)}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('guest', type=Path)
    parser.add_argument('--extract', type=Path, help='new directory for Apple-patched images; not an Android package')
    args = parser.parse_args()
    data = args.guest.read_bytes()
    modules = inspect(data)
    if args.extract:
        args.extract.mkdir(parents=True, exist_ok=False)
        for name, module in modules.items():
            (args.extract / (name + '.apple-patched.bin')).write_bytes(module['image'])
    report = {'source_sha256': hashlib.sha256(data).hexdigest(), 'source_bytes': len(data),
              'android_ready': False, 'original_nso_recovered': False, 'modules': {}}
    for name, module in modules.items():
        image = module.pop('image')
        report['modules'][name] = dict(module, bytes=len(image), sha256=hashlib.sha256(image).hexdigest())
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
