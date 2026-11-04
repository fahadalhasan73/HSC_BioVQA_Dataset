# HSC BioVQA Question-Video Matching Agent — Non-LLM v0.3.0

## Purpose

This agent deterministically links original mapped HSC Biology questions to curriculum-tagged lecture video segments.

It does **not**:

- rewrite or generate questions,
- call Gemini or any other LLM,
- use external embedding APIs,
- modify the taxonomy.

Inputs:

- `data/questions/master/question.json`
- `data/segments/master/segments.json`

Outputs:

- `data/mappings/question_video_mapping.json` — authoritative many-to-many mapping registry
- `data/final_dataset/master/hsc_biovqa.json` — joined export containing only accepted `matched` pairs

## Exact deterministic matching pipeline

1. Load questions and final video segments.
2. Reject mappings marked `low_information`, `taxonomy_update_required`, `failed`, `error`, or `unmapped`.
3. A candidate segment must have the **same paper and same chapter** as the question.
4. For every candidate, compute four scores:
   - `topic`: 1 for exact topic ID match, otherwise 0.
   - `subtopic`: 1 for exact subtopic ID match, otherwise 0.
   - `concept`: question concept coverage = `|question concepts ∩ segment concepts| / |question concepts|`.
   - `semantic`: cosine similarity from character-boundary TF-IDF (`char_wb`, n-grams 3–5) over original question text/stimulus and segment transcript.
5. Compute the exact final score:

   `final = 0.20*topic + 0.25*subtopic + 0.35*concept + 0.20*semantic`

   Weights are normalized by code if edited so the configured weights need only be positive.
6. Discard candidates with `final < 0.55`.
7. Sort deterministically by:
   1. final score descending,
   2. concept score descending,
   3. subtopic score descending,
   4. topic score descending,
   5. semantic score descending,
   6. earlier segment start time,
   7. segment ID lexicographically.
8. Keep at most 8 retained candidates for audit; the first 3 are marked `matched`, later retained candidates are `ranked_candidate`.
9. Checkpoint after every processed question so an interrupted run can resume.
10. Export only `matched` pairs into `hsc_biovqa.json`.

Paper and chapter are hard filters, so they are not redundantly weighted in the final score.

## Text used for semantic similarity

By default:

- textual stimulus/context is included when present,
- the original question stem is included,
- answer options are **not** included, because distractor options can artificially increase similarity with unrelated segments,
- the segment transcript is used as the comparison text.

No paraphrasing or correction is performed by this agent.

## Run

From the repository root:

```bash
python -m question_video_matching.src.main
```

Useful options:

```bash
python -m question_video_matching.src.main --help
python -m question_video_matching.src.main --dry-run
python -m question_video_matching.src.main --question-id HSCQ_000001 --dry-run
python -m question_video_matching.src.main --force
```

`--force` ignores a compatible checkpoint and recomputes. A checkpoint is reusable only when the question store, segment store, and matching configuration fingerprints are unchanged.

## Recommended first real test

```bash
python -m question_video_matching.src.main --dry-run
```

After reviewing the real matches, run without `--dry-run` to write the authoritative mapping store and final joined dataset.
