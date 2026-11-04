from typing import Any, Dict, Iterable, List


DEFAULT_REJECTED_STATUSES = {
    "low_information",
    "taxonomy_update_required",
    "failed",
    "error",
    "unmapped",
}


def mapping_is_usable(mapping: Dict[str, Any], rejected_statuses: Iterable[str] = ()) -> bool:
    if not isinstance(mapping, dict) or not mapping:
        return False

    rejected = {str(x).strip().lower() for x in rejected_statuses} or DEFAULT_REJECTED_STATUSES
    status = str(mapping.get("status", "")).strip().lower()
    if status and status in rejected:
        return False

    # Paper/chapter are the minimum useful anchors for candidate filtering.
    return bool(mapping.get("paper_id") and mapping.get("chapter_id"))


def generate_candidates(question: Dict[str, Any], segments: List[Dict[str, Any]], cfg: Dict[str, Any]):
    qm = question.get("curriculum_mapping") or {}
    rejected = cfg.get("rejected_mapping_statuses") or DEFAULT_REJECTED_STATUSES

    if not mapping_is_usable(qm, rejected):
        return []

    out = []
    for segment in segments:
        sm = segment.get("curriculum_mapping") or {}
        if not mapping_is_usable(sm, rejected):
            continue

        if cfg.get("require_same_paper", True) and qm.get("paper_id") != sm.get("paper_id"):
            continue
        if cfg.get("require_same_chapter", True) and qm.get("chapter_id") != sm.get("chapter_id"):
            continue
        out.append(segment)

    return out
