"""Hosted coaching adapter. Missing credentials use the template generator."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from formcheck_rag.chunking import Chunk
from formcheck_rag.feedback import (
    PROMPT_VERSION,
    Feedback,
    TemplateFeedbackGenerator,
    validate_feedback,
)
from formcheck_rag.findings import AnalysisFindings

HOSTED_MODEL = "gpt-6-luna"


class HostedFeedbackGenerator:
    """Call the hosted model only when OPENAI_API_KEY is set. Otherwise fall back."""

    def __init__(self, timeout_seconds: float = 8.0) -> None:
        self.timeout_seconds = timeout_seconds

    def generate(self, findings: AnalysisFindings, evidence: list[Chunk]) -> Feedback:
        fallback = TemplateFeedbackGenerator().generate(findings, evidence)
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            return fallback
        try:
            hosted = _request(api_key, findings, evidence, self.timeout_seconds)
            validate_feedback(hosted, findings, evidence)
            return hosted
        except (OSError, urllib.error.URLError, TimeoutError, ValueError, KeyError):
            return fallback


def _request(
    api_key: str,
    findings: AnalysisFindings,
    evidence: list[Chunk],
    timeout_seconds: float,
) -> Feedback:
    body = {
        "model": HOSTED_MODEL,
        "messages": [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "findings": [item.model_dump() for item in findings.findings],
                        "chunks": [item.model_dump() for item in evidence],
                    }
                ),
            }
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        payload = json.loads(response.read().decode("utf-8"))
    content = payload["choices"][0]["message"]["content"]
    parsed = json.loads(content)
    parsed.setdefault("prompt_version", PROMPT_VERSION)
    parsed.setdefault("model", HOSTED_MODEL)
    return Feedback.model_validate(parsed)
