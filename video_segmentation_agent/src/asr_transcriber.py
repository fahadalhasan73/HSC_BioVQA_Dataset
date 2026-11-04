from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel


DEFAULT_BIOLOGY_PROMPT = """
এই অডিওটি একটি বাংলা HSC Biology lecture।

বক্তা বাংলা এবং English মিশিয়ে কথা বলতে পারেন।

Transcription rules:
- বাংলা শব্দ বাংলা লিপিতে লিখতে হবে।
- English শব্দ English alphabet-এ রাখতে হবে।
- Biology এবং scientific terminology যেভাবে বলা হয়েছে
  সেভাবেই রাখতে হবে।
- Cell, Cell Division, Cellularity, DNA, RNA, Chromosome,
  Chromatid, Centromere, Mitosis, Meiosis, Interphase,
  Prophase, Metaphase, Anaphase, Telophase,
  Cytokinesis, Karyokinesis, Figure, Analysis ইত্যাদি
  English term English-এই থাকবে।
- কোনো translation করা যাবে না।
- কোনো paraphrase করা যাবে না।
- Spoken content যতটা সম্ভব verbatim রাখতে হবে।
""".strip()


def _to_bool(value: Any, default: bool = False) -> bool:
    """
    Convert configuration values safely to boolean.

    YAML normally gives real True/False values, but this helper
    also safely handles strings such as "true" and "false".
    """
    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.strip().lower() in {
            "1",
            "true",
            "yes",
            "y",
            "on",
        }

    return bool(value)


def transcribe_audio(
    audio_path: str | Path,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """
    Transcribe a Bangla-English HSC Biology lecture using
    Faster-Whisper.

    The function preserves:
    - segment timestamps
    - raw ASR text
    - Bangla-English code switching
    - optional word-level timestamps
    - ASR configuration metadata
    """

    audio_path = Path(audio_path).resolve()

    # ---------------------------------------------------------
    # 1. Validate audio
    # ---------------------------------------------------------
    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    if not audio_path.is_file():
        raise ValueError(
            f"Audio path is not a file: {audio_path}"
        )

    # ---------------------------------------------------------
    # 2. Read ASR configuration
    # ---------------------------------------------------------
    model_name = cfg.get(
        "model",
        "large-v3",
    )

    device = cfg.get(
        "device",
        "cpu",
    )

    compute_type = cfg.get(
        "compute_type",
        "int8",
    )

    language = cfg.get(
        "language",
        "bn",
    )

    task = cfg.get(
        "task",
        "transcribe",
    )

    beam_size = int(
        cfg.get(
            "beam_size",
            5,
        )
    )

    vad_filter = _to_bool(
        cfg.get("vad_filter"),
        default=True,
    )

    word_timestamps = _to_bool(
        cfg.get("word_timestamps"),
        default=False,
    )

    condition_on_previous_text = _to_bool(
        cfg.get("condition_on_previous_text"),
        default=True,
    )

    transcription_policy = cfg.get(
        "transcription_policy",
        "verbatim_code_switched_bn_en",
    )

    initial_prompt = cfg.get(
        "initial_prompt"
    )

    # If YAML has no prompt or an empty prompt, use our default.
    if not initial_prompt:
        initial_prompt = DEFAULT_BIOLOGY_PROMPT

    # ---------------------------------------------------------
    # 3. Load Faster-Whisper
    # ---------------------------------------------------------
    print(
        f"Loading Faster-Whisper model: {model_name}",
        flush=True,
    )

    print(
        f"Device: {device} | "
        f"Compute type: {compute_type}",
        flush=True,
    )

    model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type,
    )

    # ---------------------------------------------------------
    # 4. Start transcription
    # ---------------------------------------------------------
    segments_generator, info = model.transcribe(
        str(audio_path),

        # Bengali is the dominant lecture language.
        language=language,

        # Never translate the lecture.
        task=task,

        beam_size=beam_size,

        vad_filter=vad_filter,

        word_timestamps=word_timestamps,

        initial_prompt=initial_prompt,

        # Preserve lecture context between nearby utterances.
        condition_on_previous_text=condition_on_previous_text,
    )

    segments: list[dict[str, Any]] = []
    full_text_parts: list[str] = []

    # ---------------------------------------------------------
    # 5. Consume Whisper generator
    # ---------------------------------------------------------
    for index, segment in enumerate(
        segments_generator
    ):
        text = (
            segment.text
            or ""
        ).strip()

        if not text:
            continue

        # Visible progress so long CPU jobs do not look frozen.
        print(
            f"ASR [{index + 1:04d}] "
            f"{segment.start:8.2f}s -> "
            f"{segment.end:8.2f}s | "
            f"{text[:100]}",
            flush=True,
        )

        segment_data: dict[str, Any] = {
            "asr_segment_id": index,

            "start_sec": round(
                float(segment.start),
                3,
            ),

            "end_sec": round(
                float(segment.end),
                3,
            ),

            "text": text,
        }

        # -----------------------------------------------------
        # 6. Save word timestamps when enabled
        # -----------------------------------------------------
        if word_timestamps:
            words = []

            for word in (
                getattr(segment, "words", None)
                or []
            ):
                words.append(
                    {
                        "start_sec": (
                            round(
                                float(word.start),
                                3,
                            )
                            if word.start is not None
                            else None
                        ),

                        "end_sec": (
                            round(
                                float(word.end),
                                3,
                            )
                            if word.end is not None
                            else None
                        ),

                        "word": (
                            word.word
                            or ""
                        ),

                        "probability": (
                            round(
                                float(word.probability),
                                6,
                            )
                            if getattr(
                                word,
                                "probability",
                                None,
                            )
                            is not None
                            else None
                        ),
                    }
                )

            segment_data["words"] = words

        segments.append(
            segment_data
        )

        full_text_parts.append(
            text
        )

    # ---------------------------------------------------------
    # 7. Return transcript artifact
    # ---------------------------------------------------------
    return {
        "engine": "faster-whisper",

        "model": model_name,

        "device": device,

        "compute_type": compute_type,

        "configured_language": language,

        "detected_language": getattr(
            info,
            "language",
            None,
        ),

        "language_probability": getattr(
            info,
            "language_probability",
            None,
        ),

        "task": task,

        "beam_size": beam_size,

        "vad_filter": vad_filter,

        "word_timestamps": word_timestamps,

        "condition_on_previous_text":
            condition_on_previous_text,

        "transcription_policy":
            transcription_policy,

        "human_verified": False,

        "transcript_status":
            "provisional_asr",

        "text": " ".join(
            full_text_parts
        ).strip(),

        "segments": segments,
    }