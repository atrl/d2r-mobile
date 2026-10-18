#!/usr/bin/env python3
"""合成数据验证整合包完整性和拒绝错误平台输入；不含游戏内容。
Synthetic tests for bundle integrity and rejection of wrong-platform inputs; no game content.
"""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from build_package import assemble, GAME_MODULES, GAME_LAYOUTS
from make_install_bundle import bundle, validate_package


class BundleTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for directory in ('game', 'romfs/data', 'shaders'):
            (self.root / directory).mkdir(parents=True)
        for name in GAME_MODULES + GAME_LAYOUTS:
            (self.root / 'game' / name).write_bytes(b'synthetic')
        (self.root / 'romfs/data/test.data').write_bytes(b'synthetic')
        (self.root / 'shaders/host-subgroup-size.txt').write_text('64')
        (self.root / 'shaders/test.spv').write_bytes(b'synthetic')
        derived = self.root / 'derived.tsv'
        derived.write_text('synthetic\n')
        self.package = self.root / 'data.zip'
        assemble(self.package, self.root / 'game', self.root / 'romfs', self.root / 'shaders', derived, quiet=True)

    def test_bundle_preserves_inputs_and_hashes(self):
        validate_package(self.package)
        apk = self.root / 'app.apk'
        apk.write_bytes(b'synthetic apk; CLI additionally verifies the release signature')
        output = self.root / 'bundle.zip'
        bundle(apk, self.package, output)
        with zipfile.ZipFile(output) as archive:
            self.assertEqual(archive.read('d2r-package.zip'), self.package.read_bytes())
            self.assertEqual(archive.read('D2R-Android-port.apk'), apk.read_bytes())
            for line in archive.read('SHA256SUMS').decode().splitlines():
                digest, name = line.split()
                self.assertEqual(digest, hashlib.sha256(archive.read(name)).hexdigest())
        with self.assertRaises(ValueError):
            bundle(apk, self.package, output)

    def test_apple_input_rejected(self):
        apple = self.root / 'apple.zip'
        with zipfile.ZipFile(apple, 'w') as archive:
            archive.writestr('prepared.json', '{"format":"d2r-mobile-prepared"}')
        with self.assertRaisesRegex(ValueError, 'iOS'):
            validate_package(apple)

    def test_path_traversal_rejected(self):
        with zipfile.ZipFile(self.package, 'a') as archive:
            archive.writestr('romfs/../manifest.json', '{}')
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            validate_package(self.package)

    def test_manifest_count_mismatch_rejected(self):
        with zipfile.ZipFile(self.package, 'a') as archive:
            archive.writestr('game/extra.so', b'extra')
        with self.assertRaisesRegex(ValueError, 'mismatch'):
            validate_package(self.package)


if __name__ == '__main__':
    unittest.main()
