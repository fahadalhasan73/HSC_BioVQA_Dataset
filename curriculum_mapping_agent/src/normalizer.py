import re
import unicodedata
from typing import Any


_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: str | None) -> str:
    if text is None:
        return ""
    text = unicodedata.normalize("NFC", str(text))
    text = text.replace("\u200c", "").replace("\u200d", "")
    text = text.replace("“", '"').replace("”", '"').replace("‘", "'").replace("’", "'")
    text = _WHITESPACE_RE.sub(" ", text).strip()
    return text


def normalize_question(raw: dict[str, Any]) -> dict[str, Any]:
    normalized = {
        "question_normalized_bn": normalize_text(raw.get("question_original_bn")),
        "stimulus_normalized_bn": normalize_text(raw.get("stimulus_original_bn")),
        "options_normalized": {},
    }

    options = raw.get("options") or {}
    for key in ("A", "B", "C", "D"):
        if key in options:
            normalized["options_normalized"][key] = normalize_text(options[key])

    return normalized


def build_question_context(raw: dict[str, Any], normalized: dict[str, Any]) -> str:
    parts: list[str] = []

    stimulus = normalized.get("stimulus_normalized_bn")
    if stimulus:
        parts.append(f"Stimulus:\n{stimulus}")

    parts.append(f"Question:\n{normalized['question_normalized_bn']}")

    options = normalized.get("options_normalized") or {}
    if options:
        option_text = "\n".join(f"{k}. {options[k]}" for k in ("A", "B", "C", "D") if k in options)
        parts.append(
            "Options (use only as curriculum context; do not solve the MCQ):\n"
            + option_text
        )

    source = raw.get("source") or {}
    if source.get("paper"):
        parts.append(f"Source paper: {source['paper']}")

    return "\n\n".join(parts)
