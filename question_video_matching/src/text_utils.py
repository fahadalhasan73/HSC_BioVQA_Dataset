import re
from typing import Any, Dict


_WS_RE = re.compile(r"\s+", flags=re.UNICODE)


def normalize_text(value: Any) -> str:
    text = "" if value is None else str(value)
    return _WS_RE.sub(" ", text).strip()


def _first_text(record: Dict[str, Any], keys) -> str:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return normalize_text(value)
    return ""


def question_text(question: Dict[str, Any], include_options: bool = True) -> str:
    """Return the best available original question text without paraphrasing it."""
    stem = _first_text(
        question,
        (
            "question_original_bn",
            "question_bangla",
            "question_text",
            "question",
            "stem",
            "text",
        ),
    )

    stimulus = _first_text(
        question,
        ("stimulus_original_bn", "stimulus", "passage", "context"),
    )

    parts = [x for x in (stimulus, stem) if x]

    if include_options:
        options = question.get("options")
        if isinstance(options, dict):
            option_texts = []
            for key in ("A", "B", "C", "D", "a", "b", "c", "d"):
                value = options.get(key)
                if value not in (None, ""):
                    option_texts.append(f"{key}: {normalize_text(value)}")
            if not option_texts:
                option_texts = [
                    f"{k}: {normalize_text(v)}"
                    for k, v in options.items()
                    if v not in (None, "")
                ]
            parts.extend(option_texts)
        elif isinstance(options, list):
            parts.extend(normalize_text(x) for x in options if x not in (None, ""))

    return normalize_text(" ".join(parts))


def segment_text(segment: Dict[str, Any]) -> str:
    return _first_text(
        segment,
        (
            "transcript",
            "transcript_text",
            "text",
            "text_normalized",
        ),
    )
