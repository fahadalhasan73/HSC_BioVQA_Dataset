# Curriculum Mapping Agent

Integrated version of the existing question mapper. It preserves the original HSC questions and maps them hierarchically to Paper → Chapter → Topic → Subtopic → Concept IDs.

Changes made during repository integration:

- canonical taxonomy moved to `../shared/taxonomy/`;
- question registry moved to `../data/questions/master/question.json`;
- Gemini client automatically loads the root `.env` and rate-limits requests;
- lexical retrieval now uses a Unicode-aware tokenizer (`regex` letters + combining marks + numbers), fixing the earlier Bangla `re \\w+` fragmentation problem;
- retrieval component values are retained in candidate traces.

Run from repository root:

```powershell
python -m curriculum_mapping_agent.src.main --input data/questions/incoming/<batch>.json
```
