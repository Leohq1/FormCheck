import os

import pytest
from formcheck_rag.feedback import TemplateFeedbackGenerator
from formcheck_rag.findings import AnalysisFindings
from formcheck_rag.gemini import (
    GeminiConfig,
    GeminiFeedbackGenerator,
    gemini_config_from_env,
    parse_gemini_json,
)
from test_feedback import _findings, _index


class _Scripted:
    def __init__(self, responses: list[object]) -> None:
        self.responses = list(responses)
        self.calls = 0

    def complete(self, *, model: str, prompt: str, timeout_seconds: float) -> dict[str, object]:
        del model, prompt, timeout_seconds
        self.calls += 1
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        assert isinstance(response, dict)
        return response


def test_missing_config_uses_the_template_without_a_transport() -> None:
    findings = _findings()
    evidence = _index().search_findings(findings)
    feedback = GeminiFeedbackGenerator(None, transport=None).generate(findings, evidence)

    assert feedback.model == "template-fallback"
    assert feedback.tips


def test_invalid_model_output_falls_back_after_retries() -> None:
    findings = _findings()
    evidence = _index().search_findings(findings)
    transport = _Scripted([TimeoutError("slow"), {"summary": "you have low arm extension"}])
    feedback = GeminiFeedbackGenerator(
        GeminiConfig(api_key="test-key", model="gemini-test", max_attempts=2),
        transport=transport,
    ).generate(findings, evidence)

    assert transport.calls == 2
    assert feedback.model == "template-fallback"
    assert "you have low arm extension" not in feedback.summary.lower()


def test_valid_model_output_is_kept_when_citations_match(monkeypatch: pytest.MonkeyPatch) -> None:
    del monkeypatch
    findings = _findings()
    evidence = _index().search_findings(findings)
    expected = TemplateFeedbackGenerator().generate(findings, evidence)
    transport = _Scripted([expected.model_dump()])
    feedback = GeminiFeedbackGenerator(
        GeminiConfig(api_key="test-key", model="gemini-test", max_attempts=1),
        transport=transport,
    ).generate(findings, evidence)

    assert feedback.tips[0].finding_id == expected.tips[0].finding_id
    assert transport.calls == 1


def test_string_limitations_are_accepted() -> None:
    findings = _findings()
    evidence = _index().search_findings(findings)
    expected = TemplateFeedbackGenerator().generate(findings, evidence)
    payload = expected.model_dump()
    payload["limitations"] = "Contact time was estimated."
    feedback = GeminiFeedbackGenerator(
        GeminiConfig(api_key="test-key", model="gemini-test", max_attempts=1),
        transport=_Scripted([payload]),
    ).generate(findings, evidence)

    assert feedback.limitations == ["Contact time was estimated."]
    assert feedback.model == "gemini-test"


def test_parse_gemini_json_strips_a_markdown_fence() -> None:
    payload = parse_gemini_json('```json\n{"summary": "Reach up."}\n```')
    assert payload == {"summary": "Reach up."}


def test_env_config_requires_key_and_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    assert gemini_config_from_env() is None
    monkeypatch.setenv("GEMINI_API_KEY", "secret")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.5-flash")
    config = gemini_config_from_env()
    assert config is not None
    assert config.model == "gemini-2.5-flash"


@pytest.mark.integration
def test_live_gemini_is_skipped_without_a_key() -> None:
    if not os.environ.get("GEMINI_API_KEY") or not os.environ.get("GEMINI_MODEL"):
        pytest.skip("GEMINI_API_KEY is not set")
    assert isinstance(_findings(), AnalysisFindings)
