from pathlib import Path

from curriculum_mapping_agent.src.taxonomy_loader import TaxonomyIndex


def test_taxonomy_loads():
    root = Path(__file__).resolve().parents[1]
    taxonomy = TaxonomyIndex.from_file(
        root.parent / "shared/taxonomy/hsc_biology_master_taxonomy_v1.0.json"
    )
    assert taxonomy.get("HSC_BIO_P1")["level"] == "paper"
    chapters = taxonomy.child_nodes("HSC_BIO_P1", level="chapter")
    assert len(chapters) == 12
