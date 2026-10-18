#!/usr/bin/env python3
"""Recover the extraction-tool manifest from a matching runtime TVFS and data files.
从匹配的运行时 TVFS 与数据文件重建提取清单；内容哈希通过实际解码计算。
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tools'))
import casc_overlay


def entries(tvfs):
    if len(tvfs) < 46 or tvfs[:12] != bytes.fromhex('54564653012e10100000000a'):
        raise ValueError('unsupported TVFS header')
    po, ps, vo, vs, co, cs = struct.unpack_from('>6I', tvfs, 12)
    eo, es = struct.unpack_from('>II', tvfs, 38)
    if not (46 == po and po + ps == eo and eo + es == co and co + cs == vo and vo + vs == len(tvfs)):
        raise ValueError('invalid TVFS table bounds')
    specs = {}; position = 0
    for spec in tvfs[eo:eo + es].split(b'\0'):
        if spec: specs[position] = spec
        position += len(spec) + 1
    width = casc_overlay.offset_field_size(cs)
    seen = set()
    for _, path, value, folder, _ in casc_overlay.walk_paths(tvfs, po, po + ps):
        if folder is not None: continue
        name = path.decode('utf-8')
        if '|' in name or '\n' in name or name in seen:
            raise ValueError('invalid or duplicate path')
        seen.add(name)
        at = vo + value
        if not vo <= at <= len(tvfs) - 9 - width or tvfs[at] != 1:
            raise ValueError('unsupported file spans')
        offset, size = struct.unpack_from('>II', tvfs, at + 1)
        cft = co + int.from_bytes(tvfs[at + 9:at + 9 + width], 'big')
        if offset != 0 or not co <= cft <= co + cs - 25:
            raise ValueError('invalid container file reference')
        key = tvfs[cft:cft + 16]
        encoded = struct.unpack_from('>I', tvfs, cft + 16)[0]
        spec = tvfs[cft + 20]
        if spec not in specs:
            raise ValueError('invalid encoding or content size')
        # Community overlays update CFT content sizes while retaining original VFS span sizes.
        # 覆盖层更新容器内容长度，可能保留原 VFS 跨度长度；实际解码再核验 CFT 长度。
        yield {'path': name, 'key': key.hex(), 'size': struct.unpack_from('>I', tvfs, cft + 21)[0],
               'span_size': size, 'encoded': encoded,
               'encoding': specs[spec].decode('ascii')}


def decode(root, row):
    key = bytes.fromhex(row['key'])
    file = root / 'data' / f'{key[9]:02d}-{key[10]:08d}.data'
    with file.open('rb') as stream:
        stream.seek(int.from_bytes(key[11:], 'big'))
        raw = stream.read(row['encoded'])
    if len(raw) != row['encoded']:
        raise ValueError('truncated data: ' + row['path'])
    encoding = row['encoding']
    if encoding in ('n', 'z'):
        signed = raw
        content = raw if encoding == 'n' else zlib.decompress(raw)
    elif encoding.startswith('b:'):
        if len(raw) < 12 or raw[:4] != b'BLTE': raise ValueError('invalid BLTE')
        size = struct.unpack_from('>I', raw, 4)[0]
        count = int.from_bytes(raw[9:12], 'big')
        if size != 12 + 24 * count or size > len(raw): raise ValueError('invalid BLTE header')
        signed = raw[:size]; chunks = []; at = size
        for index in range(count):
            encoded, decoded = struct.unpack_from('>II', raw, 12 + index * 24)
            block = raw[at:at + encoded]; at += encoded
            digest = raw[20 + index * 24:36 + index * 24]
            if len(block) != encoded or hashlib.md5(block).digest() != digest:
                raise ValueError('BLTE block checksum mismatch')
            if block[:1] == b'Z': chunk = zlib.decompress(block[1:])
            elif block[:1] == b'N': chunk = block[1:]
            else: raise ValueError('unsupported BLTE mode')
            if len(chunk) != decoded: raise ValueError('BLTE decoded size mismatch')
            chunks.append(chunk)
        if at != len(raw): raise ValueError('BLTE trailing bytes')
        content = b''.join(chunks)
    else:
        raise ValueError('unsupported encoding: ' + encoding)
    if hashlib.md5(signed).digest()[:9] != key[:9] or len(content) != row['size']:
        raise ValueError('resource key/size mismatch: ' + row['path'])
    return content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('romfs', type=Path)
    parser.add_argument('--manifest', type=Path, help='new output file; decodes all files to compute content hashes')
    parser.add_argument('--available-only', action='store_true', help='diagnostic partial manifest; record missing archives/paths instead of claiming completeness')
    args = parser.parse_args()
    tvfs = bytes(casc_overlay.load_vfs1(args.romfs))
    _, config = casc_overlay.config_values(args.romfs / 'data/.build.config')
    if hashlib.md5(tvfs).hexdigest() != config['vfs-1'].split()[0]:
        raise ValueError('TVFS content hash mismatch')
    rows = list(entries(tvfs)); missing = []
    if args.manifest:
        temporary = args.manifest.with_suffix(args.manifest.suffix + '.partial')
        if args.manifest.exists(): raise ValueError('output already exists')
        with temporary.open('x') as stream:
            stream.write('# Recovered from TVFS; content keys computed from verified decoded bytes\n')
            for number, row in enumerate(rows):
                key = bytes.fromhex(row['key'])
                archive = f'{key[9]:02d}-{key[10]:08d}.data'
                if args.available_only and not (args.romfs / 'data' / archive).is_file():
                    missing.append({'path': row['path'], 'archive': archive})
                    continue
                content = decode(args.romfs, row)
                fields = [str(number), '0', str(key[9]), str(key[10]), hashlib.md5(content).hexdigest(),
                          str(row['size']), row['key'], str(row['encoded']), row['encoding'], 'data:' + row['path'], '0']
                stream.write('|'.join(fields) + '\n')
        temporary.rename(args.manifest)
        if args.available_only:
            args.manifest.with_suffix('.missing.json').write_text(json.dumps(missing, indent=2) + '\n')
    shaders = [r for r in rows if r['path'].startswith('data/hd/shaders/') and r['path'].endswith('.bin')]
    print(json.dumps({'files': len(rows), 'shader_packages': len(shaders),
                      'shader_archives': dict(Counter(f"{bytes.fromhex(r['key'])[9]:02d}-{bytes.fromhex(r['key'])[10]:08d}.data" for r in shaders)),
                      'manifest_written': bool(args.manifest), 'missing_files': len(missing), 'complete_manifest': bool(args.manifest) and not missing}, indent=2))


if __name__ == '__main__': main()
