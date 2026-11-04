import json
from collections import defaultdict
from pathlib import Path
from typing import Any


class TaxonomyError(ValueError):
    pass


class TaxonomyIndex:
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        self.content_version = payload.get("taxonomy_content_version")
        self.schema_version = payload.get("taxonomy_schema_version")

        nodes = payload.get("nodes")
        if not isinstance(nodes, list):
            raise TaxonomyError("Taxonomy JSON must contain a 'nodes' list.")

        self.nodes: list[dict[str, Any]] = nodes
        self.by_id: dict[str, dict[str, Any]] = {}
        self.children: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
        self.by_level: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for node in self.nodes:
            node_id = node.get("id")
            if not node_id:
                raise TaxonomyError("Every taxonomy node must have an id.")
            if node_id in self.by_id:
                raise TaxonomyError(f"Duplicate taxonomy id: {node_id}")
            self.by_id[node_id] = node
            self.children[node.get("parent_id")].append(node)
            self.by_level[node.get("level", "")].append(node)

        for group in self.children.values():
            group.sort(key=lambda n: n["id"])

    @classmethod
    def from_file(cls, path: str | Path) -> "TaxonomyIndex":
        with Path(path).open("r", encoding="utf-8") as f:
            return cls(json.load(f))

    def get(self, node_id: str) -> dict[str, Any]:
        try:
            return self.by_id[node_id]
        except KeyError:
            raise TaxonomyError(f"Unknown taxonomy id: {node_id}") from None

    def child_nodes(
        self,
        parent_id: str,
        *,
        level: str | None = None,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        result = list(self.children.get(parent_id, []))
        if level is not None:
            result = [n for n in result if n.get("level") == level]
        if active_only:
            result = [n for n in result if n.get("status", "active") == "active"]
        return result

    def nodes_at_level(
        self,
        level: str,
        *,
        active_only: bool = True,
    ) -> list[dict[str, Any]]:
        result = list(self.by_level.get(level, []))
        if active_only:
            result = [n for n in result if n.get("status", "active") == "active"]
        return result

    def ancestors(self, node_id: str) -> list[dict[str, Any]]:
        chain: list[dict[str, Any]] = []
        current = self.get(node_id)
        while current.get("parent_id"):
            current = self.get(current["parent_id"])
            chain.append(current)
        return chain

    def descendants(self, node_id: str) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        stack = list(self.children.get(node_id, []))
        while stack:
            node = stack.pop()
            output.append(node)
            stack.extend(self.children.get(node["id"], []))
        return output

    def path_labels(self, node_id: str) -> str:
        node = self.get(node_id)
        chain = list(reversed(self.ancestors(node_id))) + [node]
        labels = []
        for n in chain:
            label = n.get("label_bn") or n.get("label_en") or n["id"]
            labels.append(label)
        return " > ".join(labels)

    def candidate_document(self, node_id: str) -> str:
        """
        Search text for a candidate. Including descendant labels helps broad
        chapter/topic retrieval even when the question does not literally use
        the chapter name.
        """
        node = self.get(node_id)
        texts: list[str] = [
            str(node.get("label_bn", "")),
            str(node.get("label_en", "")),
        ]

        for key in ("aliases_bn", "aliases_en"):
            values = node.get(key) or []
            if isinstance(values, list):
                texts.extend(str(v) for v in values)

        # Include descendant labels only for non-concept nodes.
        if node.get("level") != "concept":
            for child in self.descendants(node_id):
                texts.append(str(child.get("label_bn", "")))
                texts.append(str(child.get("label_en", "")))

        return " ".join(t for t in texts if t).strip()
