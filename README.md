# HSC BioVQA Dataset

**VQA dataset based on HSC questions and Bangla Biology video lectures**

This repository contains the reproducible dataset-construction pipeline for the CSE 499A project. The project keeps question annotation, video segmentation, and question-video matching as separate components while forcing them to use one shared controlled HSC Biology taxonomy.

## Core architecture

1. `curriculum_mapping_agent/` maps original HSC questions to taxonomy IDs.
2. `video_segmentation_agent/` converts lecture videos into coherent timestamped curriculum-aligned segments.
3. `question_video_matching/` matches mapped questions to mapped video segments and records evidence-oriented candidate pairs.
4. `shared/` contains the canonical taxonomy, schemas, and common usage rules.
5. `data/` stores raw inputs, intermediate artifacts, master registries, backups, exports, and final dataset views.

## Important design rules

- Original HSC question text is never paraphrased by the pipeline.
- The canonical taxonomy is read-only to agents.
- Agents return taxonomy IDs; they never create taxonomy nodes automatically.
- Missing concepts produce `TAXONOMY_UPDATE_REQUIRED` for human taxonomy review.
- Question annotations, video segment annotations, and question-video mappings remain separate registries.
- The current canonical taxonomy contains Biology First Paper content. `HSC_BIO_P2` is reserved for future Biology Second Paper expansion.
- Diagram-dependent questions are currently excluded from the question corpus.
- The integrated question retriever uses a Unicode-aware tokenizer that preserves Bangla combining marks.

## Environment

Recommended: Python 3.11 or 3.12 for the smoothest multimedia/ASR dependency support. The question-only agent can also run on newer Python versions if its dependencies support them.

System dependencies:

- `ffmpeg`
- `ffprobe`

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Copy/edit the root `.env` file and set your Gemini API key:

```text
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.6-flash
```

The `.env` file is ignored by Git.

## Commands

Validate the repository/environment:

```powershell
python scripts/validate_environment.py
```

Run all local tests:

```powershell
python -m pytest -q
```

Map a question batch:

```powershell
python -m curriculum_mapping_agent.src.main --input data/questions/incoming/barishal_2025_raw_input_batch_01.json
```

Run video segmentation end-to-end:

```powershell
python -m video_segmentation_agent.src.main --video data/videos/incoming/YOUR_VIDEO.mp4
```

Run question-video matching:

```powershell
python -m question_video_matching.src.matcher
```

Export master registries to CSV:

```powershell
python scripts/export_csv.py
```

See `FOLDER_STRUCTURE.txt` for the full repository map and the README files inside data folders for artifact meanings.
