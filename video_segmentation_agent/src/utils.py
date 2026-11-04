import json, os, shutil, hashlib
from datetime import datetime, timezone
from pathlib import Path

def utc_now_iso(): return datetime.now(timezone.utc).isoformat()
def sha256_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()
def atomic_write_json(path, payload):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True); tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w',encoding='utf-8') as f:
        json.dump(payload,f,ensure_ascii=False,indent=2); f.flush(); os.fsync(f.fileno())
    with tmp.open('r',encoding='utf-8') as f: json.load(f)
    os.replace(tmp,path)
def backup_json(path, backup_dir):
    path=Path(path)
    if not path.exists(): return None
    b=Path(backup_dir); b.mkdir(parents=True,exist_ok=True)
    dest=b/f'{path.stem}_{datetime.now().strftime("%Y%m%d_%H%M%S")}{path.suffix}'
    shutil.copy2(path,dest); return dest

def sec_to_hms(sec: float) -> str:
    ms=int(round(sec*1000)); h=ms//3600000; ms%=3600000; m=ms//60000; ms%=60000; s=ms//1000; rem=ms%1000
    return f'{h:02d}:{m:02d}:{s:02d}.{rem:03d}'
