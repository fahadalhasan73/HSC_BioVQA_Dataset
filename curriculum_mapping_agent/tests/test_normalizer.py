from curriculum_mapping_agent.src.normalizer import normalize_text


def test_normalize_text():
    assert normalize_text("  কোষ   বিভাজন  ") == "কোষ বিভাজন"
