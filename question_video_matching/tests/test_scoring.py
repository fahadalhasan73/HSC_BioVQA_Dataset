import pytest

from question_video_matching.src.scoring import concept_overlap, score_pair


def cfg():
    return {
        "weights": {"topic": 0.20, "subtopic": 0.25, "concept": 0.35, "semantic": 0.20},
        "concept_overlap_method": "question_coverage",
    }


def test_exact_formula():
    q = {"topic_id": "T", "subtopic_id": "ST", "primary_concept_id": "C1", "secondary_concept_ids": ["C2"]}
    s = {"topic_id": "T", "subtopic_id": "ST", "primary_concept_id": "C1"}
    total, parts, evidence = score_pair(q, s, 0.50, cfg())

    # topic=1, subtopic=1, concept=1/2, semantic=.5
    expected = 0.20 * 1 + 0.25 * 1 + 0.35 * 0.5 + 0.20 * 0.5
    assert total == pytest.approx(expected)
    assert parts["concept"] == pytest.approx(0.5)
    assert evidence["shared_concept_ids"] == ["C1"]


def test_matching_concept_scores_higher():
    q = {"topic_id": "T", "subtopic_id": "S", "primary_concept_id": "X"}
    same = {"topic_id": "T", "subtopic_id": "S", "primary_concept_id": "X"}
    diff = {"topic_id": "T", "subtopic_id": "S", "primary_concept_id": "Y"}
    a, _, _ = score_pair(q, same, 0.2, cfg())
    b, _, _ = score_pair(q, diff, 0.2, cfg())
    assert a > b


def test_question_coverage():
    assert concept_overlap({"A", "B"}, {"B", "C"}) == pytest.approx(0.5)
