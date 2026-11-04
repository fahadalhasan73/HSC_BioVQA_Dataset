# HSC BioVQA — Git Collaboration Guide

This document explains how our team should use the GitHub repository, branches, commits, pushes, and pull requests while working on the **HSC BioVQA Dataset** project.

---

## Repository

**GitHub Repository**

```text
https://github.com/fahadalhasan73/HSC_BioVQA_Dataset
```

---

# 1. Branch Structure

We currently use the following branches:

```text
main
├── fahad
├── ashik
└── shaira
```

### Branch purposes

| Branch | Purpose |
|---|---|
| `main` | Stable and integrated version of the project |
| `fahad` | Fahad's working branch |
| `ashik` | Ashik's working branch |
| `shaira` | Shaira's working branch |

Each member should primarily work on their own branch.

Changes should be merged into `main` using a **Pull Request** after the work is ready.

---


# 3. First-Time Repository Setup

Clone the repository:

```bash
git clone https://github.com/fahadalhasan73/HSC_BioVQA_Dataset.git
```

Enter the repository:

```bash
cd HSC_BioVQA_Dataset
```

Fetch all branches:

```bash
git fetch origin
```

Check available branches:

```bash
git branch -a
```

Expected remote branches:

```text
origin/main
origin/fahad
origin/ashik
origin/shaira
```

---

# 4. Switch to Your Branch

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

If the branch already exists locally, simply use:

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

# 5. Python Environment Setup

Each member must create their **own virtual environment**.

Do not copy another member's `.venv` directory.

## Windows

Create the environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

---

## macOS / Linux

Create the environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 6. Environment Variables

Each member must create their own:

```text
.env
```

Use your own API key.

Example:

```env
GEMINI_API_KEY=YOUR_API_KEY
GEMINI_MODEL=gemini-3.5-flash-lite
```

Never commit or push `.env`.

The repository contains:

```text
.env.example
```

which can be used as a template.

---

# 7. Files That Must Not Be Committed

The `.gitignore` file prevents unnecessary or sensitive files from being uploaded.

Examples include:

```text
.env
.venv/
__pycache__/
*.pyc
*.wav
*.mp3
*.mp4
*.npy
*.npz
*.log
desktop.ini
.DS_Store
```

Never upload:

- API keys
- `.env`
- virtual environments
- raw videos
- generated audio
- Python cache files
- temporary files
- personal IDE files

---

# 8. Normal Daily Workflow

Before starting work, check your current branch:

```bash
git branch
```

Then fetch the latest information from GitHub:

```bash
git fetch origin
```

Check the repository status:

```bash
git status
```

---

# 9. Making Code Changes

Edit the required files normally in VS Code.

After making changes, check:

```bash
git status
```

Example:

```text
modified:
    curriculum_mapping_agent/src/candidate_retriever.py
```

---

# 10. Stage Specific Files

If you only want to commit one specific file:

```bash
git add path/to/file
```

Example:

```bash
git add curriculum_mapping_agent/src/candidate_retriever.py
```

If multiple files should be committed:

```bash
git add file1 file2
```

If all current changes are intended:

```bash
git add .
```

Use `git add .` carefully.

Always check the status first:

```bash
git status
```

---

# 11. Check What Will Be Committed

Before creating a commit:

```bash
git diff --staged
```

This shows exactly what is currently staged.

---

# 12. Commit Changes

Create a clear commit message:

```bash
git commit -m "Improve curriculum candidate retrieval"
```

Other examples:

```bash
git commit -m "Fix video segmentation boundary logic"
```

```bash
git commit -m "Update deterministic question-video matcher"
```

```bash
git commit -m "Add new HSC Biology question batch"
```

Avoid unclear commit messages such as:

```text
update
changes
fix
new code
```

---

# 13. Push Changes to Your Branch

After committing:

```bash
git push
```

The changes will be pushed to your own branch.

For example:

```text
Fahad  → origin/fahad
Ashik  → origin/ashik
Shaira → origin/shaira
```

Your push does **not automatically update `main`**.

---

# 14. Pull Requests

When your work is complete and ready to be added to the main project, create a Pull Request on GitHub.

Example:

```text
ashik
  ↓
Pull Request
  ↓
main
```

or:

```text
shaira
  ↓
Pull Request
  ↓
main
```

or:

```text
fahad
  ↓
Pull Request
  ↓
main
```

### Pull Request workflow

1. Push your changes to your branch.
2. Open GitHub.
3. Go to **Pull Requests**.
4. Click **New Pull Request**.
5. Select:

```text
base: main
compare: your-branch
```

6. Review the changed files.
7. Add a clear title and description.
8. Create the Pull Request.
9. Review the changes.
10. Merge into `main` when ready.

---

# 15. Updating Your Branch from `main`

Changes made to `main` do **not automatically appear** in personal branches.

If `main` has received new updates, bring them into your branch manually.

Example for Ashik:

```bash
git fetch origin
git switch ashik
git merge origin/main
```

Example for Shaira:

```bash
git fetch origin
git switch shaira
git merge origin/main
```

Example for Fahad:

```bash
git fetch origin
git switch fahad
git merge origin/main
```

After merging successfully:

```bash
git push
```

---

# 16. Recommended Workflow Before Starting New Work

Use this sequence:

```bash
git fetch origin
git switch your-branch
git merge origin/main
git status
```

Then start editing.

For example:

```bash
git fetch origin
git switch ashik
git merge origin/main
git status
```

---

# 17. Recommended Workflow After Finishing Work

Use:

```bash
git status
git add <files>
git diff --staged
git commit -m "Describe the change"
git push
```

Then create a Pull Request if the changes should be added to `main`.

---

# 18. Important Master Files

Some files can easily cause merge conflicts because multiple agents may update them.

Examples:

```text
data/questions/master/question.json
data/segments/master/segments.json
data/mappings/question_video_mapping.json
data/final_dataset/master/hsc_biovqa.json
```

Recommended ownership:

| File | Primary Responsibility |
|---|---|
| `question.json` | Curriculum Mapping / Question Processing |
| `segments.json` | Video Segmentation |
| `question_video_mapping.json` | Question-Video Matching |
| `hsc_biovqa.json` | Final Integration |

Avoid having multiple people edit the same master JSON file at the same time.

---

# 19. Merge Conflicts

A merge conflict may happen when two branches modify the same lines in the same file.

Git may show something like:

```text
CONFLICT (content): Merge conflict in some_file.py
```

If this happens:

**Do not randomly delete files or overwrite the repository.**

First check:

```bash
git status
```

Then discuss the conflict with the team and resolve it carefully.

---

# 20. Useful Git Commands

## Check current status

```bash
git status
```

---

## Check current branch

```bash
git branch
```

---

## Check all local and remote branches

```bash
git branch -a
```

---

## Download latest GitHub branch information

```bash
git fetch origin
```

---

## Switch branch

```bash
git switch branch-name
```

Example:

```bash
git switch fahad
```

---

## See unstaged changes

```bash
git diff
```

---

## See staged changes

```bash
git diff --staged
```

---

## Stage one file

```bash
git add path/to/file
```

---

## Stage all intended changes

```bash
git add .
```

---

## Commit

```bash
git commit -m "Commit message"
```

---

## Push

```bash
git push
```

---

## See recent commits

```bash
git log --oneline
```

---

## Pull latest changes for the current tracking branch

```bash
git pull
```

---

# 21. Team Rules

Please follow these basic rules:

1. Work mainly on your own branch.
2. Avoid directly pushing to `main` unless necessary.
3. Use Pull Requests for important changes.
4. Run `git status` before committing.
5. Do not commit `.env`.
6. Do not commit API keys.
7. Do not commit `.venv`.
8. Do not commit raw videos or large generated audio files.
9. Use meaningful commit messages.
10. Pull/fetch updates regularly.
11. Be careful when modifying shared files.
12. Do not resolve merge conflicts by blindly deleting files.
13. Make sure your code works before merging it into `main`.

---

# 22. Basic Collaboration Architecture

```text
                   GitHub Repository
                          │
                          │
                        main
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
        fahad           ashik           shaira
          │               │               │
          │               │               │
       Develop         Develop         Develop
          │               │               │
          ▼               ▼               ▼
        Commit          Commit          Commit
          │               │               │
          ▼               ▼               ▼
         Push            Push            Push
          │               │               │
          └───────────────┼───────────────┘
                          │
                          ▼
                    Pull Requests
                          │
                          ▼
                        Review
                          │
                          ▼
                     Merge to main
```

---

# 23. Quick Reference

### Start work

```bash
git fetch origin
git switch your-branch
git merge origin/main
git status
```

### Finish work

```bash
git status
git add <files>
git diff --staged
git commit -m "Describe your changes"
git push
```

### Then

```text
Open Pull Request
        ↓
Review
        ↓
Merge into main
```

---

# HSC BioVQA Team

**Project:** HSC BioVQA Dataset  
**Course:** CSE 499  
**Faculty Advisor:** Dr. Sumaiya Tabassum Nimi [STI]

### Group Members

- Fahad Al Hasan
- Nazmul Huda
- Shaira Tahsin Areeba
