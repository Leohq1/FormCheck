from pathlib import Path

import pytest
from formcheck_rag.chunking import chunk_document
from formcheck_rag.feedback import (
    FeedbackValidationError,
    TemplateFeedbackGenerator,
    validate_feedback,
)
from formcheck_rag.findings import AnalysisFindings
from formcheck_rag.manifest import load_manifest
from formcheck_rag.retrieval import InMemoryIndex

FIXTURES = Path(__file__).parent / "fixtures"


def _index() -> InMemoryIndex:
    index = InMemoryIndex()
    for source in load_manifest(FIXTURES / "sources.json"):
        text = (FIXTURES / source.text_file).read_text(encoding="utf-8")
        index.add(chunk_document(text, source, corpus_version="test-1"))
    return index


def _findings() -> AnalysisFindings:
    return AnalysisFindings.model_validate_json((FIXTURES / "findings.json").read_text(encoding="utf-8"))


def test_template_feedback_cites_only_retrieved_chunks_and_keeps_the_finding():
    findings = _findings()
    evidence = _index().search_findings(findings)
    feedback = TemplateFeedbackGenerator().generate(findings, evidence)

    validate_feedback(feedback, findings, evidence)
    assert feedback.model == "template-fallback"
    assert feedback.prompt_version == "1"
    assert len(feedback.tips) == 1
    tip = feedback.tips[0]
    assert findings.schema_version == "0-draft"
    assert tip.finding_id == "clear.low_arm_extension.v1"
    assert "moderate severity" in tip.explanation.lower()
    assert "0.81" in tip.explanation
    assert tip.citations[0].chunk_id in {chunk.chunk_id for chunk in evidence}
    assert "diagnos" not in feedback.summary.lower()
    assert any("racket" in item.lower() or "shuttle" in item.lower() for item in feedback.limitations)


def test_validator_rejects_an_invented_citation():
    findings = _findings()
    evidence = _index().search_findings(findings)
    feedback = TemplateFeedbackGenerator().generate(findings, evidence)
    feedback.tips[0].citations[0].chunk_id = "chunk-does-not-exist"

    with pytest.raises(FeedbackValidationError):
        validate_feedback(feedback, findings, evidence)


def test_validator_rejects_a_tip_for_a_finding_the_rules_did_not_supply():
    findings = _findings()
    evidence = _index().search_findings(findings)
    feedback = TemplateFeedbackGenerator().generate(findings, evidence)
    feedback.tips[0].finding_id = "clear.invented_fault.v1"

    with pytest.raises(FeedbackValidationError):
        validate_feedback(feedback, findings, evidence)


def test_user_facing_mode_does_not_cite_the_test_corpus():
    findings = _findings()
    evidence = _index().search_findings(findings)
    feedback = TemplateFeedbackGenerator().generate(findings, evidence, user_facing=True)

    assert feedback.tips == []
    assert any("no approved coaching passage" in item.lower() for item in feedback.limitations)


def test_missing_passages_do_not_invent_a_recommendation():
    findings = _findings()
    feedback = TemplateFeedbackGenerator().generate(findings, [])

    validate_feedback(feedback, findings, [])
    assert feedback.tips == []
    assert any("no approved coaching passage" in item.lower() for item in feedback.limitations)
