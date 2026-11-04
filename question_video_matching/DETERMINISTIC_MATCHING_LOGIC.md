# Deterministic Matching Logic

Algorithm ID: `deterministic_taxonomy_tfidf_v1`

## 1. Candidate eligibility

A question and segment are comparable only when both curriculum mappings are usable and, under the default configuration:

- `question.paper_id == segment.paper_id`
- `question.chapter_id == segment.chapter_id`

Mappings with status `low_information`, `taxonomy_update_required`, `failed`, `error`, or `unmapped` are excluded.

## 2. Signal definitions

Let Q be the question curriculum mapping and S the segment curriculum mapping.

### Topic

`topic = 1` iff Q has a topic ID and `Q.topic_id == S.topic_id`; otherwise `0`.

### Subtopic

`subtopic = 1` iff Q has a subtopic ID and `Q.subtopic_id == S.subtopic_id`; otherwise `0`.

### Concept

Question concepts are the union of:

- `primary_concept_id`
- `secondary_concept_ids`
- `concept_ids`

Segment concepts are collected the same way.

Default concept score:

`concept = |Q_concepts ∩ S_concepts| / |Q_concepts|`

If either concept set is empty, the concept score is `0`.

### Semantic

Text source:

- question textual stimulus/context + original question stem,
- segment transcript.

Default TF-IDF settings:

- analyzer: `char_wb`
- n-gram range: `(3,5)`
- lowercase: `true`
- cosine similarity clipped to `[0,1]`
- answer options excluded by default.

## 3. Final score

Default weights:

- topic = 0.20
- subtopic = 0.25
- concept = 0.35
- semantic = 0.20

`final = 0.20*topic + 0.25*subtopic + 0.35*concept + 0.20*semantic`

The implementation normalizes configured weights by their sum, so manual YAML edits remain deterministic even if the values do not sum exactly to 1.

## 4. Threshold and selection

- minimum score = `0.55`
- top retained candidates = `8`
- accepted matches per question = `3`

Candidates below 0.55 are not stored as mapping pairs.

## 5. Deterministic tie-breaking

Candidates with equal/near-equal final scores are ordered by:

1. final score descending
2. concept score descending
3. subtopic score descending
4. topic score descending
5. semantic score descending
6. segment start time ascending
7. segment ID ascending

There is no random seed because no randomized component is used.

## 6. Reproducibility

The mapping store records:

- algorithm ID,
- weights and semantic settings,
- source SHA-256 fingerprints,
- config SHA-256 fingerprint,
- stable pair IDs derived from `question_id|segment_id`.

Therefore the same inputs and config produce the same ranking and pair IDs.
