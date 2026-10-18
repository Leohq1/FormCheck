from formcheck_rag.findings import AnalysisFindings
from formcheck_rag.generator import HostedFeedbackGenerator


def test_hosted_generator_uses_the_template_without_an_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    findings = AnalysisFindings.model_validate(
        {
            "analysis_id": "abc",
            "stroke": {"type": "overhead_clear"},
            "findings": [],
        }
    )

    feedback = HostedFeedbackGenerator().generate(findings, [])

    assert feedback.model == "template-fallback"
    assert feedback.tips == []
