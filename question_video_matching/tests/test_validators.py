import pytest
from question_video_matching.src.validators import validate_inputs, validate_pairs


def test_duplicate_segment_id_rejected():
    q = [{"question_id": "Q1"}]
    s = [
        {"segment_id": "S1", "video_id": "V1"},
        {"segment_id": "S1", "video_id": "V1"},
    ]
    with pytest.raises(ValueError):
        validate_inputs(q, s)


def test_unknown_pair_reference_rejected():
    pairs = [{"pair_id": "P1", "question_id": "Q1", "segment_id": "S2", "scores": {"final": 0.8}}]
    with pytest.raises(ValueError):
        validate_pairs(pairs, {"Q1"}, {"S1"})
