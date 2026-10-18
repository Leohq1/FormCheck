"""Person 4 coaching stage. Uses the local corpus and the template generator."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from formcheck_rag.corpus import CORPUS_VERSION, load_index
from formcheck_rag.embeddings import LOCAL_EMBEDDING_MODEL
from formcheck_rag.feedback import TEMPLATE_MODEL, TemplateFeedbackGenerator, validate_feedback
from formcheck_rag.findings import AnalysisFindings


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
    feedback = TemplateFeedbackGenerator().generate(findings, evidence)
    validate_feedback(feedback, findings, evidence)
    updated = dict(result)
    updated["feedback"] = feedback.model_dump()
    versions = dict(result.get("versions") or {})
    versions["corpus"] = CORPUS_VERSION
    versions["embedding"] = LOCAL_EMBEDDING_MODEL
    versions["generation"] = TEMPLATE_MODEL
    updated["versions"] = versions
    return updated


def _manifest() -> Path:
    override = os.environ.get("FORMCHECK_CORPUS_MANIFEST")
    if override:
        return Path(override)
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "corpus" / "manifests" / "sources.json"
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("corpus/manifests/sources.json")
