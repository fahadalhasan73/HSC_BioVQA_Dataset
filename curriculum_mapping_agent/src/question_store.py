import hashlib
import json
import os
import shutil
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class QuestionStore:
    def __init__(
        self,
        path: str | Path,
        backup_dir: str | Path,
    ):
        self.path = Path(path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.data = self._load_or_create()

    def _load_or_create(self) -> dict[str, Any]:
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "dataset": {
                "name": "HSC-VQA Question Registry",
                "schema_version": "1.0",
                "revision": 0,
                "total_questions": 0,
                "next_question_number": 1,
                "next_batch_number": 1,
                "last_updated": None,
            },
            "batches": [],
            "questions": [],
        }
        self.data = data
        self.save()
        return data

    @property
    def questions(self) -> list[dict[str, Any]]:
        return self.data["questions"]

    def make_backup(self) -> Path | None:
        if not self.path.exists():
            return None
        revision = int(self.data["dataset"].get("revision", 0))
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = self.backup_dir / (
            f"question_rev_{revision:05d}_{stamp}.json"
        )
        shutil.copy2(self.path, destination)
        return destination

    def _next_question_id(self) -> str:
        number = int(self.data["dataset"]["next_question_number"])
        self.data["dataset"]["next_question_number"] = number + 1
        return f"HSCQ_{number:06d}"

    def _next_batch_id(self) -> str:
        number = int(self.data["dataset"]["next_batch_number"])
        self.data["dataset"]["next_batch_number"] = number + 1
        return f"BATCH_{number:05d}"

    def find_batch_by_input_fingerprint(
        self,
        input_fingerprint: str,
    ) -> dict[str, Any] | None:
        for batch in self.data["batches"]:
            if batch.get("input_fingerprint") == input_fingerprint:
                return batch
        return None

    def start_or_resume_batch(
        self,
        input_file: str,
        input_fingerprint: str,
        submitted_count: int,
    ) -> dict[str, Any]:
        existing = self.find_batch_by_input_fingerprint(input_fingerprint)
        if existing:
            return existing

        batch = {
            "batch_id": self._next_batch_id(),
            "input_file": input_file,
            "input_fingerprint": input_fingerprint,
            "status": "processing",
            "submitted_count": submitted_count,
            "processed_indices": [],
            "added_count": 0,
            "duplicate_count": 0,
            "error_count": 0,
            "duplicates": [],
            "errors": [],
            "started_at": utc_now_iso(),
            "completed_at": None,
        }
        self.data["batches"].append(batch)
        self._touch_revision()
        self.save()
        return batch

    def allocate_question_id(self) -> str:
        return self._next_question_id()

    def add_question(self, question_record: dict[str, Any]) -> None:
        self.data["questions"].append(question_record)
        self.data["dataset"]["total_questions"] = len(self.data["questions"])

    def mark_input_index_processed(self, batch: dict[str, Any], index: int) -> None:
        if index not in batch["processed_indices"]:
            batch["processed_indices"].append(index)
            batch["processed_indices"].sort()
        # A successful retry supersedes any earlier error for this input index.
        batch["errors"] = [e for e in batch.get("errors", []) if e.get("input_index") != index]
        batch["error_count"] = len(batch["errors"])

    def record_duplicate(
        self,
        batch: dict[str, Any],
        input_index: int,
        existing_question_id: str,
    ) -> None:
        batch["duplicates"].append(
            {
                "input_index": input_index,
                "existing_question_id": existing_question_id,
            }
        )
        batch["duplicate_count"] = len(batch["duplicates"])
        self.mark_input_index_processed(batch, input_index)

    def record_error(
        self,
        batch: dict[str, Any],
        input_index: int,
        error: str,
    ) -> None:
        batch["errors"] = [e for e in batch.get("errors", []) if e.get("input_index") != input_index]
        batch["errors"].append({"input_index": input_index, "error": error})
        batch["error_count"] = len(batch["errors"])
        # Do not mark as processed: rerunning the same batch will retry it.

    def complete_batch(self, batch: dict[str, Any]) -> None:
        batch["status"] = "completed"
        batch["completed_at"] = utc_now_iso()
        batch["added_count"] = sum(
            1
            for q in self.data["questions"]
            if q.get("batch_id") == batch["batch_id"]
        )
        self._touch_revision()
        self.save()

    def _touch_revision(self) -> None:
        self.data["dataset"]["revision"] = (
            int(self.data["dataset"].get("revision", 0)) + 1
        )
        self.data["dataset"]["last_updated"] = utc_now_iso()

    def checkpoint(self) -> None:
        self._touch_revision()
        self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")

        with temp.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())

        # Validate the temporary file before replacing the master.
        with temp.open("r", encoding="utf-8") as f:
            json.load(f)

        os.replace(temp, self.path)
