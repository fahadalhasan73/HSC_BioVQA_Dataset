# HSC BioVQA Dataset  
## Complete Project Setup & Run Guide

This document explains how to set up and run the **HSC BioVQA Dataset** project on a new teammate's computer.

It covers:

- Cloning the GitHub repository
- Switching to the correct Git branch
- Installing Python
- Creating a virtual environment
- Installing dependencies
- Configuring environment variables
- Setting up Gemini API access
- Preparing Faster-Whisper
- Preparing input data
- Running the Curriculum Mapping Agent
- Running the Video Segmentation Agent
- Running the Question-Video Matching Agent
- Running tests
- Updating the repository
- Common troubleshooting

---

# 1. Project Overview

The project builds an HSC Biology question-to-video-segment dataset.

The current high-level pipeline is:

```text
HSC Questions
     │
     ▼
Curriculum Mapping Agent
     │
     ▼
question.json
     │
     │
     ├───────────────────────────────┐
     │                               │
     │                               ▼
     │                         Lecture Videos
     │                               │
     │                               ▼
     │                    Video Segmentation Agent
     │                               │
     │                               ▼
     │                          segments.json
     │                               │
     └───────────────┬───────────────┘
                     │
                     ▼
          Question-Video Matching Agent
                     │
                     ▼
       question_video_mapping.json
                     │
                     ▼
              hsc_biovqa.json
```

All agents use the same controlled HSC Biology taxonomy.

---

# 2. Repository

GitHub repository:

```text
https://github.com/fahadalhasan73/HSC_BioVQA_Dataset
```

Current team branches:

```text
main
├── fahad
├── ashik
└── shaira
```

### Branch purposes

| Branch | Purpose |
|---|---|
| `main` | Stable integrated project |
| `fahad` | Fahad's development branch |
| `ashik` | Ashik's development branch |
| `shaira` | Shaira's development branch |

---

# 3. System Requirements

Recommended:

- Windows 10/11 or macOS
- Git
- Python
- Internet connection
- Gemini API key
- Sufficient disk space for video and ASR models
- At least 8 GB RAM recommended

For a new setup, **Python 3.12 is recommended** to keep the development environments consistent.

The project has also been tested on other Python versions, but using the same version across teammates reduces dependency differences.

---

# 4. Install Git

Check whether Git is already installed:

```bash
git --version
```

Expected output will look similar to:

```text
git version 2.x.x
```

If Git is not installed, install it before continuing.

---

# 5. Install Python

Check Python:

## Windows

```powershell
python --version
```

## macOS

```bash
python3 --version
```

Recommended:

```text
Python 3.12.x
```

---

# 6. Clone the Repository

Open a terminal in the directory where you want to store the project.

Run:

```bash
git clone https://github.com/fahadalhasan73/HSC_BioVQA_Dataset.git
```

Enter the repository:

```bash
cd HSC_BioVQA_Dataset
```

Check:

```bash
git status
```

You should initially be on:

```text
main
```

---

# 7. Fetch All Team Branches

Run:

```bash
git fetch origin
```

Then:

```bash
git branch -a
```

Expected:

```text
* main
  remotes/origin/main
  remotes/origin/fahad
  remotes/origin/ashik
  remotes/origin/shaira
```

---

# 8. Switch to Your Own Branch

Each teammate should normally work on their own branch.

## Fahad

```bash
git switch -c fahad --track origin/fahad
```

## Ashik

```bash
git switch -c ashik --track origin/ashik
```

## Shaira

```bash
git switch -c shaira --track origin/shaira
```

If the branch already exists locally:

```bash
git switch fahad
```

or:

```bash
git switch ashik
```

or:

```bash
git switch shaira
```

Check the current branch:

```bash
git branch
```

Example:

```text
  main
* ashik
```

The `*` indicates the currently active branch.

---

# 9. Create a Python Virtual Environment

Each teammate must create their **own virtual environment**.

Never copy `.venv` from another computer.

---

## Windows

Create:

```powershell
python -m venv .venv
```

Activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

After activation, the terminal should look similar to:

```text
(.venv) PS ...\HSC_BioVQA_Dataset>
```

---

## macOS / Linux

Create:

```bash
python3 -m venv .venv
```

Activate:

```bash
source .venv/bin/activate
```

The terminal should now show something similar to:

```text
(.venv)
```

---

# 10. Upgrade pip

After activating the virtual environment:

```bash
python -m pip install --upgrade pip
```

---

# 11. Install Project Dependencies

Run:

```bash
pip install -r requirements.txt
```

Important packages currently used by the project include:

```text
faster-whisper
av
ctranslate2
google-genai
python-dotenv
static-ffmpeg
pytest
```

A particularly important dependency is:

```text
av==18.1.0
```

because newer incompatible PyAV versions may cause issues with Faster-Whisper.

---

# 12. Verify Important Packages

Run:

```bash
python -c "import faster_whisper; print('faster-whisper OK')"
```

Run:

```bash
python -c "import av; print('PyAV version:', av.__version__)"
```

Run:

```bash
python -c "import ctranslate2; print('CTranslate2 version:', ctranslate2.__version__)"
```

Run:

```bash
python -c "from google import genai; print('Google GenAI OK')"
```

Run:

```bash
python -c "import static_ffmpeg; print('static-ffmpeg OK')"
```

All commands should complete without import errors.

---

# 13. Configure Environment Variables

The actual `.env` file is intentionally not stored in GitHub because it contains private API credentials.

The repository includes:

```text
.env.example
```

Create your own `.env`.

---

## Windows

```powershell
Copy-Item ".env.example" ".env"
```

---

## macOS / Linux

```bash
cp .env.example .env
```

Open `.env` in VS Code and configure:

```env
GEMINI_API_KEY=YOUR_OWN_GEMINI_API_KEY
GEMINI_MODEL=gemini-3.5-flash-lite
```

Each teammate should use their **own Gemini API key/project**.

Do not share or commit API keys.

---

# 14. Confirm `.env` Is Ignored

Run:

```bash
git check-ignore -v .env
```

Git should report that `.env` is ignored.

Also verify:

```bash
git status
```

`.env` should not appear as an untracked file.

---

# 15. Important Repository Structure

The main project structure is:

```text
HSC_BioVQA_Dataset/
│
├── curriculum_mapping_agent/
│
├── video_segmentation_agent/
│
├── question_video_matching/
│
├── shared/
│   ├── taxonomy/
│   ├── schemas/
│   └── config/
│
├── data/
│   ├── questions/
│   │   ├── incoming/
│   │   ├── master/
│   │   ├── backups/
│   │   └── exports/
│   │
│   ├── videos/
│   │   ├── incoming/
│   │   ├── manifests/
│   │   └── processed/
│   │
│   ├── segments/
│   │   └── master/
│   │
│   ├── mappings/
│   │
│   └── final_dataset/
│       └── master/
│
├── reports/
├── scripts/
├── requirements.txt
├── README.md
└── .env.example
```

---

# 16. Master Taxonomy

The project uses one shared taxonomy:

```text
shared/taxonomy/hsc_biology_master_taxonomy_v1.0.json
```

The taxonomy is shared across:

```text
Curriculum Mapping Agent
Video Segmentation Agent
Question-Video Matching Agent
```

Agents must **not automatically create new taxonomy nodes**.

If a required concept is missing, it should be flagged for manual review.

---

# 17. Prepare the Faster-Whisper Model

The Video Segmentation Agent currently uses:

```text
Whisper large-v3
```

Recommended configuration:

```text
model = large-v3
device = cpu
compute_type = int8
language = bn
```

The first run downloads a large model.

To download/cache it before processing a video:

---

## Windows

```powershell
python -c "from faster_whisper import WhisperModel; print('Downloading/loading large-v3...'); m=WhisperModel('large-v3', device='cpu', compute_type='int8'); print('large-v3 is ready and cached.')"
```

---

## macOS / Linux

```bash
python -c 'from faster_whisper import WhisperModel; print("Downloading/loading large-v3..."); m=WhisperModel("large-v3", device="cpu", compute_type="int8"); print("large-v3 is ready and cached.")'
```

Expected:

```text
large-v3 is ready and cached.
```

A Hugging Face `HF_TOKEN` warning may appear.

That warning is normally harmless for public model downloads.

---

# 18. Raw Videos Are Not Included in Git

Raw videos are intentionally ignored by Git.

Therefore cloning the repository will **not automatically download the lecture videos**.

Each teammate who needs to run video processing must manually place the required video inside:

```text
data/videos/incoming/
```

Example:

```text
data/videos/incoming/
└── BNBD_cell_division_p01_T01_0001_20260601.mp4
```

Do not commit raw `.mp4` files unless the team explicitly decides otherwise.

---

# 19. Question Input Files

Raw question batches go into:

```text
data/questions/incoming/
```

Example:

```text
barishal_2025_raw_input_batch_01.json
```

The raw question input should contain original HSC question content.

Do not paraphrase the original board questions.

---

# 20. Run the Curriculum Mapping Agent

First check the CLI:

```bash
python -m curriculum_mapping_agent.src.main --help
```

The current CLI accepts:

```text
--input INPUT
--config CONFIG
```

Example:

```bash
python -m curriculum_mapping_agent.src.main --input "data/questions/incoming/barishal_2025_raw_input_batch_01.json"
```

The agent maps each question through:

```text
Paper
  ↓
Chapter
  ↓
Topic
  ↓
Subtopic
  ↓
Concept
```

The canonical question registry is:

```text
data/questions/master/question.json
```

---

# 21. Curriculum Mapping Output

Each mapped question contains information such as:

```text
paper_id
chapter_id
topic_id
subtopic_id
primary_concept_id
secondary_concept_ids
confidence
review_status
```

Possible review statuses may include:

```text
auto_accepted
human_review_required
```

Questions marked:

```text
human_review_required
```

should be inspected manually.

---

# 22. Run Curriculum Mapping Tests

Run:

```bash
python -m pytest curriculum_mapping_agent/tests -q
```

If that directory contains the current test suite, all tests should pass before merging code into `main`.

---

# 23. Video Segmentation Pipeline

The current video pipeline is:

```text
Raw Video
   ↓
Metadata Validation
   ↓
Audio Extraction
   ↓
Faster-Whisper Bangla ASR
   ↓
Timestamped Transcript
   ↓
Microchunk Generation
   ↓
Curriculum Tagging
   ↓
Boundary Detection
   ↓
Segment Merging
   ↓
Final Video Segments
```

---

# 24. Check the Video Agent CLI

Before running a video, check the current command-line interface:

```bash
python -m video_segmentation_agent.src.main --help
```

Use the arguments shown by the repository's current CLI.

This avoids using outdated commands after code changes.

---

# 25. Video Processing Outputs

For each video, the agent creates a workspace similar to:

```text
data/videos/processed/<video_id>/
```

It may contain:

```text
audio/
transcript/
microchunks/
curriculum_tags/
segments/
metadata/
```

Important lightweight outputs include:

```text
transcript.json
microchunks.json
chunk_tags.json
segments.json
```

---

# 26. ASR Behavior

The current ASR setup uses:

```text
Faster-Whisper large-v3
Bangla
CPU
int8
```

Transcription can take significant time on CPU.

For an approximately 11-minute test lecture, processing has previously taken much longer than real-time.

Therefore:

- Do not interrupt ASR unnecessarily.
- Keep the computer plugged in.
- Avoid running heavy CPU workloads simultaneously.

---

# 27. Do Not Use `--force` When Resuming

If the Video Segmentation Agent already has:

```text
transcript.json
microchunks.json
```

do not force regeneration unless required.

The pipeline is designed to reuse existing intermediate files where possible.

Using a force option may cause expensive ASR work to run again.

---

# 28. Curriculum Tagging Checkpoints

Video curriculum tagging saves progress incrementally.

A file such as:

```text
chunk_tags.json
```

may be updated as microchunks are successfully mapped.

Therefore an interrupted Gemini tagging stage can often resume without repeating everything.

---

# 29. Final Segment Registry

Final video segments are stored in:

```text
data/segments/master/segments.json
```

Each segment contains information such as:

```text
segment_id
video_id
start_sec
end_sec
transcript
curriculum_mapping
```

---

# 30. Validate Segment Quality

Before running the Question-Video Matching Agent, inspect:

```text
data/segments/master/segments.json
```

Confirm that:

- paper mapping is correct
- chapter mapping is correct
- topic mapping is reasonable
- subtopic mapping is reasonable
- concepts are correct
- timestamps are valid

Incorrect segment taxonomy will directly reduce matching quality.

---

# 31. Question-Video Matching Agent

The current matching agent is completely deterministic.

It does **not use Gemini or another LLM**.

Its main inputs are:

```text
data/questions/master/question.json
```

and:

```text
data/segments/master/segments.json
```

---

# 32. Matching Logic

Candidate eligibility:

```text
same paper
AND
same chapter
```

Then four scores are calculated:

```text
Topic Match
Subtopic Match
Concept Overlap
TF-IDF Text Similarity
```

Current weighted formula:

```text
final_score =
    0.20 × topic_match
  + 0.25 × subtopic_match
  + 0.35 × concept_overlap
  + 0.20 × semantic_similarity
```

Current minimum threshold:

```text
0.55
```

---

# 33. Test the Matching Agent

Run its tests:

```bash
python -m pytest question_video_matching/tests -q
```

The current non-LLM implementation should pass its test suite before normal execution.

---

# 34. Dry Run the Matching Agent

Use a dry run first:

```bash
python -m question_video_matching.src.main --dry-run
```

Example output:

```text
Matched HSCQ_000001 | candidates=3 | retained=0 | matched=0
Matched HSCQ_000006 | candidates=3 | retained=3 | matched=3

Questions: 6
Segments: 5
Pairs: 3
Matched pairs: 3
```

A dry run performs the matching computation without replacing the authoritative output.

---

# 35. Run the Matcher Normally

When the dry run looks correct:

```bash
python -m question_video_matching.src.main
```

The mapping output is stored in:

```text
data/mappings/question_video_mapping.json
```

---

# 36. Final Joined Dataset

The final joined dataset is stored in:

```text
data/final_dataset/master/hsc_biovqa.json
```

It combines information from:

```text
Question
+
Matched Video Segment
+
Timestamp
+
Transcript
+
Curriculum Mapping
+
Matching Score
```

---

# 37. Run General Tests

From the repository root:

```bash
python -m pytest -q
```

This is recommended before pushing major changes.

---

# 38. Python Compilation Check

A quick syntax check can be performed with:

```bash
python -m compileall curriculum_mapping_agent
python -m compileall video_segmentation_agent
python -m compileall question_video_matching
```

If no syntax errors are reported, compilation succeeded.

---

# 39. Recommended New-Device Smoke Test

After installation, run these commands:

```bash
python --version
```

```bash
git status
```

```bash
python -c "import faster_whisper; print('faster-whisper OK')"
```

```bash
python -c "import av; print('PyAV:', av.__version__)"
```

```bash
python -c "from google import genai; print('Gemini SDK OK')"
```

```bash
python -m curriculum_mapping_agent.src.main --help
```

```bash
python -m video_segmentation_agent.src.main --help
```

```bash
python -m question_video_matching.src.main --help
```

```bash
python -m pytest question_video_matching/tests -q
```

If these succeed, the basic project environment is ready.

---

# 40. Daily Git Workflow

Before starting work:

```bash
git fetch origin
git switch your-branch
git merge origin/main
git status
```

Example:

```bash
git fetch origin
git switch ashik
git merge origin/main
git status
```

---

# 41. After Making Changes

Check:

```bash
git status
```

Stage specific files:

```bash
git add path/to/file
```

Example:

```bash
git add curriculum_mapping_agent/src/candidate_retriever.py
```

Check staged changes:

```bash
git diff --staged
```

Commit:

```bash
git commit -m "Improve curriculum candidate retrieval"
```

Push:

```bash
git push
```

---

# 42. Pull Request Workflow

When your branch work is ready:

```text
your branch
     ↓
Pull Request
     ↓
main
```

On GitHub:

1. Open **Pull Requests**
2. Click **New Pull Request**
3. Select:

```text
base: main
compare: your-branch
```

4. Review the changes
5. Create the Pull Request
6. Merge when ready

---

# 43. Important Files That Should Not Be Shared Through Git

Do not commit:

```text
.env
.venv/
*.wav
*.mp3
*.mp4
*.npy
*.npz
__pycache__/
*.pyc
.pytest_cache/
desktop.ini
.DS_Store
```

These are intentionally ignored.

---

# 44. Important Files That Should Be Shared

The following should normally stay version-controlled:

```text
source code
taxonomy
schemas
configs
prompts
tests
requirements.txt
README files
question master JSON
segment master JSON
mapping JSON
final dataset JSON
lightweight processing JSON
```

---

# 45. Common Problem: `.env` Missing

This is expected after cloning.

`.env` is not stored in GitHub.

Create it manually from:

```text
.env.example
```

Then add your own API key.

---

# 46. Common Problem: Raw Video Missing

This is also expected.

Raw video files are not stored in GitHub.

Manually copy the required lecture video into:

```text
data/videos/incoming/
```

---

# 47. Common Problem: `ModuleNotFoundError`

Example:

```text
ModuleNotFoundError: No module named 'faster_whisper'
```

Usually means:

- `.venv` is not activated, or
- dependencies were not installed.

Activate the environment and run:

```bash
pip install -r requirements.txt
```

---

# 48. Common Problem: PowerShell Blocks Virtual Environment Activation

If Windows shows an execution policy error, run PowerShell with an appropriate execution policy for the current user/session, then activate:

```powershell
.\.venv\Scripts\Activate.ps1
```

Do not permanently weaken system security settings unnecessarily.

---

# 49. Common Problem: Gemini 429

A `429` normally indicates rate-limit or quota exhaustion.

Possible causes:

- too many API calls
- free-tier quota exhausted
- multiple teammates using the same API project

Recommended:

```text
Each teammate should use their own API key/project.
```

---

# 50. Common Problem: Gemini 503

A `503` typically means the model/API is temporarily unavailable or overloaded.

The project contains retry handling, but repeated `503` responses may still require trying again later or using the configured supported model.

Current project testing has successfully used:

```text
gemini-3.5-flash-lite
```

---

# 51. Common Problem: Faster-Whisper Model Download

If the first ASR run appears slow before transcription starts, the model may still be downloading.

Pre-download it using the command in the **Prepare Faster-Whisper Model** section.

---

# 52. Common Problem: PyAV Compatibility

If Faster-Whisper produces a PyAV-related error, check:

```bash
python -c "import av; print(av.__version__)"
```

The project currently expects:

```text
18.1.0
```

If required:

```bash
pip install av==18.1.0
```

---

# 53. Common Problem: Git Does Not Show New Branches

Run:

```bash
git fetch origin
```

Then:

```bash
git branch -a
```

---

# 54. Common Problem: Git Merge Conflict

If Git reports:

```text
CONFLICT
```

do not blindly delete files.

Run:

```bash
git status
```

Identify the conflicting files and resolve them carefully with the team.

Master JSON registries should be handled especially carefully.

---

# 55. Canonical Data Files

The main authoritative files are:

```text
data/questions/master/question.json
data/segments/master/segments.json
data/mappings/question_video_mapping.json
data/final_dataset/master/hsc_biovqa.json
```

These files should be treated carefully because downstream agents depend on them.

---

# 56. Recommended Responsibility Boundaries

| Component | Primary Owner |
|---|---|
| Curriculum Mapping Agent | Ashik |
| Question processing | Ashik |
| Video Segmentation Agent | Shaira |
| Video processing | Shaira |
| Question-Video Matching Agent | Fahad |
| Final dataset integration | Fahad |
| Shared taxonomy | Team |
| Schemas/configuration | Team |

---

# 57. Full Setup Checklist

Before running the complete project on a new machine, confirm:

- [ ] Git installed
- [ ] Python installed
- [ ] Repository cloned
- [ ] Correct branch selected
- [ ] `.venv` created
- [ ] `.venv` activated
- [ ] `requirements.txt` installed
- [ ] `.env` created
- [ ] Personal Gemini API key configured
- [ ] Faster-Whisper imports correctly
- [ ] PyAV version verified
- [ ] Google GenAI SDK imports correctly
- [ ] `large-v3` downloaded/cached
- [ ] Required raw video manually copied
- [ ] Question input files available
- [ ] Curriculum Mapping CLI works
- [ ] Video Segmentation CLI works
- [ ] Matching CLI works
- [ ] Tests pass

---

# 58. Full Pipeline Checklist

### Questions

```text
Raw HSC Questions
      ↓
Curriculum Mapping Agent
      ↓
question.json
```

Verify:

- [ ] question IDs correct
- [ ] taxonomy mapping correct
- [ ] review statuses checked

---

### Videos

```text
Raw Lecture Video
      ↓
ASR
      ↓
Transcript
      ↓
Microchunks
      ↓
Curriculum Tags
      ↓
Boundaries
      ↓
Final Segments
      ↓
segments.json
```

Verify:

- [ ] transcript generated
- [ ] microchunks generated
- [ ] curriculum mappings reasonable
- [ ] timestamps valid
- [ ] final segments generated

---

### Matching

```text
question.json
      +
segments.json
      ↓
Question-Video Matching
      ↓
question_video_mapping.json
      ↓
hsc_biovqa.json
```

Verify:

- [ ] dry run completed
- [ ] candidates look reasonable
- [ ] accepted matches look correct
- [ ] final mapping written
- [ ] final dataset generated

---

# 59. Recommended Run Order

For a completely new dataset run:

```text
1. Activate virtual environment
        ↓
2. Configure .env
        ↓
3. Prepare question input
        ↓
4. Run Curriculum Mapping Agent
        ↓
5. Verify question.json
        ↓
6. Add raw lecture video
        ↓
7. Run Video Segmentation Agent
        ↓
8. Verify segments.json
        ↓
9. Run Question-Video Matcher --dry-run
        ↓
10. Inspect matching results
        ↓
11. Run matcher normally
        ↓
12. Verify mapping JSON
        ↓
13. Verify final HSC BioVQA dataset
```

---

# 60. Quick Start — Windows

After cloning:

```powershell
cd HSC_BioVQA_Dataset

git fetch origin
git switch YOUR_BRANCH

python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -r requirements.txt

Copy-Item ".env.example" ".env"
```

Edit `.env`, then verify:

```powershell
python -c "import faster_whisper; print('faster-whisper OK')"
python -c "import av; print(av.__version__)"
python -c "from google import genai; print('Gemini SDK OK')"

python -m curriculum_mapping_agent.src.main --help
python -m video_segmentation_agent.src.main --help
python -m question_video_matching.src.main --help
```

---

# 61. Quick Start — macOS

After cloning:

```bash
cd HSC_BioVQA_Dataset

git fetch origin
git switch YOUR_BRANCH

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

cp .env.example .env
```

Edit `.env`, then verify:

```bash
python -c 'import faster_whisper; print("faster-whisper OK")'
python -c 'import av; print(av.__version__)'
python -c 'from google import genai; print("Gemini SDK OK")'

python -m curriculum_mapping_agent.src.main --help
python -m video_segmentation_agent.src.main --help
python -m question_video_matching.src.main --help
```

---

# 62. Team Rule

Before pushing important changes:

```bash
git status
git diff
git diff --staged
```

Before merging into `main`:

```text
Run tests
Check outputs
Review changed files
Create Pull Request
Merge only when stable
```

---

# 63. Project Information

**Project:** HSC BioVQA Dataset  
**Course:** CSE 499A  
**Faculty Advisor:** Dr. Sumaiya Tabassum Nimi [STI]

### Group Members

- Fahad Al Hasan
- Nazmul Huda
- Shaira Tahsin Areeba

---

# 64. Final Notes

The most important things for a teammate setting up this project are:

```text
Clone repository
     ↓
Switch to personal branch
     ↓
Create personal .venv
     ↓
Install requirements
     ↓
Create personal .env
     ↓
Use personal Gemini API key
     ↓
Download/cache Whisper large-v3
     ↓
Manually add raw video if required
     ↓
Run agent --help commands
     ↓
Run tests
     ↓
Start development
```

Never copy another member's `.venv` or `.env`.

Never commit API keys.

Always verify the active Git branch before making or pushing major changes.
