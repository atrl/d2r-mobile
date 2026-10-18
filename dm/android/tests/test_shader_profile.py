#!/usr/bin/env python3
"""Exercise the production shader profile selector with physical32/64 fixtures."""
import os, subprocess, tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=(root/'native/nvn_vulkan_shader.inc').read_text()
function=source[source.index('static void shader_profile_check(void)'):source.index('static void *read_shader_file')]
with tempfile.TemporaryDirectory() as tmp:
 p=Path(tmp); cache=p/'shaders'; cache.mkdir()
 c=p/'test.c'; c.write_text('''#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <errno.h>
#include <stdarg.h>
static uint32_t gpu_subgroup_size;
#define LOG(...) ((void)0)
static void die(const char *format, ...) { (void)format; exit(42); }
'''+function+'''\nint main(int argc,char **argv){ (void)argc; gpu_subgroup_size=atoi(argv[1]); shader_profile_check(); puts(getenv("DM_VK_SHADERS")); return 0; }\n''')
 subprocess.run([os.environ.get('CC','cc'),'-Wall','-Wextra','-Werror',str(c),'-o',str(p/'test')],check=True)
 env=dict(os.environ,DM_VK_SHADERS=str(cache))
 def check(size,expected,path=None):
  r=subprocess.run([str(p/'test'),str(size)],env=env,capture_output=True,text=True)
  assert r.returncode==expected,(size,r.returncode,r.stderr)
  if path: assert r.stdout.strip()==str(path),r.stdout
 (cache/'host-subgroup-size.txt').write_text('32\n')
 check(32,0,cache); check(64,42)
 variant=cache/'subgroup64';variant.mkdir();(variant/'host-subgroup-size.txt').write_text('64\n')
 check(64,0,variant); check(32,0,cache);check(128,42)
 (variant/'host-subgroup-size.txt').write_text('32\n');check(64,42)
 (variant/'host-subgroup-size.txt').write_text('64 garbage\n');check(64,42)
 print('32 unchanged; 64 selects validated variant; missing/wrong/invalid profiles rejected')
