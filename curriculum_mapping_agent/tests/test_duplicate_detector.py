from curriculum_mapping_agent.src.duplicate_detector import build_question_fingerprint
from curriculum_mapping_agent.src.normalizer import normalize_question


def test_same_question_same_fingerprint():
    q1 = {
        "question_original_bn": "কোনটিতে মিয়োসিস ঘটে?",
        "question_type": "MCQ",
        "options": {"A": "ক", "B": "খ", "C": "গ", "D": "ঘ"},
    }
    q2 = {
        "question_original_bn": "  কোনটিতে   মিয়োসিস ঘটে? ",
        "question_type": "MCQ",
        "options": {"A": "ক", "B": "খ", "C": "গ", "D": "ঘ"},
    }

    f1 = build_question_fingerprint(q1, normalize_question(q1))
    f2 = build_question_fingerprint(q2, normalize_question(q2))
    assert f1 == f2
