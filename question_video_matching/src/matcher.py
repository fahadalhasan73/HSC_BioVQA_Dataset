import argparse
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from .candidate_generator import generate_candidates
from .data_loader import load_questions, load_segments
from .dataset_exporter import build_joined_view
from .mapping_store import atomic_write_json, save_mapping_store
from .scoring import score_pair
from .semantic_matcher import similarities
from .text_utils import question_text, segment_text
from .validators import validate_inputs, validate_pairs


AGENT_ROOT = Path(__file__).resolve().parents[1]
ALGORITHM_VERSION = "deterministic_taxonomy_tfidf_v1"


def resolve(path_value):
    path = Path(path_value)
    return path if path.is_absolute() else (AGENT_ROOT / path).resolve()


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def config_fingerprint(cfg: Dict[str, Any]) -> str:
    relevant = {
        "candidates": cfg.get("candidates", {}),
        "scoring": cfg.get("scoring", {}),
        "semantic": cfg.get("semantic", {}),
        "selection": cfg.get("selection", {}),
    }
    raw = json.dumps(relevant, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def source_fingerprint(question_store, segment_store, cfg):
    return {
        "question_store_sha256": sha256_file(question_store),
        "segment_store_sha256": sha256_file(segment_store),
        "config_sha256": config_fingerprint(cfg),
    }


def stable_pair_id(question_id: str, segment_id: str) -> str:
    digest = hashlib.sha1(f"{question_id}|{segment_id}".encode("utf-8")).hexdigest()[:12].upper()
    return f"PAIR_{digest}"


def _load_existing_payload(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        with p.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def _algorithm_metadata(cfg: Dict[str, Any]) -> Dict[str, Any]:
    weights = cfg.get("scoring", {}).get("weights", {})
    return {
        "name": ALGORITHM_VERSION,
        "llm_used": False,
        "candidate_filter": {
            "same_paper_required": bool(cfg.get("candidates", {}).get("require_same_paper", True)),
            "same_chapter_required": bool(cfg.get("candidates", {}).get("require_same_chapter", True)),
        },
        "score_formula": (
            "normalized(w_topic)*topic_exact + normalized(w_subtopic)*subtopic_exact + "
            "normalized(w_concept)*concept_overlap + normalized(w_semantic)*tfidf_cosine"
        ),
        "weights": {k: float(v) for k, v in weights.items()},
        "concept_overlap_method": cfg.get("scoring", {}).get("concept_overlap_method", "question_coverage"),
        "semantic": cfg.get("semantic", {}),
        "minimum_candidate_score": float(cfg.get("scoring", {}).get("minimum_candidate_score", 0.55)),
        "max_matches_per_question": int(cfg.get("selection", {}).get("max_matches_per_question", 3)),
    }


def _build_payload(cfg, fingerprint, pairs, completed_question_ids, all_questions, segments, question_summaries):
    return {
        "dataset": {
            "name": "HSC BioVQA Question-Video Mapping",
            "schema_version": "1.2",
            "agent_version": str(cfg.get("project", {}).get("version", "0.3.0-non-llm")),
            "updated_at": utc_now_iso(),
            "total_questions": len(all_questions),
            "total_segments": len(segments),
            "total_pairs": len(pairs),
            "total_matched_pairs": sum(1 for p in pairs if p.get("status") == "matched"),
        },
        "algorithm": _algorithm_metadata(cfg),
        "source_fingerprint": fingerprint,
        "completed_question_ids": sorted(set(completed_question_ids)),
        "question_summaries": sorted(question_summaries.values(), key=lambda x: x.get("question_id", "")),
        "pairs": pairs,
    }


def _start_time(segment: Dict[str, Any]) -> float:
    value = segment.get("start_sec", segment.get("start_time_sec", 0.0))
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _sort_key(item: Tuple[float, Dict[str, Any], Dict[str, float], Dict[str, Any]]):
    """Stable deterministic tie-breaking after the final score."""
    total, segment, parts, _ = item
    return (
        -float(total),
        -float(parts.get("concept", 0.0)),
        -float(parts.get("subtopic", 0.0)),
        -float(parts.get("topic", 0.0)),
        -float(parts.get("semantic", 0.0)),
        _start_time(segment),
        str(segment.get("segment_id", "")),
    )


def main():
    parser = argparse.ArgumentParser(
        description="Deterministically match mapped HSC Biology questions to curriculum-tagged video segments."
    )
    parser.add_argument("--config", default=str(AGENT_ROOT / "config" / "matching_config.yaml"))
    parser.add_argument("--question-store", default=None)
    parser.add_argument("--segment-store", default=None)
    parser.add_argument("--mapping-store", default=None)
    parser.add_argument("--question-id", action="append", default=[], help="Process only this question ID; repeatable.")
    parser.add_argument("--force", action="store_true", help="Ignore matching checkpoint and recompute selected questions.")
    parser.add_argument("--dry-run", action="store_true", help="Compute matches without writing stores.")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    question_store = Path(args.question_store) if args.question_store else resolve(cfg["paths"]["question_store"])
    segment_store = Path(args.segment_store) if args.segment_store else resolve(cfg["paths"]["segment_store"])
    mapping_store = Path(args.mapping_store) if args.mapping_store else resolve(cfg["paths"]["mapping_store"])

    log_path = resolve(cfg["paths"]["log_file"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)

    all_questions = load_questions(question_store)
    segments = load_segments(segment_store)
    all_question_ids, segment_ids = validate_inputs(all_questions, segments)
    questions = list(all_questions)

    if args.question_id:
        wanted = set(args.question_id)
        questions = [q for q in questions if q.get("question_id") in wanted]
        missing = wanted - {q.get("question_id") for q in questions}
        if missing:
            logger.warning("Requested question IDs not found: %s", ", ".join(sorted(missing)))

    fingerprint = source_fingerprint(question_store, segment_store, cfg)
    resume_enabled = bool(cfg.get("resume", {}).get("enabled", True)) and not args.force
    existing = _load_existing_payload(mapping_store) if resume_enabled else None
    compatible_existing = bool(existing and existing.get("source_fingerprint") == fingerprint)

    pairs: List[Dict[str, Any]] = []
    completed_question_ids = set()
    question_summaries: Dict[str, Dict[str, Any]] = {}

    if args.question_id and not args.dry_run and not compatible_existing:
        raise RuntimeError(
            "Safe targeted write refused: --question-id can update the authoritative mapping store only "
            "when a compatible mapping checkpoint already exists. Use --dry-run for a first targeted test, "
            "or run the full matcher once."
        )

    if compatible_existing:
        pairs = [p for p in existing.get("pairs", []) if isinstance(p, dict)]
        completed_question_ids = set(existing.get("completed_question_ids", []))
        question_summaries = {
            x.get("question_id"): x
            for x in existing.get("question_summaries", [])
            if isinstance(x, dict) and x.get("question_id")
        }
        if args.question_id:
            selected = set(args.question_id)
            completed_question_ids -= selected
            logger.info("Loaded compatible mapping store and will recompute selected questions: %s", ", ".join(sorted(selected)))
        else:
            logger.info("Resuming matching checkpoint: %s completed questions", len(completed_question_ids))
    elif existing:
        logger.info("Existing mapping store fingerprint differs; recomputing against current sources/config.")

    min_score = float(cfg.get("scoring", {}).get("minimum_candidate_score", 0.55))
    top_k = int(cfg.get("candidates", {}).get("top_k_per_question", 8))
    max_matches = int(cfg.get("selection", {}).get("max_matches_per_question", 3))

    for q_index, question in enumerate(questions, start=1):
        qid = question.get("question_id")
        if not qid:
            logger.warning("Skipping question without question_id at index %s", q_index)
            continue
        if qid in completed_question_ids:
            logger.info("Skipping completed question %s", qid)
            continue

        # Replace previous pairs for this question when explicitly recomputing it.
        pairs = [p for p in pairs if p.get("question_id") != qid]

        candidates = generate_candidates(question, segments, cfg.get("candidates", {}))
        qtext = question_text(
            question,
            include_options=bool(cfg.get("semantic", {}).get("include_options_in_question_text", False)),
        )
        sem_scores = similarities(
            qtext,
            [segment_text(s) for s in candidates],
            cfg.get("semantic", {}),
        )

        question_mapping = question.get("curriculum_mapping") or {}
        scored = []
        for segment, semantic_score in zip(candidates, sem_scores):
            segment_mapping = segment.get("curriculum_mapping") or {}
            total, parts, concept_evidence = score_pair(
                question_mapping,
                segment_mapping,
                semantic_score,
                cfg.get("scoring", {}),
            )
            scored.append((total, segment, parts, concept_evidence))

        scored.sort(key=_sort_key)
        retained = [item for item in scored if item[0] >= min_score][:top_k]

        matched_count = 0
        for rank, (total, segment, parts, concept_evidence) in enumerate(retained, start=1):
            status = "matched" if matched_count < max_matches else "ranked_candidate"
            if status == "matched":
                matched_count += 1

            start_sec = segment.get("start_sec", segment.get("start_time_sec"))
            end_sec = segment.get("end_sec", segment.get("end_time_sec"))

            match_basis = []
            if concept_evidence.get("shared_concept_ids"):
                match_basis.append("concept")
            if parts.get("subtopic"):
                match_basis.append("subtopic")
            if parts.get("topic"):
                match_basis.append("topic")
            if parts.get("semantic", 0.0) >= 0.50:
                match_basis.append("semantic")

            pair = {
                "pair_id": stable_pair_id(qid, segment.get("segment_id", "")),
                "question_id": qid,
                "video_id": segment.get("video_id"),
                "segment_id": segment.get("segment_id"),
                "rank": rank,
                "evidence_span": {"start_sec": start_sec, "end_sec": end_sec},
                "match_basis": match_basis,
                "taxonomy_match": {
                    "paper": True,
                    "chapter": True,
                    "topic": bool(parts["topic"]),
                    "subtopic": bool(parts["subtopic"]),
                    **concept_evidence,
                },
                "scores": {
                    **{k: round(float(v), 6) for k, v in parts.items()},
                    "final": round(float(total), 6),
                },
                "status": status,
            }
            pairs.append(pair)

        completed_question_ids.add(qid)
        question_summaries[qid] = {
            "question_id": qid,
            "candidate_segments": len(candidates),
            "retained_candidates": len(retained),
            "matched_pairs": matched_count,
            "status": "matched" if matched_count else ("no_candidate_above_threshold" if candidates else "no_taxonomy_candidate"),
        }
        logger.info(
            "Matched %s | candidates=%s | retained=%s | matched=%s",
            qid,
            len(candidates),
            len(retained),
            matched_count,
        )

        if cfg.get("resume", {}).get("checkpoint_after_each_question", True) and not args.dry_run:
            checkpoint = _build_payload(
                cfg, fingerprint, pairs, completed_question_ids, all_questions, segments, question_summaries
            )
            atomic_write_json(mapping_store, checkpoint)

    payload = _build_payload(cfg, fingerprint, pairs, completed_question_ids, all_questions, segments, question_summaries)

    if not args.dry_run:
        save_mapping_store(
            mapping_store,
            resolve(cfg["paths"]["backup_dir"]),
            payload,
            create_backup=True,
        )

        validate_pairs(pairs, all_question_ids, segment_ids)
        joined = build_joined_view(all_questions, segments, pairs, accepted_statuses=("matched",))
        final_path = resolve(cfg["paths"].get("final_dataset_store", "../data/final_dataset/master/hsc_biovqa.json"))
        atomic_write_json(
            final_path,
            {
                "dataset": {
                    "name": "HSC BioVQA Joined Question-Video Dataset",
                    "schema_version": "1.1",
                    "agent_version": str(cfg.get("project", {}).get("version", "0.3.0-non-llm")),
                    "algorithm": ALGORITHM_VERSION,
                    "llm_used": False,
                    "generated_at": utc_now_iso(),
                    "total_records": len(joined),
                },
                "records": joined,
            },
        )

    validate_pairs(pairs, all_question_ids, segment_ids)

    print(
        f"Questions: {len(questions)} | Segments: {len(segments)} | "
        f"Pairs: {len(pairs)} | Matched pairs: {sum(1 for p in pairs if p.get('status') == 'matched')}"
    )


if __name__ == "__main__":
    main()
