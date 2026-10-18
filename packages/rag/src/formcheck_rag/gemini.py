"""Hosted Gemini feedback. A missing key uses the deterministic template."""

from __future__ import annotations

import os
from typing import Protocol

from pydantic import BaseModel, Field

from formcheck_rag.chunking import Chunk
from formcheck_rag.feedback import (
    Feedback,
    FeedbackValidationError,
    TemplateFeedbackGenerator,
    validate_feedback,
)
from formcheck_rag.findings import AnalysisFindings

_FAULTY_PHRASE = "you have low arm extension"


class GeminiConfig(BaseModel):
    api_key: str
    model: str = Field(min_length=1)
    timeout_seconds: float = 20.0
    max_attempts: int = 3


class GeminiTransport(Protocol):
    def complete(self, *, model: str, prompt: str, timeout_seconds: float) -> dict[str, object]: ...


def gemini_config_from_env() -> GeminiConfig | None:
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    model = os.environ.get("GEMINI_MODEL", "").strip()
    if not api_key or not model:
        return None
    return GeminiConfig(api_key=api_key, model=model)


class GeminiFeedbackGenerator:
    def __init__(
        self,
        config: GeminiConfig | None,
        transport: GeminiTransport | None = None,
        template: TemplateFeedbackGenerator | None = None,
    ) -> None:
        self.config = config
        self.transport = transport
        self.template = template or TemplateFeedbackGenerator()

    def generate(self, findings: AnalysisFindings, evidence: list[Chunk]) -> Feedback:
        if self.config is None or self.transport is None:
            return self.template.generate(findings, evidence)
        for _attempt in range(self.config.max_attempts):
            try:
                payload = self.transport.complete(
                    model=self.config.model,
                    prompt=_prompt(findings),
                    timeout_seconds=self.config.timeout_seconds,
                )
                feedback = Feedback.model_validate(payload)
                validate_feedback(feedback, findings, evidence)
                _reject_invented_fault(feedback, findings)
                return feedback
            except (FeedbackValidationError, ValueError, TimeoutError, OSError):
                continue
        return self.template.generate(findings, evidence)


def _prompt(findings: AnalysisFindings) -> str:
    return (
        "Explain only validated findings. Do not turn candidate diagnostics into coaching advice. "
        f"Findings: {len(findings.findings)}."
    )


def _reject_invented_fault(feedback: Feedback, findings: AnalysisFindings) -> None:
    if findings.findings:
        return
    text = " ".join([feedback.summary, *(tip.explanation for tip in feedback.tips)]).lower()
    if _FAULTY_PHRASE in text or "low arm extension" in text:
        raise FeedbackValidationError("Feedback invented a technique fault.")
