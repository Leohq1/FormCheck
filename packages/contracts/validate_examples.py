"""Validate contract examples against their JSON Schemas.

Run from this directory (or any cwd):

    pip install -r packages/contracts/requirements.txt
    python packages/contracts/validate_examples.py

Schemas use relative $id values (e.g. analysis-result.schema.json) so refs
resolve via this registry. Prefer this script (or an equivalent that loads
all schemas into a registry) over validating a single file in isolation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parent

SCHEMA_FILES = [
    "common.schema.json",
    "analysis-error.schema.json",
    "analysis-job.schema.json",
    "analysis-progress.schema.json",
    "analysis-findings.schema.json",
    "analysis-result.schema.json",
]

PAIRS = [
    ("analysis-job.schema.json", "examples/analysis-job.example.json"),
    ("analysis-progress.schema.json", "examples/analysis-progress.example.json"),
    ("analysis-error.schema.json", "examples/analysis-error.example.json"),
    ("analysis-findings.schema.json", "examples/analysis-findings.example.json"),
    ("analysis-result.schema.json", "examples/analysis-result.example.json"),
    ("analysis-result.schema.json", "examples/analysis-result-failed.example.json"),
    ("analysis-result.schema.json", "examples/analysis-result-inconclusive.example.json"),
]


def build_registry() -> Registry:
    resources = []
    for name in SCHEMA_FILES:
        data = json.loads((ROOT / name).read_text(encoding="utf-8"))
        resources.append((data["$id"], Resource.from_contents(data)))
    return Registry().with_resources(resources)


def main() -> int:
    registry = build_registry()
    format_checker = FormatChecker()

    for schema_name, example_name in PAIRS:
        schema = json.loads((ROOT / schema_name).read_text(encoding="utf-8"))
        example = json.loads((ROOT / example_name).read_text(encoding="utf-8"))
        Draft202012Validator(
            schema, registry=registry, format_checker=format_checker
        ).validate(example)
        print(f"ok {schema_name} <- {example_name}")

    # Semantic guard: failed without error must not validate
    failed_ok = json.loads(
        (ROOT / "examples/analysis-result-failed.example.json").read_text(encoding="utf-8")
    )
    broken = dict(failed_ok)
    broken["error"] = None
    result_schema = json.loads((ROOT / "analysis-result.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(
        result_schema, registry=registry, format_checker=format_checker
    )
    errors = list(validator.iter_errors(broken))
    if not errors:
        print("FAIL: failed status with error=null unexpectedly validated", file=sys.stderr)
        return 1
    print("ok conditional: failed + error=null is rejected")

    # Semantic guard: completed with a non-null error must not validate
    completed_ok = json.loads(
        (ROOT / "examples/analysis-result.example.json").read_text(encoding="utf-8")
    )
    completed_broken = dict(completed_ok)
    completed_broken["error"] = failed_ok["error"]
    errors = list(validator.iter_errors(completed_broken))
    if not errors:
        print(
            "FAIL: completed status with non-null error unexpectedly validated",
            file=sys.stderr,
        )
        return 1
    print("ok conditional: completed + error!=null is rejected")

    # Semantic guard: inconclusive without error must not validate (§8.5)
    inconclusive_ok = json.loads(
        (ROOT / "examples/analysis-result-inconclusive.example.json").read_text(
            encoding="utf-8"
        )
    )
    inconclusive_broken = dict(inconclusive_ok)
    inconclusive_broken["error"] = None
    errors = list(validator.iter_errors(inconclusive_broken))
    if not errors:
        print(
            "FAIL: inconclusive status with error=null unexpectedly validated",
            file=sys.stderr,
        )
        return 1
    print("ok conditional: inconclusive + error=null is rejected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
