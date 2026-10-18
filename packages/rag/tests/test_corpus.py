from pathlib import Path

from formcheck_rag.corpus import load_index, metadata_sql
from formcheck_rag.manifest import load_manifest
from formcheck_rag.retrieval import RetrievalQuery

ROOT = Path(__file__).resolve().parents[3]
MANIFEST = ROOT / "corpus" / "manifests" / "sources.json"
EXCLUDED = ROOT / "corpus" / "manifests" / "excluded.json"


def _arm_query() -> RetrievalQuery:
    return RetrievalQuery(
        stroke="overhead_clear",
        finding="clear.low_arm_extension.v1",
        phase="maximum_reach",
        severity="moderate",
        fault_tags=["contact_reach", "arm_extension"],
        evidence_summary="dominant elbow angle at maximum wrist height was 128 deg",
    )


def test_approved_sources_are_cc_by_sa_and_present():
    sources = load_manifest(MANIFEST)
    assert sources
    for source in sources:
        assert source.license == "CC BY-SA 4.0"
        assert source.review_status == "approved"
        assert source.source_version == "en-1"
        assert source.audience == "school physical education"
        assert source.skill_level == "beginner"
        assert source.body_region_tags
        assert source.page_locator.startswith("p")
        assert source.text_file
        text = (MANIFEST.parent / source.text_file).read_text(encoding="utf-8")
        assert "CC BY-SA 4.0" in text
        assert "http" in text


def test_metadata_sql_carries_the_new_fields():
    sql = metadata_sql(MANIFEST)
    assert "source_version" in sql
    assert "body_region_tags" in sql
    assert "school physical education" in sql
    assert "p. 3" in sql
    assert "local-bow-1536" in sql


def test_excluded_sources_have_no_text_and_are_not_indexed():
    excluded = load_manifest(EXCLUDED)
    assert excluded
    assert all(source.review_status == "rejected" for source in excluded)
    assert all(source.text_file is None for source in excluded)
    index = load_index(EXCLUDED)
    assert index.search(_arm_query()) == []


def test_low_arm_extension_retrieves_extended_arm_clear_and_not_smash():
    hits = load_index(MANIFEST).search(_arm_query())

    assert 1 <= len(hits) <= 6
    blob = " ".join(hit.text.lower() for hit in hits)
    assert "fully extended" in blob or "nearly extended" in blob
    assert "above the head" in blob or "highest point" in blob
    assert all("overhead_clear" in hit.stroke_tags for hit in hits)
    assert all("attacking shot" not in hit.text.lower() for hit in hits)
    assert all(hit.source_id.startswith("knsu-") for hit in hits)
    assert all(hit.source_version == "en-1" for hit in hits)
    assert all(hit.page_locator.startswith("p") for hit in hits)
    assert all("dominant_arm" in hit.body_region_tags for hit in hits)
    assert all(hit.audience == "school physical education" for hit in hits)
    assert all(hit.skill_level == "beginner" for hit in hits)
    assert all("high serve" not in hit.text.lower() for hit in hits)
