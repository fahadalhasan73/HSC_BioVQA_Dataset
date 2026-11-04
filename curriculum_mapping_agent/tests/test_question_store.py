import json

from curriculum_mapping_agent.src.question_store import QuestionStore


def test_question_store_creates_and_allocates_ids(tmp_path):
    path = tmp_path / "question.json"
    backups = tmp_path / "backups"

    store = QuestionStore(path, backups)
    assert store.allocate_question_id() == "HSCQ_000001"
    assert store.allocate_question_id() == "HSCQ_000002"
