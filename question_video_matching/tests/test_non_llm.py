from pathlib import Path


def test_no_llm_implementation_files_or_imports():
    root = Path(__file__).resolve().parents[1]
    assert not (root / "src" / "evidence_validator.py").exists()

    source = "\n".join(p.read_text(encoding="utf-8") for p in (root / "src").glob("*.py"))
    forbidden = ["google.genai", "from google import genai", "GEMINI_API_KEY", "GEMINI_MODEL", "EvidenceValidator"]
    for token in forbidden:
        assert token not in source
