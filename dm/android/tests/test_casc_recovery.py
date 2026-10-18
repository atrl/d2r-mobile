"""Synthetic TVFS and encoded resources; no game data."""
import hashlib
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

    def test_invalid_header_and_spans(self):
        tvfs, _ = fixture(b'test', 'n')
        with self.assertRaises(ValueError): list(entries(tvfs[:-1]))
        bad = bytearray(tvfs); bad[-10] = 2
        with self.assertRaisesRegex(ValueError, 'spans'): list(entries(bad))


if __name__ == '__main__': unittest.main()
