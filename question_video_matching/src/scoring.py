from typing import Any, Dict, Set, Tuple


SIGNALS = ("topic", "subtopic", "concept", "semantic")


def concept_ids(mapping: Dict[str, Any]) -> Set[str]:
    """Collect all concept IDs carried by a curriculum mapping."""
    ids: Set[str] = set()

    primary = mapping.get("primary_concept_id")
    if primary:
        ids.add(str(primary))

    for key in ("secondary_concept_ids", "concept_ids"):
        values = mapping.get(key) or []
        if isinstance(values, (list, tuple, set)):
            ids.update(str(x) for x in values if x)

    return ids


def concept_overlap(q_ids: Set[str], s_ids: Set[str], method: str = "question_coverage") -> float:
    """
    Deterministic concept overlap.

    question_coverage (default): |Q ∩ S| / |Q|
    jaccard:                    |Q ∩ S| / |Q ∪ S|
    """
    if not q_ids or not s_ids:
        return 0.0

    intersection = len(q_ids & s_ids)

    if method == "jaccard":
        return intersection / max(1, len(q_ids | s_ids))

    if method != "question_coverage":
        raise ValueError(f"Unsupported concept_overlap_method: {method}")

    return intersection / max(1, len(q_ids))


def _validated_weights(cfg: Dict[str, Any]) -> Dict[str, float]:
    configured = cfg.get("weights") or {}
    weights = {signal: float(configured.get(signal, 0.0)) for signal in SIGNALS}

    if any(value < 0 for value in weights.values()):
        raise ValueError("Matching score weights cannot be negative.")

    total = sum(weights.values())
    if total <= 0:
        raise ValueError("Matching score weights must sum to a positive value.")

    # Normalize even if a human edits YAML to weights that do not sum exactly to 1.
    return {key: value / total for key, value in weights.items()}


def score_pair(
    question_mapping: Dict[str, Any],
    segment_mapping: Dict[str, Any],
    semantic_score: float,
    cfg: Dict[str, Any],
) -> Tuple[float, Dict[str, float], Dict[str, Any]]:
    """
    Exact deterministic scoring formula.

    Candidate eligibility (same paper/chapter) is handled before this function.
    Therefore paper/chapter are not scored again.

    final = w_topic * topic_exact
          + w_subtopic * subtopic_exact
          + w_concept * concept_coverage
          + w_semantic * semantic_cosine

    Missing taxonomy IDs score 0 for that signal. There is no LLM, randomness,
    hidden calibration, or model-dependent post-processing.
    """
    weights = _validated_weights(cfg)
    method = str(cfg.get("concept_overlap_method", "question_coverage"))

    q_topic = question_mapping.get("topic_id")
    q_subtopic = question_mapping.get("subtopic_id")

    parts = {
        "topic": float(bool(q_topic) and q_topic == segment_mapping.get("topic_id")),
        "subtopic": float(bool(q_subtopic) and q_subtopic == segment_mapping.get("subtopic_id")),
        "concept": 0.0,
        "semantic": float(max(0.0, min(1.0, semantic_score))),
    }

    q_concepts = concept_ids(question_mapping)
    s_concepts = concept_ids(segment_mapping)
    parts["concept"] = concept_overlap(q_concepts, s_concepts, method)

    total = sum(weights[signal] * parts[signal] for signal in SIGNALS)

    evidence = {
        "question_concept_ids": sorted(q_concepts),
        "segment_concept_ids": sorted(s_concepts),
        "shared_concept_ids": sorted(q_concepts & s_concepts),
        "concept_overlap_method": method,
    }

    return float(max(0.0, min(1.0, total))), parts, evidence
