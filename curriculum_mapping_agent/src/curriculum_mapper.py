import json
from pathlib import Path
from typing import Any

from .candidate_retriever import CandidateRetriever
from .llm_client import LLMClient
from .taxonomy_loader import TaxonomyIndex
from .taxonomy_validator import validate_hierarchy


class CurriculumMapper:
    def __init__(
        self,
        taxonomy: TaxonomyIndex,
        retriever: CandidateRetriever,
        llm: LLMClient,
        config: dict[str, Any],
        prompts_dir: str | Path,
    ):
        self.taxonomy = taxonomy
        self.retriever = retriever
        self.llm = llm
        self.config = config
        self.prompts_dir = Path(prompts_dir)
        self.top_k = config["retrieval"]["top_k"]
        self.max_secondary = int(
            config["mapping"].get("max_secondary_concepts", 3)
        )

    def _load_prompt(self, filename: str) -> str:
        return (self.prompts_dir / filename).read_text(encoding="utf-8")

    def _candidate_payload(
        self,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        output = []
        for node in candidates:
            output.append(
                {
                    "id": node["id"],
                    "label_bn": node.get("label_bn"),
                    "label_en": node.get("label_en"),
                    "path": self.taxonomy.path_labels(node["id"]),
                    "retrieval_score": node.get("_retrieval_score", 0.0),
                    "retrieval_components": node.get("_retrieval_components", {}),
                }
            )
        return output

    def _select_single(
        self,
        stage: str,
        question_context: str,
        candidates: list[dict[str, Any]],
    ) -> tuple[str, float, list[dict[str, Any]]]:
        if not candidates:
            raise ValueError(f"No candidates available for stage: {stage}")

        ranked = self.retriever.rank(
            query=question_context,
            candidates=candidates,
            top_k=int(self.top_k[stage]),
        )

        prompt_template = self._load_prompt(f"{stage}_classifier.txt")
        prompt = prompt_template.format(
            question_context=question_context,
            candidates_json=json.dumps(
                self._candidate_payload(ranked),
                ensure_ascii=False,
                indent=2,
            ),
        )

        result = self.llm.classify_json(prompt)
        selected_id = result.get("selected_id")
        confidence = float(result.get("confidence", 0.0))

        allowed_ids = {n["id"] for n in ranked}
        if selected_id not in allowed_ids:
            raise ValueError(
                f"LLM selected invalid {stage} id: {selected_id}. "
                f"Allowed: {sorted(allowed_ids)}"
            )

        confidence = max(0.0, min(confidence, 1.0))
        return selected_id, confidence, ranked

    def _select_concepts(
        self,
        question_context: str,
        candidates: list[dict[str, Any]],
    ) -> tuple[str, str | None, list[str], float, list[dict[str, Any]]]:
        if not candidates:
            return "taxonomy_update_required", None, [], 0.0, []

        ranked = self.retriever.rank(
            query=question_context,
            candidates=candidates,
            top_k=int(self.top_k["concept"]),
        )

        prompt_template = self._load_prompt("concept_classifier.txt")
        prompt = prompt_template.format(
            question_context=question_context,
            max_secondary_concepts=self.max_secondary,
            candidates_json=json.dumps(
                self._candidate_payload(ranked),
                ensure_ascii=False,
                indent=2,
            ),
        )

        result = self.llm.classify_json(prompt)
        status = result.get("status", "mapped")
        confidence = max(0.0, min(float(result.get("confidence", 0.0)), 1.0))

        allowed = {n["id"] for n in ranked}

        if status == "taxonomy_update_required":
            return status, None, [], confidence, ranked

        primary = result.get("primary_concept_id")
        secondaries = result.get("secondary_concept_ids") or []

        if primary not in allowed:
            raise ValueError(f"Invalid primary concept id returned: {primary}")

        if not isinstance(secondaries, list):
            raise ValueError("secondary_concept_ids must be a list.")

        secondaries = [str(x) for x in secondaries if x]
        if len(secondaries) > self.max_secondary:
            secondaries = secondaries[: self.max_secondary]

        invalid = [x for x in secondaries if x not in allowed]
        if invalid:
            raise ValueError(f"Invalid secondary concept id(s): {invalid}")

        secondaries = [x for x in secondaries if x != primary]
        secondaries = list(dict.fromkeys(secondaries))

        return "mapped", primary, secondaries, confidence, ranked

    def _infer_paper_id(self, raw_question: dict[str, Any]) -> str:
        source = raw_question.get("source") or {}
        paper_text = str(source.get("paper", "")).lower()

        if "1st" in paper_text or "first" in paper_text or "প্রথম" in paper_text:
            return "HSC_BIO_P1"
        if "2nd" in paper_text or "second" in paper_text or "দ্বিত" in paper_text:
            return "HSC_BIO_P2"

        active_papers = self.config["taxonomy"].get("active_paper_ids", [])
        if len(active_papers) == 1:
            return active_papers[0]

        raise ValueError(
            "Could not infer paper. Provide source.paper or configure exactly "
            "one active_paper_id."
        )

    def map_question(
        self,
        raw_question: dict[str, Any],
        question_context: str,
    ) -> dict[str, Any]:
        paper_id = self._infer_paper_id(raw_question)
        paper = self.taxonomy.get(paper_id)
        if paper.get("status", "active") != "active":
            raise ValueError(f"Paper is not active in taxonomy: {paper_id}")

        chapter_candidates = self.taxonomy.child_nodes(
            paper_id, level="chapter", active_only=True
        )
        chapter_id, chapter_conf, chapter_ranked = self._select_single(
            "chapter", question_context, chapter_candidates
        )

        topic_candidates = self.taxonomy.child_nodes(
            chapter_id, level="topic", active_only=True
        )
        topic_id, topic_conf, topic_ranked = self._select_single(
            "topic", question_context, topic_candidates
        )

        subtopic_candidates = self.taxonomy.child_nodes(
            topic_id, level="subtopic", active_only=True
        )
        subtopic_id, subtopic_conf, subtopic_ranked = self._select_single(
            "subtopic", question_context, subtopic_candidates
        )

        concept_candidates = self.taxonomy.child_nodes(
            subtopic_id, level="concept", active_only=True
        )
        (
            concept_status,
            primary_concept_id,
            secondary_concept_ids,
            concept_conf,
            concept_ranked,
        ) = self._select_concepts(question_context, concept_candidates)

        if concept_status == "mapped":
            validate_hierarchy(
                taxonomy=self.taxonomy,
                paper_id=paper_id,
                chapter_id=chapter_id,
                topic_id=topic_id,
                subtopic_id=subtopic_id,
                primary_concept_id=primary_concept_id,
                secondary_concept_ids=secondary_concept_ids,
            )

        stage_confidences = {
            "chapter": chapter_conf,
            "topic": topic_conf,
            "subtopic": subtopic_conf,
            "concept": concept_conf,
        }
        final_confidence = min(stage_confidences.values())

        return {
            "status": concept_status,
            "taxonomy_version": self.taxonomy.content_version,
            "paper_id": paper_id,
            "chapter_id": chapter_id,
            "topic_id": topic_id,
            "subtopic_id": subtopic_id,
            "primary_concept_id": primary_concept_id,
            "secondary_concept_ids": secondary_concept_ids,
            "stage_confidences": stage_confidences,
            "confidence": round(final_confidence, 4),
            "confidence_method": self.config["mapping"].get(
                "confidence_method",
                "minimum_stage_llm_confidence_v0.1",
            ),
            "retrieval_method": self.config.get("retrieval", {}).get("method", "unicode_lexical_v0.2"),
            "candidate_trace": {
                "chapter": self._candidate_payload(chapter_ranked),
                "topic": self._candidate_payload(topic_ranked),
                "subtopic": self._candidate_payload(subtopic_ranked),
                "concept": self._candidate_payload(concept_ranked),
            },
        }
