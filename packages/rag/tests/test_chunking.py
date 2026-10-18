from pathlib import Path

from formcheck_rag.chunking import chunk_document
from formcheck_rag.manifest import load_manifest

FIXTURES = Path(__file__).parent / "fixtures"


def test_chunks_follow_headings_and_stay_within_the_token_budget():
    source = load_manifest(FIXTURES / "sources.json")[0]
    text = (FIXTURES / "clear-coaching.md").read_text(encoding="utf-8")

    chunks = chunk_document(text, source, corpus_version="test-1")

    assert len(chunks) >= 2
    locators = [chunk.locator for chunk in chunks]
    assert "Arm extension" in locators
    assert "Court recovery" in locators
    elbow = next(chunk for chunk in chunks if chunk.locator == "Arm extension")
    assert "center of the court" not in elbow.text
    assert all(len(chunk.text.split()) <= 540 for chunk in chunks)
    assert all(chunk.review_status == "approved" for chunk in chunks)
    assert all(chunk.corpus_version == "test-1" for chunk in chunks)
    assert all(chunk.source_version == "synthetic-1" for chunk in chunks)
    assert all(chunk.page_locator == "fixture" for chunk in chunks)
    assert all(chunk.body_region_tags == ["dominant_arm", "elbow"] for chunk in chunks)


def test_long_section_splits_instead_of_mixing_into_the_next_heading():
    source = load_manifest(FIXTURES / "sources.json")[0]
    long_section = " ".join(f"elbowword{i}" for i in range(800))
    text = f"# Elbow timing\n\n{long_section}\n\n# Court recovery\n\nRecover toward the center of the court.\n"

    chunks = chunk_document(text, source, corpus_version="test-1")
    elbow_chunks = [chunk for chunk in chunks if chunk.locator == "Elbow timing"]

    assert len(elbow_chunks) >= 2
    assert all("center of the court" not in chunk.text for chunk in elbow_chunks)
    assert all(len(chunk.text.split()) <= 540 for chunk in elbow_chunks)
