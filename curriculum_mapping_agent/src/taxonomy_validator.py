from typing import Any

from .taxonomy_loader import TaxonomyIndex, TaxonomyError


class MappingValidationError(ValueError):
    pass


def _require_node_level(
    taxonomy: TaxonomyIndex,
    node_id: str,
    expected_level: str,
) -> dict[str, Any]:
    try:
        node = taxonomy.get(node_id)
    except TaxonomyError as exc:
        raise MappingValidationError(str(exc)) from exc

    if node.get("level") != expected_level:
        raise MappingValidationError(
            f"{node_id} has level {node.get('level')!r}; "
            f"expected {expected_level!r}."
        )
    return node


def validate_hierarchy(
    taxonomy: TaxonomyIndex,
    paper_id: str,
    chapter_id: str,
    topic_id: str,
    subtopic_id: str,
    primary_concept_id: str | None,
    secondary_concept_ids: list[str],
) -> None:
    paper = _require_node_level(taxonomy, paper_id, "paper")
    chapter = _require_node_level(taxonomy, chapter_id, "chapter")
    topic = _require_node_level(taxonomy, topic_id, "topic")
    subtopic = _require_node_level(taxonomy, subtopic_id, "subtopic")

    if chapter.get("parent_id") != paper["id"]:
        raise MappingValidationError(
            f"Chapter {chapter_id} is not a child of paper {paper_id}."
        )
    if topic.get("parent_id") != chapter["id"]:
        raise MappingValidationError(
            f"Topic {topic_id} is not a child of chapter {chapter_id}."
        )
    if subtopic.get("parent_id") != topic["id"]:
        raise MappingValidationError(
            f"Subtopic {subtopic_id} is not a child of topic {topic_id}."
        )

    concept_ids = []
    if primary_concept_id:
        concept_ids.append(primary_concept_id)
    concept_ids.extend(secondary_concept_ids)

    if len(concept_ids) != len(set(concept_ids)):
        raise MappingValidationError("Duplicate concept IDs in final mapping.")

    for concept_id in concept_ids:
        concept = _require_node_level(taxonomy, concept_id, "concept")
        if concept.get("parent_id") != subtopic["id"]:
            raise MappingValidationError(
                f"Concept {concept_id} is not a child of subtopic {subtopic_id}."
            )
