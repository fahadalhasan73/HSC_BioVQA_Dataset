from typing import Dict, List


def similarities(question_text: str, segment_texts: List[str], cfg: Dict) -> List[float]:
    if not segment_texts:
        return []
    if not (question_text or "").strip():
        return [0.0] * len(segment_texts)

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    texts = [question_text, *[(x or "") for x in segment_texts]]
    if not any(x.strip() for x in texts):
        return [0.0] * len(segment_texts)

    try:
        vectorizer = TfidfVectorizer(
            analyzer=cfg.get("analyzer", "char_wb"),
            ngram_range=(int(cfg.get("ngram_min", 3)), int(cfg.get("ngram_max", 5))),
            lowercase=bool(cfg.get("lowercase", True)),
        )
        matrix = vectorizer.fit_transform(texts)
        sims = cosine_similarity(matrix[0:1], matrix[1:]).ravel()
        return [float(max(0.0, min(1.0, x))) for x in sims]
    except ValueError:
        # e.g. empty vocabulary
        return [0.0] * len(segment_texts)
