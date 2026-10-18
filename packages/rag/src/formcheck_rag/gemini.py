"""Hosted Gemini feedback. A missing key uses the deterministic template."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, Field, ValidationError

from formcheck_rag.chunking import Chunk
from formcheck_rag.feedback import (
    PROMPT_VERSION,
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


def load_local_gemini_env() -> None:
    """Fill missing Gemini variables from the untracked Compose env file."""
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "infra" / "local" / ".env"
        if not candidate.is_file():
            continue
        for line in candidate.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value
        return


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
                    prompt=_prompt(findings, evidence),
                    timeout_seconds=self.config.timeout_seconds,
                )
                feedback = Feedback.model_validate(_coerce_payload(payload, self.config.model))
                validate_feedback(feedback, findings, evidence)
                _reject_invented_fault(feedback, findings)
                return feedback
            except (FeedbackValidationError, ValidationError, ValueError, TimeoutError, OSError):
                continue
        return self.template.generate(findings, evidence)


class UrllibGeminiTransport:
    """POST generateContent. The API key stays in the request header."""

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def complete(self, *, model: str, prompt: str, timeout_seconds: float) -> dict[str, object]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        body = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2, "responseMimeType": "application/json"},
        }
        request = urllib.request.Request(
            url,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": self._api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:500]
            if self._api_key:
                detail = detail.replace(self._api_key, "[redacted]")
            raise ValueError(f"Gemini request failed with HTTP {exc.code}: {detail}") from exc
        parsed = parse_gemini_json(_response_text(raw))
        parsed.setdefault("model", model)
        parsed.setdefault("prompt_version", PROMPT_VERSION)
        return parsed


def parse_gemini_json(text: str) -> dict[str, object]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    payload = json.loads(cleaned)
    if not isinstance(payload, dict):
        raise ValueError("Gemini response was not a JSON object.")
    return payload


def _response_text(payload: dict[str, object]) -> str:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Gemini response did not include a candidate.")
    content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list):
        raise ValueError("Gemini response did not include text.")
    texts = [
        part["text"]
        for part in parts
        if isinstance(part, dict) and isinstance(part.get("text"), str) and not part.get("thought")
    ]
    if not texts:
        raise ValueError("Gemini response did not include text.")
    return "\n".join(texts)


def _prompt(findings: AnalysisFindings, evidence: list[Chunk]) -> str:
    finding_rows = [item.model_dump() for item in findings.findings]
    passages = [
        {
            "source_id": chunk.source_id,
            "chunk_id": chunk.chunk_id,
            "locator": chunk.locator,
            "text": chunk.text,
        }
        for chunk in evidence
    ]
    return (
        "Write badminton coaching JSON for the supplied findings only. "
        "Do not invent a finding, a measurement, or a citation. "
        "Do not give medical advice or injury guarantees. "
        "If findings is empty, tips must be an empty list and the summary must not claim a technique fault. "
        "Each tip cites one supplied passage by copying source_id, chunk_id, and locator exactly. "
        "Use at most three tips. Set prompt_version to \"1\". "
        "Return one JSON object with summary, tips, limitations, model, and prompt_version. "
        "Each tip has finding_id, title, explanation, practice_cue, and citations. "
        f"Findings: {json.dumps(finding_rows)} "
        f"Passages: {json.dumps(passages)}"
    )


def _coerce_payload(payload: dict[str, object], model: str) -> dict[str, object]:
    if not isinstance(payload.get("tips"), (list, dict)):
        raise ValueError("Gemini response did not include tips.")
    if not isinstance(payload.get("summary"), str):
        raise ValueError("Gemini response did not include a summary.")
    data = dict(payload)
    limitations = data.get("limitations")
    if isinstance(limitations, str):
        data["limitations"] = [limitations] if limitations.strip() else []
    tips = data.get("tips")
    if isinstance(tips, dict):
        data["tips"] = [tips]
    data["model"] = model
    data["prompt_version"] = PROMPT_VERSION
    return data


def _reject_invented_fault(feedback: Feedback, findings: AnalysisFindings) -> None:
    if findings.findings:
        return
    text = " ".join([feedback.summary, *(tip.explanation for tip in feedback.tips)]).lower()
    if _FAULTY_PHRASE in text or "low arm extension" in text:
        raise FeedbackValidationError("Feedback invented a technique fault.")
