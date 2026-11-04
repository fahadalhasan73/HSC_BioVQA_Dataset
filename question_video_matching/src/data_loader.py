import json
from pathlib import Path
from typing import Any, Dict, List


def _load(path) -> Any:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Required JSON file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_questions(path) -> List[Dict[str, Any]]:
    data = _load(path)
    if isinstance(data, list):
        questions = data
    elif isinstance(data, dict):
        questions = data.get("questions") or data.get("records") or []
    else:
        questions = []
    if not isinstance(questions, list):
        raise ValueError("Question store must contain a list under 'questions'.")
    return [q for q in questions if isinstance(q, dict)]


def load_segments(path) -> List[Dict[str, Any]]:
    data = _load(path)
    if isinstance(data, list):
        segments = data
    elif isinstance(data, dict):
        segments = data.get("segments") or []
        # Defensive support for registries that store per-video entries.
        if not segments and isinstance(data.get("videos"), list):
            segments = []
            for video in data["videos"]:
                if isinstance(video, dict) and isinstance(video.get("segments"), list):
                    segments.extend(video["segments"])
    else:
        segments = []
    if not isinstance(segments, list):
        raise ValueError("Segment store must contain a list under 'segments'.")
    return [s for s in segments if isinstance(s, dict)]
