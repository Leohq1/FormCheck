import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from formcheck_rag.manifest import load_manifest

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_manifest_accepts_required_rights_fields():
    sources = load_manifest(FIXTURES / "sources.json")

    assert len(sources) == 2
    approved = sources[0]
    assert approved.source_id == "source-test-clear"
    assert approved.review_status == "approved"
    assert approved.license
    assert "overhead_clear" in approved.stroke_tags


def test_load_manifest_rejects_a_source_without_a_license(tmp_path: Path):
    payload = json.loads((FIXTURES / "sources.json").read_text(encoding="utf-8"))
    payload[0].pop("license")
    path = tmp_path / "sources-missing-license.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValidationError):
        load_manifest(path)
