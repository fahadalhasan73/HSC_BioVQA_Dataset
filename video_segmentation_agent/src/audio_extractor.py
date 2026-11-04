from pathlib import Path
import subprocess

from static_ffmpeg import run


def extract_audio(
    video_path: str | Path,
    output_wav: str | Path,
    sample_rate: int = 16000,
    channels: int = 1,
) -> Path:
    """
    Extract audio from a video and convert it to PCM WAV.

    The default output is:
        - 16 kHz
        - mono
        - 16-bit PCM

    This format is suitable for Faster-Whisper ASR.
    """

    video_path = Path(video_path).resolve()
    output_wav = Path(output_wav).resolve()

    # ---------------------------------------------------------
    # 1. Validate input video
    # ---------------------------------------------------------
    if not video_path.exists():
        raise FileNotFoundError(
            f"Video file not found: {video_path}"
        )

    if not video_path.is_file():
        raise ValueError(
            f"Input path is not a file: {video_path}"
        )

    if sample_rate <= 0:
        raise ValueError(
            "sample_rate must be greater than 0."
        )

    if channels <= 0:
        raise ValueError(
            "channels must be greater than 0."
        )

    # ---------------------------------------------------------
    # 2. Prepare output directory
    # ---------------------------------------------------------
    output_wav.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ---------------------------------------------------------
    # 3. Obtain static FFmpeg executable
    # ---------------------------------------------------------
    try:
        ffmpeg_path, _ = (
            run.get_or_fetch_platform_executables_else_raise()
        )

    except Exception as exc:
        raise RuntimeError(
            "Unable to obtain FFmpeg from static-ffmpeg."
        ) from exc

    ffmpeg_path = Path(ffmpeg_path)

    if not ffmpeg_path.exists():
        raise FileNotFoundError(
            f"FFmpeg executable was not found: {ffmpeg_path}"
        )

    # ---------------------------------------------------------
    # 4. FFmpeg command
    # ---------------------------------------------------------
    cmd = [
        str(ffmpeg_path),

        # Replace existing output.
        "-y",

        # Reduce normal console noise.
        "-hide_banner",
        "-loglevel",
        "error",

        # Input video.
        "-i",
        str(video_path),

        # Disable video output.
        "-vn",

        # Select audio stream if present.
        "-map",
        "0:a:0",

        # Number of channels.
        "-ac",
        str(channels),

        # Audio sample rate.
        "-ar",
        str(sample_rate),

        # 16-bit PCM WAV.
        "-c:a",
        "pcm_s16le",

        str(output_wav),
    ]

    # ---------------------------------------------------------
    # 5. Execute FFmpeg
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
        # Remove incomplete output if FFmpeg failed.
        if output_wav.exists():
            try:
                output_wav.unlink()
            except OSError:
                pass

        raise RuntimeError(
            f"FFmpeg audio extraction failed.\n\n"
            f"Input:\n{video_path}\n\n"
            f"Output:\n{output_wav}\n\n"
            f"Return code: {exc.returncode}\n\n"
            f"stderr:\n{exc.stderr}"
        ) from exc

    except OSError as exc:
        raise RuntimeError(
            f"Could not execute FFmpeg at:\n"
            f"{ffmpeg_path}"
        ) from exc

    # ---------------------------------------------------------
    # 6. Verify output
    # ---------------------------------------------------------
    if not output_wav.exists():
        raise RuntimeError(
            "FFmpeg completed but the WAV file "
            "was not created."
        )

    if output_wav.stat().st_size == 0:
        raise RuntimeError(
            "FFmpeg created an empty WAV file."
        )

    return output_wav