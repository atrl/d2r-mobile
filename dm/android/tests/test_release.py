#!/usr/bin/env python3
import os
from pathlib import Path
import subprocess
import sys
import unittest

BUILD = Path(__file__).resolve().parents[1] / 'tools/build.py'
class ReleaseContract(unittest.TestCase):
    def test_missing_signer_fails_before_build(self):
        env = {k:v for k,v in os.environ.items() if not k.startswith('D2R_')}
        p = subprocess.run([sys.executable,str(BUILD),'--game-run','--release','--version-code','10000'], env=env, capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0)
        self.assertIn('release signing credentials are required',p.stderr)
    def test_bad_version_code(self):
        for code in ['0','-1','2100000001']:
            p=subprocess.run([sys.executable,str(BUILD),'--version-code',code],capture_output=True,text=True)
            self.assertNotEqual(p.returncode,0)
            self.assertIn('version-code must be',p.stderr)
if __name__=='__main__': unittest.main()
