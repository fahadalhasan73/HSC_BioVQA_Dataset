from question_video_matching.src.semantic_matcher import similarities


def test_similarity_order():
    sims = similarities(
        "মিয়োসিস কোষ বিভাজন",
        ["মিয়োসিসের পর্যায়", "সালোকসংশ্লেষণ"],
        {"analyzer": "char_wb", "ngram_min": 3, "ngram_max": 5},
    )
    assert sims[0] > sims[1]


def test_empty_question_returns_zeroes():
    assert similarities("", ["abc", "def"], {}) == [0.0, 0.0]
