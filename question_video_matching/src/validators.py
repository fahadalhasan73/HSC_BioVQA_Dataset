from typing import Any, Dict, Iterable, List


def _unique_ids(records: Iterable[Dict[str, Any]], key: str, label: str):
    seen = set()
    for index, record in enumerate(records, start=1):
        value = record.get(key)
        if not value:
            raise ValueError(f"{label} at index {index} is missing required '{key}'.")
        if value in seen:
            raise ValueError(f"Duplicate {label} {key}: {value}")
        seen.add(value)
    return seen


def validate_inputs(questions: List[Dict[str, Any]], segments: List[Dict[str, Any]]):
    question_ids = _unique_ids(questions, "question_id", "question")
    segment_ids = _unique_ids(segments, "segment_id", "segment")
    for segment in segments:
        if not segment.get("video_id"):
            raise ValueError(f"Segment {segment.get('segment_id')} is missing video_id.")
        start = segment.get("start_sec", segment.get("start_time_sec"))
        end = segment.get("end_sec", segment.get("end_time_sec"))
        if start is not None and end is not None and float(end) <= float(start):
            raise ValueError(f"Segment {segment.get('segment_id')} has invalid timestamps: {start} -> {end}")
    return question_ids, segment_ids


def validate_pairs(pairs, question_ids, segment_ids):
    pair_ids = set()
    for pair in pairs:
        pid = pair.get("pair_id")
        if not pid:
            raise ValueError("A mapping pair is missing pair_id.")
        if pid in pair_ids:
            raise ValueError(f"Duplicate pair_id: {pid}")
        pair_ids.add(pid)
        if pair.get("question_id") not in question_ids:
            raise ValueError(f"Pair {pid} references unknown question_id: {pair.get('question_id')}")
        if pair.get("segment_id") not in segment_ids:
            raise ValueError(f"Pair {pid} references unknown segment_id: {pair.get('segment_id')}")
        score = float((pair.get("scores") or {}).get("final", -1))
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"Pair {pid} has invalid final score: {score}")
