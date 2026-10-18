#!/usr/bin/env python3
"""Verify the distributed APK's identity, signing and foldable declarations."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
TOOLS=Path(os.environ.get('DM_ANDROID_TOOLS',str(Path.home()/'dm-work/tools/android')))

def verify(apk,release=False):
    env=dict(os.environ,JAVA_HOME=str(TOOLS/'jdk'),PATH=str(TOOLS/'jdk/bin')+os.pathsep+os.environ['PATH'])
    def tool(name,*args):return subprocess.check_output([str(TOOLS/'build-tools'/name),*map(str,args)],env=env,text=True)
    badging=tool('aapt2','dump','badging',apk)
    assert "package: name='org.d2r.android.port'" in badging
    assert "native-code: 'arm64-v8a'" in badging
    assert "minSdkVersion:'29'" in badging
    manifest=tool('aapt2','dump','xmltree',apk,'--file','AndroidManifest.xml')
    assert 'org.d2r.android.port.FoldDiagnosticActivity' in manifest
    assert manifest.count('android:resizeableActivity')==3
    signature=tool('apksigner','verify','--verbose','--print-certs',apk)
    tool('zipalign','-c','-P','16','4',apk)
    if release:
        assert 'application-debuggable' not in badging
        fingerprint=re.search(r'Signer #1 certificate SHA-256 digest: ([0-9a-f]+)',signature).group(1)
        expected=(ROOT.parents[1]/'.github/release-certificate.sha256').read_text().strip()
        assert fingerprint==expected, 'Unexpected release signing certificate'
        code=int(re.search(r"versionCode='(\d+)'",badging).group(1))
        assert code>=10000
    with zipfile.ZipFile(apk) as z:
        names=z.namelist()
        assert 'classes.dex' in names
        assert 'lib/arm64-v8a/libdmandroid.so' in names
        assert not any(Path(n).name in {'prod.keys','title.keys','libdmguest_main.so','libdmguest_sdk.so','libdmguest_subsdk0.so'} or Path(n).suffix.lower() in {'.nsp','.nsz','.xci','.nca','.d2s'} for n in names)
    print('APK identity, signature, alignment and foldable declarations verified; device execution not tested.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('apk',type=Path);parser.add_argument('--release',action='store_true');args=parser.parse_args()
    verify(args.apk,args.release)
