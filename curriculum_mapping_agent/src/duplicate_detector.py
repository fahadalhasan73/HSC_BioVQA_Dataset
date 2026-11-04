import hashlib
import json
from typing import Any


def build_question_fingerprint(
    raw: dict[str, Any],
    normalized: dict[str, Any],
    include_options: bool = True,
    include_stimulus: bool = True,
) -> str:
    payload: dict[str, Any] = {
        "question": normalized.get("question_normalized_bn", ""),
        "question_type": str(raw.get("question_type", "")).upper(),
    }

    if include_stimulus:
        payload["stimulus"] = normalized.get("stimulus_normalized_bn", "")

    if include_options:
        payload["options"] = normalized.get("options_normalized", {})

    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_existing_fingerprint_index(
    questions: list[dict[str, Any]]
) -> dict[str, str]:
    index: dict[str, str] = {}
    for q in questions:
        fingerprint = q.get("fingerprint")
        question_id = q.get("question_id")
        if fingerprint and question_id:
            index[fingerprint] = question_id
    return index
