import json
import os
import shutil
from datetime import datetime
from pathlib import Path


def atomic_write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    with tmp.open("r", encoding="utf-8") as f:
        json.load(f)
    os.replace(tmp, path)


def save_mapping_store(path, backup_dir, payload, create_backup=True):
    path = Path(path)
    backup_dir = Path(backup_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    if create_backup and path.exists():
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        shutil.copy2(path, backup_dir / f"mapping_{stamp}.json")

    atomic_write_json(path, payload)
