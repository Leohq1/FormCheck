"""Validate payloads against packages/contracts JSON Schemas."""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource

logger = logging.getLogger(__name__)

SCHEMA_FILES = [
    "common.schema.json",
    "analysis-error.schema.json",
    "analysis-job.schema.json",
    "analysis-progress.schema.json",
    "analysis-findings.schema.json",
    "analysis-result.schema.json",
]


def _contracts_root() -> Path:
    """Resolve contracts dir in repo checkout or Docker image layout."""
    here = Path(__file__).resolve()
    env = os.environ.get("FORMCHECK_CONTRACTS_DIR")
    candidates = []
    if env:
        candidates.append(Path(env))
    candidates.extend(
        [
            here.parents[2] / "packages" / "contracts",  # repo: services/formcheck -> root
            Path("/contracts"),
            here.parents[1] / "contracts",
        ]
    )
    for path in candidates:
        if (path / "analysis-result.schema.json").is_file():
            return path
    raise FileNotFoundError(
        "packages/contracts not found; copy schemas into the image or run from the repo"
    )


@lru_cache
def build_registry() -> tuple[Path, Registry]:
    root = _contracts_root()
    resources = []
    for name in SCHEMA_FILES:
        data = json.loads((root / name).read_text(encoding="utf-8"))
        resources.append((data["$id"], Resource.from_contents(data)))
    return root, Registry().with_resources(resources)


@lru_cache
def _validator(schema_name: str) -> Draft202012Validator:
    root, registry = build_registry()
    schema = json.loads((root / schema_name).read_text(encoding="utf-8"))
    return Draft202012Validator(
        schema, registry=registry, format_checker=FormatChecker()
    )


def validate_payload(schema_name: str, payload: dict[str, Any]) -> None:
    _validator(schema_name).validate(payload)


def validate_analysis_job(payload: dict[str, Any]) -> None:
    validate_payload("analysis-job.schema.json", payload)


def validate_analysis_progress(payload: dict[str, Any]) -> None:
    validate_payload("analysis-progress.schema.json", payload)


def validate_analysis_result(payload: dict[str, Any]) -> None:
    validate_payload("analysis-result.schema.json", payload)


def format_validation_error(exc: ValidationError) -> str:
    path = ".".join(str(p) for p in exc.absolute_path) or "<root>"
    return f"{path}: {exc.message}"
