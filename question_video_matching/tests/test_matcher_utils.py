from question_video_matching.src.matcher import stable_pair_id


def test_pair_id_is_stable():
    assert stable_pair_id("Q1", "S1") == stable_pair_id("Q1", "S1")
    assert stable_pair_id("Q1", "S1") != stable_pair_id("Q1", "S2")
