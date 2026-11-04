# Changes — v0.3.0 Non-LLM

- Removed `src/evidence_validator.py` completely.
- Removed the LLM evidence prompt directory.
- Removed Gemini/API-key/model configuration.
- Removed `--no-evidence`; the agent is always non-LLM.
- Removed evidence-validation fields from mapping pairs.
- Made same-paper and same-chapter exact matches hard candidate filters.
- Removed chapter from the weighted score because it is already a mandatory filter.
- Defined the exact score as topic 0.20 + subtopic 0.25 + concept 0.35 + TF-IDF semantic 0.20.
- Added deterministic tie-breaking rules.
- Preserved stable pair IDs, checkpoint/resume, source/config fingerprints, atomic writes, backups, validation, and joined export.
- Added algorithm metadata to output JSON for reproducibility.
