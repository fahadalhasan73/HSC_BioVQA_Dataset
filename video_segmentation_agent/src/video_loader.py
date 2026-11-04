import re
from pathlib import Path
from .utils import sha256_file

class VideoInputError(ValueError): pass

def validate_video(path, accepted_extensions):
    p=Path(path).resolve()
    if not p.exists(): raise FileNotFoundError(f'Video not found: {p}')
    if p.suffix.lower() not in {x.lower() for x in accepted_extensions}: raise VideoInputError(f'Unsupported video extension: {p.suffix}')
    return p

def make_video_id(path: Path) -> str:
    base=re.sub(r'[^A-Za-z0-9_-]+','_',path.stem).strip('_') or 'VIDEO'
    return base

def video_manifest(path: Path):
    return {'video_id':make_video_id(path),'source_file':str(path),'source_filename':path.name,'file_sha256':sha256_file(path)}
