import json
from pathlib import Path

from pydantic import BaseModel, Field


class SourceManifest(BaseModel):
    source_id: str
    title: str
    author: str
    publisher: str
    publication_date: str
    license: str = Field(min_length=1)
    allowed_use: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    stroke_tags: list[str]
    fault_tags: list[str]
    phase_tags: list[str] = Field(default_factory=list)
    body_region_tags: list[str]
    audience: str = Field(min_length=1)
    skill_level: str = Field(min_length=1)
    page_locator: str = Field(min_length=1)
    review_status: str
    reviewer: str
    review_date: str
    content_hash: str
    text_file: str | None = None
    citation_scope: str = "test"
    canonical_location: str | None = None
    retrieved_on: str | None = None

    def allows_user_facing_citation(self) -> bool:
        return self.review_status == "approved" and self.citation_scope == "user" and bool(self.license)


def load_manifest(path: Path) -> list[SourceManifest]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("A source manifest must be a JSON list.")
    return [SourceManifest.model_validate(item) for item in payload]
