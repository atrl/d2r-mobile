#!/usr/bin/env python3
import os,subprocess,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=(root/'native/gpu_driver.c').read_text();f=s[s.index('static int profile_matches_at('):s.index('int dm_vk_driver_validate(')]
with tempfile.TemporaryDirectory() as t:
 p=Path(t);base=p/'shaders';base.mkdir();variant=base/'subgroup64';variant.mkdir()
 (base/'host-subgroup-size.txt').write_text('32\n')
 c=p/'test.c';c.write_text('''#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <errno.h>
#include <ctype.h>
#include <string.h>
typedef struct {unsigned effective_shader_subgroup_size,subgroup_size,requested_subgroup_size;} dm_vk_driver;
static int driver_error(dm_vk_driver *d,const char *f,...){(void)d;(void)f;return 0;}
#define driver_log(...) ((void)0)
'''+f+'''\nint main(int argc,char **argv){(void)argc;dm_vk_driver d={atoi(argv[2]),128,atoi(argv[2])};return profile_matches(&d,argv[1])?0:42;}\n''')
 subprocess.run([os.environ.get('CC','cc'),'-Wall','-Wextra','-Werror',str(c),'-o',str(p/'test')],check=True)
 def check(size,code):assert subprocess.run([str(p/'test'),str(base),str(size)]).returncode==code
 check(32,0);check(64,42)
 (variant/'host-subgroup-size.txt').write_text('64\n');check(64,0);check(128,42)
 (variant/'host-subgroup-size.txt').write_text('32\n');check(64,42)
 (variant/'host-subgroup-size.txt').write_text('64x\n');check(64,42)
 print('Explicit Turnip64 validates matching variant; wrong, missing and malformed profiles rejected')
