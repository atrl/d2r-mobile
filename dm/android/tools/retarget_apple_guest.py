#!/usr/bin/env python3
"""Retarget recognized Apple guest thread-base sequences without moving existing code.
仅转换符合上游模式的线程访问，保留原代码地址；不代表已通过 Android 游戏验证。
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from inspect_apple_guest import inspect, PAGE
from guest_elf import build


def branch(source, target):
    delta = target - source
    if delta % 4 or not -(1 << 27) <= delta < (1 << 27):
        raise ValueError('branch out of range')
    return 0x14000000 | ((delta >> 2) & 0x3ffffff)


def adrp(register, pc, target):
    delta = ((target & ~4095) - (pc & ~4095)) >> 12
    if not -(1 << 20) <= delta < (1 << 20):
        raise ValueError('ADRP out of range')
    return 0x90000000 | ((delta & 3) << 29) | (((delta >> 2) & 0x7ffff) << 5) | register


def thunk(at, resume, register, key):
    if not 0 <= register <= 30:
        raise ValueError('unsupported destination register')
    # Match patch_nso.thread_base(android). Preserve the existing 128-byte red zone.
    # 与上游 Android 序列一致，保留既有补丁使用的栈下 128 字节。
    words = [0xd10283ff, 0xa9007bf0, adrp(16, at + 8, key),
             0xf9402210, 0xd63f0200, 0xf9000bf0, 0xa9407bf0,
             0xf9400be0 | register, 0x910283ff, branch(at + 36, resume)]
    return struct.pack('<10I', *words)


def convert(image, layout):
    text_end, patch, key = (layout[k] for k in ('TEXT_END', 'PATCH_OFF', 'KEY_PAGE_OFF'))
    if not (0 < text_end <= key and key % PAGE == 0 and key + PAGE <= patch < len(image)):
        raise ValueError('invalid layout')
    for index, name in enumerate(('K18', 'KTLS', 'KTLR', 'KGATE', 'KRES0', 'KRES1', 'KASPECT', 'KASPECTUI')):
        if layout.get('KEY_' + name + '_IDX') != index:
            raise ValueError('unsupported key layout')
    sites = []
    for lo, hi in ((0, text_end), (patch, len(image))):
        for at in range(lo, hi - 3, 4):
            word = struct.unpack_from('<I', image, at)[0]
            if word & 0xffffffe0 != 0xd53bd060:
                continue
            if at < patch or at + 16 > len(image):
                raise ValueError('thread register outside recognized patch region')
            page, load, add = struct.unpack_from('<3I', image, at + 4)
            reg = page & 31
            immediate = ((page >> 29) & 3) | (((page >> 5) & 0x7ffff) << 2)
            if immediate & (1 << 20): immediate -= 1 << 21
            target = ((at + 4) & ~4095) + (immediate << 12)
            dest = word & 31
            if (page & 0x9f000000 != 0x90000000 or target != key or
                load & 0xffc003ff != (0xf9400000 | reg << 5 | reg) or
                (load >> 10) & 0xfff > 7 or
                add != (0x8b000000 | reg << 16 | dest << 5 | dest)):
                raise ValueError(f'unrecognized thread-base sequence at {at:#x}')
            sites.append((at, dest))
    if not sites:
        raise ValueError('no recognized Apple thread-base sequences')
    result = bytearray(image)
    for at, register in sites:
        tail = len(result)
        result.extend(thunk(tail, at + 4, register, key))
        struct.pack_into('<I', result, at, branch(at, tail))
    return bytes(result), len(sites)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('guest', type=Path)
    parser.add_argument('metadata', type=Path)
    parser.add_argument('output', type=Path, help='new local output directory')
    args = parser.parse_args()
    modules = inspect(args.guest.read_bytes())
    outputs = {}; report = {'runtime_verified': False, 'modules': {}}
    for name, module in modules.items():
        fixups = (args.metadata / (name + '.fixups.tsv')).read_text()
        layout = {k: int(v, 16) for k, v in (line[2:].split() for line in fixups.splitlines() if line.startswith('# '))}
        if layout['PATCH_OFF'] != module['patch_offset'] or (layout['TEXT_END'] + PAGE - 1) // PAGE * PAGE != module['regions'][0][1]:
            raise ValueError('metadata does not match Guest layout')
        converted, count = convert(module['image'], layout)
        soname = 'libdmguest_' + name + '.so'
        outputs[soname] = build(converted, layout['TEXT_END'], layout['PATCH_OFF'], soname)
        outputs[name + '.fixups.tsv'] = fixups.encode()
        outputs[name + '.gates.tsv'] = (args.metadata / (name + '.gates.tsv')).read_bytes()
        report['modules'][name] = {'thread_sites': count, 'input_sha256': hashlib.sha256(module['image']).hexdigest(),
                                  'elf_sha256': hashlib.sha256(outputs[soname]).hexdigest(), 'elf_bytes': len(outputs[soname])}
    args.output.mkdir(parents=True, exist_ok=False)
    for name, data in outputs.items(): (args.output / name).write_bytes(data)
    (args.output / 'conversion.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
