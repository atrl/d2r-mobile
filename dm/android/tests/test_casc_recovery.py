"""Synthetic TVFS and encoded resources; no game data."""
import hashlib
import json
import subprocess
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import zlib
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from recover_casc_manifest import entries, decode
import casc_overlay


def fixture(content, encoding):
    raw = content if encoding == 'n' else zlib.compress(content) if encoding == 'z' else casc_overlay.blte_encode(content)
    key = casc_overlay.ekey_for(raw, 0, 1, 0)
    path = b'\x01a\xff' + bytes(4)
    specs = b'z\0n\0b:64K*=n\0'
    po = 46; eo = po + len(path); co = eo + len(specs); vo = co + 25
    header = bytearray.fromhex('54564653012e10100000000a') + bytearray(34)
    struct.pack_into('>6I', header, 12, po, len(path), vo, 10, co, 25)
    struct.pack_into('>II', header, 38, eo, len(specs))
    cft = key + struct.pack('>I', len(raw)) + bytes([{'z':0, 'n':2, 'b:64K*=n':4}[encoding]]) + struct.pack('>I', len(content))
    # An overlay may retain the original span size while updating CFT decoded size.
    span = b'\x01' + struct.pack('>II', 0, len(content) + 5) + b'\0'
    return bytes(header) + path + specs + cft + span, raw


class RecoveryTest(unittest.TestCase):
    def test_encodings_offsets_and_overlay_sizes(self):
        for encoding in ('z', 'n', 'b:64K*=n'):
            with self.subTest(encoding=encoding), tempfile.TemporaryDirectory() as directory:
                content = b'synthetic resource' * 100
                tvfs, raw = fixture(content, encoding)
                rows = list(entries(tvfs)); self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]['encoding'], encoding)
                self.assertEqual(rows[0]['span_size'], len(content) + 5)
                root = Path(directory); (root / 'data').mkdir()
                (root / 'data/00-00000001.data').write_bytes(raw)
                self.assertEqual(decode(root, rows[0]), content)
                (root / 'data/00-00000001.data').write_bytes(raw[:-1])
                with self.assertRaisesRegex(ValueError, 'truncated'): decode(root, rows[0])

    def test_manifest_reports_missing_and_preserves_namespace(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); (root / 'data').mkdir()
            tvfs, resource = fixture(b'example', 'n')
            encoded = casc_overlay.blte_encode(tvfs)
            key = casc_overlay.ekey_for(encoded, 0, 7, 0)
            (root / 'data/00-00000007.data').write_bytes(encoded)
            (root / 'data/.build.config').write_text(
                f'vfs-1 = {hashlib.md5(tvfs).hexdigest()} {key.hex()}\n'
                f'vfs-1-size = {len(tvfs)} {len(encoded)}\n')
            tool = Path(__file__).resolve().parents[1] / 'tools/recover_casc_manifest.py'
            command = [sys.executable, str(tool), str(root)]
            strict = subprocess.run(command + ['--manifest', str(root / 'strict.psv')], capture_output=True)
            self.assertNotEqual(strict.returncode, 0)
            partial = root / 'partial.psv'
            result = subprocess.run(command + ['--manifest', str(partial), '--available-only'], capture_output=True, text=True, check=True)
            self.assertFalse(json.loads(result.stdout)['complete_manifest'])
            self.assertEqual(len(json.loads(partial.with_suffix('.missing.json').read_text())), 1)
            (root / 'data/00-00000001.data').write_bytes(resource)
            complete = root / 'complete.psv'
            result = subprocess.run(command + ['--manifest', str(complete)], capture_output=True, text=True, check=True)
            self.assertTrue(json.loads(result.stdout)['complete_manifest'])
            self.assertEqual(complete.read_text().splitlines()[1].split('|')[9], 'data:a')

    def test_invalid_header_and_spans(self):
        tvfs, _ = fixture(b'test', 'n')
        with self.assertRaises(ValueError): list(entries(tvfs[:-1]))
        bad = bytearray(tvfs); bad[-10] = 2
        with self.assertRaisesRegex(ValueError, 'spans'): list(entries(bad))


if __name__ == '__main__': unittest.main()
