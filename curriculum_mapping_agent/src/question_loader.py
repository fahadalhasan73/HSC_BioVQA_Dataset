import json
from pathlib import Path
from typing import Any


class QuestionInputError(ValueError):
    pass


def load_question_batch(path: str | Path) -> list[dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Input batch not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, list):
        questions = payload
    elif isinstance(payload, dict) and isinstance(payload.get("questions"), list):
        questions = payload["questions"]
    else:
        raise QuestionInputError(
            "Input JSON must be either a list of question objects or "
            "an object containing a 'questions' list."
        )

    for index, question in enumerate(questions):
        validate_raw_question(question, index)

    return questions


def validate_raw_question(question: dict[str, Any], index: int | None = None) -> None:
    prefix = f"Question at input index {index}" if index is not None else "Question"

    if not isinstance(question, dict):
        raise QuestionInputError(f"{prefix} must be a JSON object.")

    text = question.get("question_original_bn")
    if not isinstance(text, str) or not text.strip():
        raise QuestionInputError(
            f"{prefix} requires non-empty 'question_original_bn'."
        )

    qtype = question.get("question_type")
    if not isinstance(qtype, str) or not qtype.strip():
        raise QuestionInputError(f"{prefix} requires 'question_type'.")

    if qtype.upper() == "MCQ":
        options = question.get("options")
        if not isinstance(options, dict):
            raise QuestionInputError(f"{prefix} MCQ requires 'options' object.")
        required = {"A", "B", "C", "D"}
        missing = required - set(options)
        if missing:
            raise QuestionInputError(
                f"{prefix} is missing MCQ option(s): {sorted(missing)}"
            )
        for key in required:
            if not isinstance(options[key], str) or not options[key].strip():
                raise QuestionInputError(
                    f"{prefix} option {key} must contain text."
                )

    source = question.get("source")
    if not isinstance(source, dict):
        raise QuestionInputError(f"{prefix} requires a 'source' object.")
