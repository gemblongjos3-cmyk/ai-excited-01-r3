import hashlib
import os
import shutil
import sys
from pathlib import Path

def jpeg_dimensions(data):
    if len(data) < 4 or data[:2] != b"\xff\xd8" or data[-2:] != b"\xff\xd9": raise ValueError("invalid JPEG SOI/EOI markers")
    i=2; sof=set(range(0xC0,0xC4))|set(range(0xC5,0xC8))|set(range(0xC9,0xCC))|set(range(0xCD,0xD0))
    while i<len(data):
        while i<len(data) and data[i]!=0xFF: i+=1
        while i<len(data) and data[i]==0xFF: i+=1
        if i>=len(data): break
        m=data[i]; i+=1
        if m in (0xD8,0xD9) or 0xD0<=m<=0xD7: continue
        if i+2>len(data): break
        n=int.from_bytes(data[i:i+2],"big")
        if n<2 or i+n>len(data): break
        if m in sof:
            if n<7: break
            return int.from_bytes(data[i+5:i+7],"big"),int.from_bytes(data[i+3:i+5],"big")
        i+=n
    raise ValueError("JPEG SOF dimensions not found")

script_dir=Path(__file__).resolve().parent
source=script_dir/"entry.jpg"
if not source.exists(): source=Path.cwd()/"entry.jpg"
try:
    data=source.read_bytes()
    if len(data)>1048576: raise ValueError("JPEG exceeds 1048576 bytes")
    width,height=jpeg_dimensions(data)
    if width>1024 or height>1024: raise ValueError("JPEG side exceeds 1024 pixels")
except (OSError,ValueError) as exc:
    print(f"error: {exc}",file=sys.stderr); raise SystemExit(1)
dest=Path(os.environ.get("MAKEFUN_OUTPUT_DIR","/output"))/"entry.png"
dest.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(source,dest)
copied=dest.read_bytes(); source_hash=hashlib.sha256(data).hexdigest(); copied_hash=hashlib.sha256(copied).hexdigest()
if copied_hash!=source_hash: print("error: copied file sha256 does not match source",file=sys.stderr); raise SystemExit(1)
print(f"ai-excited-01 -> {dest} | {len(copied)} bytes | {width}x{height} | sha256 {copied_hash}")
