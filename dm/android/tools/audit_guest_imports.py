#!/usr/bin/env python3
"""Static relocation coverage for recovered main/sdk against a built Android host.
核对恢复模块的重定位与实际宿主 HLE 注册表；不替代运行验证。
"""
import struct,json,argparse,hashlib
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('images', type=Path, help='directory containing main/sdk.apple-patched.bin')
parser.add_argument('host', type=Path, help='built libdmandroid.so with dm_hle/dm_force sections')
args=parser.parse_args()
root=args.images
def cstr(b,at):return b[at:b.index(0,at)].decode()
def guest(name):
 b=(root/f'{name}.apple-patched.bin').read_bytes();mod=struct.unpack_from('<I',b,4)[0];assert b[mod:mod+4]==b'MOD0';dyn=mod+struct.unpack_from('<i',b,mod+4)[0];tags={}
 while True:
  tag,value=struct.unpack_from('<qQ',b,dyn);dyn+=16
  if not tag:break
  tags[tag]=value
 syms=[]
 for at in range(tags[6],tags[5],24):
  n,info,other,section,value,size=struct.unpack_from('<IBBHQQ',b,at);syms.append((cstr(b,tags[5]+n),section,info>>4))
 imports=set(); references=set()
 for start,size in [(tags.get(7,0),tags.get(8,0)),(tags.get(23,0),tags.get(2,0))]:
  for at in range(start,start+size,24):
   off,info,add=struct.unpack_from('<QQq',b,at)
   if info&0xffffffff in (257,1025,1026):
    sym=syms[info>>32];references.add(sym[0])
    if not sym[1]:imports.add((sym[0],sym[2]))
 return {n for n,section,bind in syms if section},imports,references
b=args.host.read_bytes()
if b[:6] != b"\x7fELF\x02\x01": raise ValueError("expected little-endian ELF64 host")
shoff=struct.unpack_from('<Q',b,40)[0];shsize,shnum,shstr=struct.unpack_from('<HHH',b,58)
secs=[struct.unpack_from('<IIQQQQIIQQ',b,shoff+i*shsize) for i in range(shnum)]
strings=secs[shstr];names=b[strings[4]:strings[4]+strings[5]];byname={cstr(names,s[0]):s for s in secs}
def offset(va):
 for s in secs:
  if s[1]!=8 and s[3]<=va<s[3]+s[5]:return s[4]+va-s[3]
 raise ValueError(hex(va))
rela={}
for s in secs:
 if s[1]==4:
  for at in range(s[4],s[4]+s[5],24):
   dest,info,add=struct.unpack_from('<QQq',b,at)
   if info&0xffffffff==1027:rela[dest]=add
hle=set();forced=set()
for name,stride in [('dm_hle',16),('dm_force',24)]:
 s=byname[name]
 for va in range(s[3],s[3]+s[5],stride):
  symbol=cstr(b,offset(rela[va]));hle.add(symbol)
  if name=='dm_force':forced.add(symbol)
mods={n:guest(n) for n in ['main','sdk']};defined=set().union(*(d for d,i,r in mods.values()));report={}
for name,(d,imps,refs) in mods.items():
 missing=sorted(n for n,bind in imps if bind!=2 and n not in defined and n not in hle)
 report[name]={'imports':len(imps),'unresolved_strong':missing,'unresolved_movie':[n for n in missing if 'movie' in n]}
report['unreferenced_force_entries']=sorted(forced-set().union(*(r for d,i,r in mods.values())))
report['runtime_verified']=False
report['host_sha256']=hashlib.sha256(b).hexdigest()
report['guest_sha256']={n:hashlib.sha256((root/f'{n}.apple-patched.bin').read_bytes()).hexdigest() for n in mods}
print(json.dumps(report,indent=2))

if report["unreferenced_force_entries"] or any(report[n]["unresolved_strong"] for n in mods):
 raise SystemExit(1)
