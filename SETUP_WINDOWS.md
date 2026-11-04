# Windows Quick Setup

From the `HSC_BioVQA_Dataset` root in PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r requirements.txt
```

Install FFmpeg separately and make sure both commands work:

```powershell
ffmpeg -version
ffprobe -version
```

Edit `.env`:

```text
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.6-flash
WHISPER_MODEL=small
```

Validate:

```powershell
python scripts/validate_environment.py
python -m pytest -q
```

Question mapping:

```powershell
python -m curriculum_mapping_agent.src.main --input data/questions/incoming/barishal_2025_raw_input_batch_01.json
```

Video segmentation:

```powershell
python -m video_segmentation_agent.src.main --video data/videos/incoming/YOUR_VIDEO.mp4
```

Question-video matching:

```powershell
python -m question_video_matching.src.matcher
```

The local ASR model is downloaded by `faster-whisper` the first time a model name such as `small` is used.
