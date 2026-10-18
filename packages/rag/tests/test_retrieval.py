from pathlib import Path

from formcheck_rag.chunking import chunk_document
from formcheck_rag.findings import AnalysisFindings
from formcheck_rag.manifest import load_manifest
from formcheck_rag.retrieval import InMemoryIndex, RetrievalQuery

FIXTURES = Path(__file__).parent / "fixtures"


def _index() -> InMemoryIndex:
    index = InMemoryIndex()
    for source in load_manifest(FIXTURES / "sources.json"):
        text = (FIXTURES / source.text_file).read_text(encoding="utf-8")
        index.add(chunk_document(text, source, corpus_version="test-1"))
    return index


def test_retrieval_returns_approved_overhead_clear_elbow_passages_only():
    hits = _index().search(
        RetrievalQuery(
            stroke="overhead_clear",
            finding="clear.low_arm_extension.v1",
            phase="maximum_reach",
            severity="moderate",
            fault_tags=["contact_reach", "arm_extension"],
            evidence_summary="Dominant elbow angle at maximum wrist height was 128 deg.",
        )
    )

    assert 1 <= len(hits) <= 6
    assert all(hit.review_status == "approved" for hit in hits)
    assert all("overhead_clear" in hit.stroke_tags for hit in hits)
    assert any("arm" in hit.text.lower() for hit in hits)
    assert all("pending source" not in hit.text.lower() for hit in hits)
    assert hits[0].source_id
    assert hits[0].chunk_id
    assert hits[0].locator
    assert hits[0].corpus_version == "test-1"
    assert hits[0].relevance_score > 0


def test_frontend_clear_id_and_contract_severity_still_retrieve():
    findings = AnalysisFindings.model_validate(
        {
            "analysis_id": "abc123",
            "stroke": {"type": "clear"},
            "findings": [
                {
                    "rule_id": "clear.low_arm_extension.v1",
                    "label": "Low arm extension at maximum reach",
                    "severity": "minor",
                    "confidence": 0.8,
                    "retrieval_tags": ["clear", "contact_reach", "arm_extension"],
                }
            ],
        }
    )

    hits = _index().search_findings(findings)

    assert hits
    assert all("overhead_clear" in hit.stroke_tags for hit in hits)


def test_retrieval_skips_a_different_stroke():
    hits = _index().search(
        RetrievalQuery(
            stroke="overhead_smash",
            finding="late_elbow_extension",
            fault_tags=["arm_extension"],
            evidence_summary="Dominant elbow angle at maximum wrist height was 128 deg.",
        )
    )

    assert hits == []
