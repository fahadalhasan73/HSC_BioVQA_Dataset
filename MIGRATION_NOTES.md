# Migration Notes

The uploaded `curriculum_mapping_agent_reference.zip` was migrated into the integrated repository rather than discarded.

Preserved:
- original prompts and mapping logic;
- existing Barishal 2025 raw input batches;
- existing master `question.json` with current mapped records and batch state;
- existing backups;
- original ZIP in `archive/`.

Integrated improvements:
- one shared canonical taxonomy;
- shared root data registries;
- automatic `.env` loading;
- Gemini request pacing/retry support;
- Unicode-aware Bengali lexical tokenization (`regex` Unicode Letter/Mark/Number classes), replacing the earlier `re \\w+` limitation;
- complete video segmentation baseline and question-video matching components.
