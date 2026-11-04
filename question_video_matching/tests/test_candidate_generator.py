from question_video_matching.src.candidate_generator import generate_candidates


def test_same_chapter_filter():
    q = {"curriculum_mapping": {"status": "mapped", "paper_id": "P", "chapter_id": "C1"}}
    seg = [
        {"segment_id": "S1", "curriculum_mapping": {"status": "mapped", "paper_id": "P", "chapter_id": "C1"}},
        {"segment_id": "S2", "curriculum_mapping": {"status": "mapped", "paper_id": "P", "chapter_id": "C2"}},
    ]
    assert [x["segment_id"] for x in generate_candidates(q, seg, {"require_same_paper": True, "require_same_chapter": True})] == ["S1"]


def test_mapping_without_status_is_usable_if_ids_exist():
    q = {"curriculum_mapping": {"paper_id": "P", "chapter_id": "C1"}}
    seg = [{"segment_id": "S1", "curriculum_mapping": {"paper_id": "P", "chapter_id": "C1"}}]
    assert len(generate_candidates(q, seg, {})) == 1


def test_low_information_segment_is_rejected():
    q = {"curriculum_mapping": {"status": "mapped", "paper_id": "P", "chapter_id": "C1"}}
    seg = [{"segment_id": "S1", "curriculum_mapping": {"status": "low_information", "paper_id": "P", "chapter_id": "C1"}}]
    assert generate_candidates(q, seg, {}) == []
