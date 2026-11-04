from pathlib import Path
from typing import Any
import json
import subprocess

from static_ffmpeg import run


def extract_metadata(
    video_path: str | Path,
) -> dict[str, Any]:
    """
    Extract metadata from a video using the ffprobe binary supplied
    by the static-ffmpeg Python package.

    Parameters
    ----------
    video_path:
        Path to the input video.

    Returns
    -------
    dict
        Basic video/audio/container metadata.
    """

    video_path = Path(video_path).resolve()

    # ---------------------------------------------------------
    # 1. Validate input
    # ---------------------------------------------------------
    if not video_path.exists():
        raise FileNotFoundError(
            f"Video file not found: {video_path}"
        )

    if not video_path.is_file():
        raise ValueError(
            f"Input path is not a file: {video_path}"
        )

    # ---------------------------------------------------------
    # 2. Obtain static FFmpeg / FFprobe executable paths
    # ---------------------------------------------------------
    try:
        _, ffprobe_path = (
            run.get_or_fetch_platform_executables_else_raise()
        )
    except Exception as exc:
        raise RuntimeError(
            "Unable to obtain ffprobe from static-ffmpeg."
        ) from exc

    ffprobe_path = Path(ffprobe_path)

    if not ffprobe_path.exists():
        raise FileNotFoundError(
            f"ffprobe executable was not found: {ffprobe_path}"
        )

    # ---------------------------------------------------------
    # 3. Build ffprobe command
    # ---------------------------------------------------------
    cmd = [
        str(ffprobe_path),
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(video_path),
    ]

    # ---------------------------------------------------------
    # 4. Execute ffprobe
    # ---------------------------------------------------------
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )

    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"ffprobe failed for video:\n"
            f"{video_path}\n\n"
            f"Return code: {exc.returncode}\n"
            f"stderr:\n{exc.stderr}"
        ) from exc

    except OSError as exc:
        raise RuntimeError(
            f"Could not execute ffprobe at:\n{ffprobe_path}"
        ) from exc

    # ---------------------------------------------------------
    # 5. Parse JSON returned by ffprobe
    # ---------------------------------------------------------
    try:
        payload = json.loads(result.stdout)

    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "ffprobe returned invalid JSON.\n"
            f"Output:\n{result.stdout[:1000]}"
        ) from exc

    format_info = payload.get("format", {})
    streams = payload.get("streams", [])

    # ---------------------------------------------------------
    # 6. Locate video and audio streams
    # ---------------------------------------------------------
    video_stream = next(
        (
            stream
            for stream in streams
            if stream.get("codec_type") == "video"
        ),
        {},
    )

    audio_stream = next(
        (
            stream
            for stream in streams
            if stream.get("codec_type") == "audio"
        ),
        {},
    )

    # ---------------------------------------------------------
    # 7. Duration
    # ---------------------------------------------------------
    try:
        duration_seconds = float(
            format_info.get("duration", 0.0) or 0.0
        )
    except (TypeError, ValueError):
        duration_seconds = 0.0

    # ---------------------------------------------------------
    # 8. File size
    # ---------------------------------------------------------
    try:
        file_size_bytes = int(
            format_info.get("size", 0) or 0
        )
    except (TypeError, ValueError):
        file_size_bytes = video_path.stat().st_size

    # ---------------------------------------------------------
    # 9. Frame rate helper
    # ---------------------------------------------------------
    frame_rate = None

    frame_rate_raw = (
        video_stream.get("avg_frame_rate")
        or video_stream.get("r_frame_rate")
    )

    if frame_rate_raw and frame_rate_raw != "0/0":
        try:
            numerator, denominator = frame_rate_raw.split("/")
            denominator_value = float(denominator)

            if denominator_value != 0:
                frame_rate = (
                    float(numerator)
                    / denominator_value
                )
        except (ValueError, ZeroDivisionError):
            frame_rate = None

    # ---------------------------------------------------------
    # 10. Return normalized metadata
    # ---------------------------------------------------------
    return {
        "source_file": video_path.name,
        "source_path": str(video_path),

        "duration_seconds": round(
            duration_seconds,
            3,
        ),

        "file_size_bytes": file_size_bytes,

        "container_format": format_info.get(
            "format_name"
        ),

        "container_long_name": format_info.get(
            "format_long_name"
        ),

        "video_present": bool(video_stream),

        "video_codec": video_stream.get(
            "codec_name"
        ),

        "video_codec_long_name": video_stream.get(
            "codec_long_name"
        ),

        "width": video_stream.get(
            "width"
        ),

        "height": video_stream.get(
            "height"
        ),

        "frame_rate": (
            round(frame_rate, 3)
            if frame_rate is not None
            else None
        ),

        "pixel_format": video_stream.get(
            "pix_fmt"
        ),

        "audio_present": bool(audio_stream),

        "audio_codec": audio_stream.get(
            "codec_name"
        ),

        "audio_codec_long_name": audio_stream.get(
            "codec_long_name"
        ),

        "audio_sample_rate": (
            int(audio_stream["sample_rate"])
            if audio_stream.get("sample_rate")
            else None
        ),

        "audio_channels": audio_stream.get(
            "channels"
        ),

        "audio_channel_layout": audio_stream.get(
            "channel_layout"
        ),
    }