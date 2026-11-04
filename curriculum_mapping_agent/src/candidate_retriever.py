from difflib import SequenceMatcher
from typing import Any
import regex

from .normalizer import normalize_text
from .taxonomy_loader import TaxonomyIndex

# Unicode letters + combining marks + numbers. Unlike Python re \w+, this
# preserves Bengali words containing vowel signs/other combining marks.
_TOKEN_RE = regex.compile(r"[\p{L}\p{M}\p{N}_]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(normalize_text(text).lower()))


def score_components(query: str, document: str) -> dict[str, float]:
    q = normalize_text(query).lower()
    d = normalize_text(document).lower()
    if not q or not d:
        return {'token_overlap':0.0,'sequence_similarity':0.0,'substring_boost':0.0,'retrieval_score':0.0}

    q_tokens = _tokens(q)
    d_tokens = _tokens(d)
    overlap = len(q_tokens & d_tokens) / len(q_tokens) if q_tokens else 0.0
    sequence = SequenceMatcher(None, q, d).ratio()
    hits = sum(1.0 for token in q_tokens if len(token) >= 4 and token in d)
    substring_boost = min(hits / max(len(q_tokens), 1), 1.0)
    score = 0.50 * overlap + 0.35 * sequence + 0.15 * substring_boost
    return {
        'token_overlap': round(overlap, 6),
        'sequence_similarity': round(sequence, 6),
        'substring_boost': round(substring_boost, 6),
        'retrieval_score': round(score, 6),
    }


def _score(query: str, document: str) -> float:
    return score_components(query, document)['retrieval_score']


class CandidateRetriever:
    def __init__(self, taxonomy: TaxonomyIndex): self.taxonomy = taxonomy

    def rank(self, query: str, candidates: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        scored = []
        for node in candidates:
            parts = score_components(query, self.taxonomy.candidate_document(node['id']))
            scored.append({**node, '_retrieval_score': parts['retrieval_score'], '_retrieval_components': parts})
        scored.sort(key=lambda x: x['_retrieval_score'], reverse=True)
        return scored if len(scored) <= top_k else scored[:top_k]

#Testing Ashik's branch    
