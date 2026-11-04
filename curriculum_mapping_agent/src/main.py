import argparse
import copy
import json
import logging
import os
from pathlib import Path
from typing import Any

import yaml

from .candidate_retriever import CandidateRetriever
from .curriculum_mapper import CurriculumMapper
from .duplicate_detector import (
    build_existing_fingerprint_index,
    build_question_fingerprint,
)
from .llm_client import LLMClient
from .normalizer import build_question_context, normalize_question
from .question_loader import load_question_batch
from .question_store import QuestionStore, file_sha256, utc_now_iso
from .taxonomy_loader import TaxonomyIndex


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else PROJECT_ROOT / p


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def build_question_record(
    raw: dict[str, Any],
    normalized: dict[str, Any],
    question_id: str,
    batch_id: str,
    fingerprint: str,
    mapping: dict[str, Any],
    auto_accept_threshold: float,
    agent_version: str,
    model_name: str,
) -> dict[str, Any]:
    if mapping["status"] == "taxonomy_update_required":
        review_status = "taxonomy_update_required"
    elif mapping["confidence"] >= auto_accept_threshold:
        review_status = "auto_accepted"
    else:
        review_status = "human_review_required"

    now = utc_now_iso()

    record = {
        "question_id": question_id,
        "batch_id": batch_id,
        "question_original_bn": raw["question_original_bn"],
        "question_normalized_bn": normalized["question_normalized_bn"],
        "question_type": raw["question_type"],
        "options": copy.deepcopy(raw.get("options", {})),
        "source": copy.deepcopy(raw.get("source", {})),
        "curriculum_mapping": {
            **mapping,
            "review_status": review_status,
            "agent_version": agent_version,
            "model": model_name,
        },
        "tracking": {
            "processing_status": "completed",
            "added_at": now,
            "last_modified": now,
        },
        "fingerprint": fingerprint,
    }

    if raw.get("stimulus_original_bn"):
        record["stimulus_original_bn"] = raw["stimulus_original_bn"]
        record["stimulus_normalized_bn"] = normalized[
            "stimulus_normalized_bn"
        ]

    return record


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Map raw HSC Biology questions to the master curriculum taxonomy."
    )
    parser.add_argument("--input", required=True, help="Path to raw question batch JSON.")
    parser.add_argument(
        "--config",
        default=str(PROJECT_ROOT / "config/agent_config.yaml"),
        help="Path to agent_config.yaml",
    )
    args = parser.parse_args()

    config = load_config(Path(args.config))
    setup_logging(resolve(config["paths"]["log_file"]))
    logger = logging.getLogger(__name__)

    input_path = Path(args.input).resolve()
    raw_questions = load_question_batch(input_path)
    input_fingerprint = file_sha256(input_path)

    taxonomy = TaxonomyIndex.from_file(
        resolve(config["paths"]["taxonomy_file"])
    )

    expected_version = config["taxonomy"].get("expected_content_version")
    if expected_version and taxonomy.content_version != expected_version:
        raise RuntimeError(
            f"Taxonomy version mismatch. Expected {expected_version!r}, "
            f"found {taxonomy.content_version!r}."
        )

    store = QuestionStore(
        path=resolve(config["paths"]["question_store"]),
        backup_dir=resolve(config["paths"]["backup_dir"]),
    )

    if config["storage"].get("backup_before_first_write_of_run", True):
        backup = store.make_backup()
        if backup:
            logger.info("Backup created: %s", backup)

    batch = store.start_or_resume_batch(
        input_file=str(input_path),
        input_fingerprint=input_fingerprint,
        submitted_count=len(raw_questions),
    )

    if batch["status"] == "completed":
        logger.info(
            "This exact input batch was already completed as %s. Nothing to do.",
            batch["batch_id"],
        )
        return

    llm = LLMClient.from_config(config["llm"])
    retriever = CandidateRetriever(taxonomy)
    mapper = CurriculumMapper(
        taxonomy=taxonomy,
        retriever=retriever,
        llm=llm,
        config=config,
        prompts_dir=resolve(config["paths"]["prompts_dir"]),
    )

    fingerprint_index = build_existing_fingerprint_index(store.questions)
    processed = set(batch.get("processed_indices", []))

    include_options = config["duplicate_detection"].get(
        "include_options_in_fingerprint", True
    )
    include_stimulus = config["duplicate_detection"].get(
        "include_stimulus_in_fingerprint", True
    )

    threshold = float(config["mapping"]["auto_accept_threshold"])
    agent_version = config["project"]["agent_version"]
    model_name = os.environ.get(config["llm"]["model_env"], "")

    for input_index, raw in enumerate(raw_questions):
        if input_index in processed:
            continue

        try:
            normalized = normalize_question(raw)
            fingerprint = build_question_fingerprint(
                raw,
                normalized,
                include_options=include_options,
                include_stimulus=include_stimulus,
            )

            existing_id = fingerprint_index.get(fingerprint)
            if existing_id:
                logger.info(
                    "Duplicate input index %s -> existing %s",
                    input_index,
                    existing_id,
                )
                store.record_duplicate(
                    batch,
                    input_index=input_index,
                    existing_question_id=existing_id,
                )
                store.checkpoint()
                continue

            context = build_question_context(raw, normalized)
            mapping = mapper.map_question(raw, context)

            question_id = store.allocate_question_id()
            record = build_question_record(
                raw=raw,
                normalized=normalized,
                question_id=question_id,
                batch_id=batch["batch_id"],
                fingerprint=fingerprint,
                mapping=mapping,
                auto_accept_threshold=threshold,
                agent_version=agent_version,
                model_name=model_name,
            )

            store.add_question(record)
            store.mark_input_index_processed(batch, input_index)
            fingerprint_index[fingerprint] = question_id

            logger.info(
                "Mapped %s | confidence=%.3f | review=%s",
                question_id,
                mapping["confidence"],
                record["curriculum_mapping"]["review_status"],
            )

            if config["storage"].get("save_after_each_question", True):
                store.checkpoint()

        except Exception as exc:
            logger.exception("Failed input index %s: %s", input_index, exc)
            store.record_error(batch, input_index, str(exc))
            store.checkpoint()

    # If every input index is processed, complete. Errors remain unprocessed and
    # can be retried by running the same input file again.
    if len(set(batch["processed_indices"])) == len(raw_questions):
        store.complete_batch(batch)
        logger.info(
            "Completed %s | submitted=%s | added=%s | duplicates=%s",
            batch["batch_id"],
            batch["submitted_count"],
            batch["added_count"],
            batch["duplicate_count"],
        )
    else:
        logger.warning(
            "Batch %s remains in processing state because %s item(s) failed. "
            "Run the same input again to retry.",
            batch["batch_id"],
            len(raw_questions) - len(set(batch["processed_indices"])),
        )


if __name__ == "__main__":
    main()
