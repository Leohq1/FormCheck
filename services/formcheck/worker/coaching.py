"""Person 4 coaching stage. Uses the local corpus and Gemini when configured."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from formcheck.worker.projection import PROVISIONAL_LOW_ARM_CUTOFF_DEG
from formcheck_rag.corpus import CORPUS_VERSION, load_index
from formcheck_rag.embeddings import LOCAL_EMBEDDING_MODEL
from formcheck_rag.feedback import TemplateFeedbackGenerator, validate_feedback
from formcheck_rag.findings import AnalysisFindings
from formcheck_rag.gemini import (
    GeminiFeedbackGenerator,
    UrllibGeminiTransport,
    gemini_config_from_env,
    load_local_gemini_env,
)


def apply_coaching(result: dict[str, Any]) -> dict[str, Any]:
    """Replace placeholder feedback with cited passages from the approved corpus."""
    if result.get("status") != "completed" or not result.get("findings"):
        return result
    findings = AnalysisFindings.model_validate(
        {
            "schema_version": "0-draft",
            "analysis_id": result["analysis_id"],
            "quality": result.get("quality") or {},
            "stroke": result.get("stroke") or {},
            "findings": result.get("findings") or [],
        }
    )
    evidence = load_index(_manifest()).search_findings(findings)
    feedback = _generator().generate(findings, evidence)
    validate_feedback(feedback, findings, evidence)
    updated = dict(result)
    dumped = feedback.model_dump()
    note = (
        f"The {PROVISIONAL_LOW_ARM_CUTOFF_DEG:.0f} degree cutoff is a provisional test "
        "and is not calibrated."
    )
    limitations = [str(item) for item in dumped.get("limitations") or []]
    if note not in limitations:
        limitations.append(note)
    dumped["limitations"] = limitations
    updated["feedback"] = dumped
    versions = dict(result.get("versions") or {})
    versions["corpus"] = CORPUS_VERSION
    versions["embedding"] = LOCAL_EMBEDDING_MODEL
    versions["generation"] = feedback.model
    updated["versions"] = versions
    return updated


def _generator() -> GeminiFeedbackGenerator | TemplateFeedbackGenerator:
    load_local_gemini_env()
    config = gemini_config_from_env()
    if config is None:
        return TemplateFeedbackGenerator()
    return GeminiFeedbackGenerator(config, UrllibGeminiTransport(config.api_key))


def _manifest() -> Path:
    override = os.environ.get("FORMCHECK_CORPUS_MANIFEST")
    if override:
        return Path(override)
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "corpus" / "manifests" / "sources.json"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("corpus/manifests/sources.json")
