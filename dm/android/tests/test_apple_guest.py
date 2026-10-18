#!/usr/bin/env python3
"""用上游真实封装器与合成模块做往返测试，无游戏内容。
Round-trip the actual upstream packer using synthetic modules, with no game content.
"""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'dm/android/tools'))
from inspect_apple_guest import inspect, PAGE
spec = importlib.util.spec_from_file_location('guest_dylib', ROOT / 'dm/tools/guest_dylib.py')
packer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packer)


class AppleGuestTest(unittest.TestCase):
    def test_round_trip_source_packer(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = {}
            for index, name in enumerate(('main', 'sdk')):
                image = bytes([index + 1]) * (3 * PAGE + 123)
                images[name] = image
                (root / (name + '.patched.bin')).write_bytes(image)
                (root / (name + '.fixups.tsv')).write_text(f'# TEXT_END\t{PAGE - 4:#x}\n# PATCH_OFF\t{3 * PAGE:#x}\n')
            data = packer.build(str(root), ['main', 'sdk'])
            result = inspect(data)
            self.assertEqual(set(result), set(images))
            for name, image in images.items():
                self.assertEqual(result[name]['image'], image.ljust(4 * PAGE, b'\0'))
                self.assertEqual(result[name]['patch_offset'], 3 * PAGE)
            with self.assertRaises(ValueError):
                inspect(data[:PAGE])
            with self.assertRaisesRegex(ValueError, 'invalid module name'):
                inspect(data.replace(b'__DMmainW', b'__DM../xW'))

    def test_wrong_input_rejected(self):
        for data in (b'', b'PK\x03\x04' + bytes(128), bytes(64)):
            with self.assertRaises(ValueError):
                inspect(data)


if __name__ == '__main__':
    unittest.main()
