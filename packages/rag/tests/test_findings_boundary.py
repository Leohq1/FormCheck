import json
from pathlib import Path

from formcheck_rag.chunking import chunk_document
from formcheck_rag.feedback import TemplateFeedbackGenerator, validate_feedback
from formcheck_rag.findings import AnalysisFindings
from formcheck_rag.manifest import load_manifest
from formcheck_rag.retrieval import InMemoryIndex

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> AnalysisFindings:
    return AnalysisFindings.model_validate_json((FIXTURES / name).read_text(encoding="utf-8"))


def _index() -> InMemoryIndex:
    index = InMemoryIndex()
    for source in load_manifest(FIXTURES / "sources.json"):
        text = (FIXTURES / source.text_file).read_text(encoding="utf-8")
        index.add(chunk_document(text, source, corpus_version="test-1"))
    return index


def _coach(name: str):
    findings = _load(name)
    evidence = _index().search_findings(findings)
    feedback = TemplateFeedbackGenerator().generate(findings, evidence)
    validate_feedback(feedback, findings, evidence)
    return findings, feedback


def test_empty_findings_do_not_invent_advice_from_a_measured_feature():
    findings, feedback = _coach("findings-empty.json")

    assert findings.findings == []
    assert findings.features[0].value == 160
    assert feedback.tips == []
    assert feedback.summary == "No supported technique fault was found for this overhead clear."
    assert "arm extension" not in feedback.summary.lower()


def test_would_trigger_and_raw_features_are_not_findings():
    payload = json.loads((FIXTURES / "findings-diagnostics.json").read_text(encoding="utf-8"))
    findings = AnalysisFindings.model_validate(payload)
    feedback = TemplateFeedbackGenerator().generate(findings, _index().search_findings(findings))

    assert not hasattr(findings, "diagnostics")
    assert feedback.tips == []
    assert "low arm extension" not in feedback.summary.lower()


def test_multiple_findings_cite_only_rules_with_a_retrieved_passage():
    _, feedback = _coach("findings-multiple.json")

    assert [tip.finding_id for tip in feedback.tips] == ["clear.low_arm_extension.v1"]
    assert any("limited trunk rotation" in item.lower() for item in feedback.limitations)


def test_low_confidence_finding_keeps_its_uncertainty():
    _, feedback = _coach("findings-low-confidence.json")

    assert feedback.tips[0].finding_id == "clear.low_arm_extension.v1"
    assert "low severity" in feedback.tips[0].explanation
    assert "0.42" in feedback.tips[0].explanation
    assert any("below 0.70 confidence" in item for item in feedback.limitations)


def test_inconclusive_quality_has_no_supported_finding():
    _, feedback = _coach("findings-inconclusive.json")

    assert feedback.tips == []
    assert feedback.summary == "This clip did not produce a supported technique finding."
    assert any("pose confidence" in item.lower() for item in feedback.limitations)


def test_uncertain_contact_does_not_claim_the_racket_was_tracked():
    _, feedback = _coach("findings-uncertain-contact.json")

    assert feedback.tips == []
    assert any("racket and shuttle were not tracked" in item for item in feedback.limitations)


def test_unsupported_view_does_not_describe_a_fault():
    _, feedback = _coach("findings-unsupported-view.json")

    assert feedback.tips == []
    assert feedback.summary == "This camera view did not support a technique finding."
    assert any("camera view" in item.lower() for item in feedback.limitations)
