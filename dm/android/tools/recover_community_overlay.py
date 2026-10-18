#!/usr/bin/env python3
"""Restore the two shared Cain6 configs omitted by the community language-filtered pack.
恢复社区语言裁剪包遗漏的两个 Cain6 共用配置；必须匹配原 TVFS 资源键及长度。
"""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import zlib
from recover_casc_manifest import entries, decode, casc_overlay


def verify_content(content, target):
    encoded = zlib.compress(content, 9)
    if (len(content) != target['size'] or len(encoded) != target['encoded'] or
            hashlib.md5(encoded).digest()[:9] != bytes.fromhex(target['key'])[:9]):
        raise ValueError('recovered content does not match TVFS EKey prefix and lengths')
    return encoded


def recover(source, output):
    if output.exists(): raise ValueError('output must be a new directory')
    rows = list(entries(bytes(casc_overlay.load_vfs1(source))))
    byname = {row['path']: row for row in rows}
    manifest = (source / 'data/build_manifest.psv').read_text()
    proofs = []
    with tempfile.TemporaryDirectory(prefix='d2r-recovery-') as temporary:
        work = Path(temporary); staged = work / 'source'
        casc_overlay.link_tree(source, staged, {'data'})
        (staged / 'data').mkdir()
        for file in (source / 'data').iterdir():
            if file.name not in ('build_manifest.psv', 'build_manifest.missing.json'):
                (staged / 'data' / file.name).symlink_to(file.resolve())
        replacements = {}
        for name in ('cain6_variant.json', 'cain6_state_machine.json'):
            path = 'data/hd/character/npc/cain6/' + name
            target = byname[path]
            if name.endswith('state_machine.json'):
                prior = byname['data/hd/character/npc/cain3/cain3_state_machine.json']
                content = decode(source, prior).replace(b'cain3', b'cain6')
            else:
                candidates = []
                for row in rows:
                    key = bytes.fromhex(row['key'])
                    if (row['key'][:18] == target['key'][:18] and
                            (source / 'data' / f'{key[9]:02d}-{key[10]:08d}.data').is_file()):
                        candidates.append(row)
                if not candidates: raise ValueError('no available identical Cain6 variant')
                prior = candidates[0]; content = decode(source, prior)
            encoded = verify_content(content, target)
            destination = work / name; destination.write_bytes(content)
            replacements[path] = destination
            key = bytes.fromhex(target['key'])
            fields = ['recovered', '0', str(key[9]), str(key[10]), hashlib.md5(content).hexdigest(),
                      str(len(content)), target['key'], str(len(encoded)), 'z', 'data:' + path, '0']
            manifest += '|'.join(fields) + '\n'
            proofs.append({'path': path, 'source_path': prior['path'], 'encoded_key_prefix': target['key'][:18],
                           'encoded_bytes': len(encoded), 'decoded_bytes': len(content),
                           'decoded_sha256': hashlib.sha256(content).hexdigest()})
        (staged / 'data/build_manifest.psv').write_text(manifest)
        casc_overlay.make_overlay(staged, output, replacements)
        # The temporary lookup manifest has old locations. Regenerate against the new TVFS.
        # 临时定位清单仍引用旧位置，必须根据新 TVFS 重新生成。
        (output / 'data/build_manifest.psv').unlink()
    (output / 'recovery-proof.json').write_text(json.dumps(proofs, indent=2) + '\n')
    return proofs


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    print(json.dumps(recover(args.source.resolve(), args.output.resolve()), indent=2))
