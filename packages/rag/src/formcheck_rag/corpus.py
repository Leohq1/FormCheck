from pathlib import Path

from formcheck_rag.chunking import Chunk, chunk_document
from formcheck_rag.embeddings import LOCAL_EMBEDDING_MODEL, embed_text
from formcheck_rag.manifest import SourceManifest, load_manifest
from formcheck_rag.retrieval import InMemoryIndex

CORPUS_VERSION = "knsu-cc-by-sa-2026-10-17"


def load_index(manifest_path: Path, corpus_version: str = CORPUS_VERSION) -> InMemoryIndex:
    """Index approved sources whose text files sit next to the manifest."""
    index = InMemoryIndex()
    for source in load_manifest(manifest_path):
        text = _approved_text(manifest_path, source)
        if text is None:
            continue
        index.add(chunk_document(text, source, corpus_version=corpus_version))
    return index


def metadata_sql(manifest_path: Path, corpus_version: str = CORPUS_VERSION) -> str:
    """Upsert approved sources and chunks. Embeddings stay unset."""
    statements: list[str] = []
    for source in load_manifest(manifest_path):
        text = _approved_text(manifest_path, source)
        if text is None:
            continue
        statements.append(_source_upsert(source, corpus_version))
        for chunk in chunk_document(text, source, corpus_version=corpus_version):
            statements.append(_chunk_upsert(chunk))
    return "\n".join(statements)


def _source_upsert(source: SourceManifest, corpus_version: str) -> str:
    columns = (
        "source_id, title, author, publisher, publication_date, license, allowed_use, "
        "source_version, stroke_tags, fault_tags, phase_tags, body_region_tags, "
        "audience, skill_level, page_locator, review_status, reviewer, review_date, "
        "content_hash, corpus_version"
    )
    values = ", ".join(
        [
            _quote(source.source_id),
            _quote(source.title),
            _quote(source.author),
            _quote(source.publisher),
            _quote(source.publication_date),
            _quote(source.license),
            _quote(source.allowed_use),
            _quote(source.source_version),
            _array(source.stroke_tags),
            _array(source.fault_tags),
            _array(source.phase_tags),
            _array(source.body_region_tags),
            _quote(source.audience),
            _quote(source.skill_level),
            _quote(source.page_locator),
            _quote(source.review_status),
            _quote(source.reviewer),
            _quote(source.review_date),
            _quote(source.content_hash),
            _quote(corpus_version),
        ]
    )
    return (
        f"INSERT INTO coaching_source ({columns}) VALUES ({values}) "
        "ON CONFLICT (source_id) DO UPDATE SET "
        "title = EXCLUDED.title, author = EXCLUDED.author, publisher = EXCLUDED.publisher, "
        "publication_date = EXCLUDED.publication_date, license = EXCLUDED.license, "
        "allowed_use = EXCLUDED.allowed_use, source_version = EXCLUDED.source_version, "
        "stroke_tags = EXCLUDED.stroke_tags, fault_tags = EXCLUDED.fault_tags, "
        "phase_tags = EXCLUDED.phase_tags, body_region_tags = EXCLUDED.body_region_tags, "
        "audience = EXCLUDED.audience, skill_level = EXCLUDED.skill_level, "
        "page_locator = EXCLUDED.page_locator, review_status = EXCLUDED.review_status, "
        "reviewer = EXCLUDED.reviewer, review_date = EXCLUDED.review_date, "
        "content_hash = EXCLUDED.content_hash, corpus_version = EXCLUDED.corpus_version;"
    )


def _chunk_upsert(chunk: Chunk) -> str:
    columns = (
        "chunk_id, source_id, locator, text_content, source_version, stroke_tags, "
        "fault_tags, phase_tags, body_region_tags, audience, skill_level, page_locator, "
        "review_status, corpus_version, embedding, embedding_model"
    )
    vector = "[" + ",".join(f"{value:.8f}" for value in embed_text(chunk.text)) + "]"
    values = ", ".join(
        [
            _quote(chunk.chunk_id),
            _quote(chunk.source_id),
            _quote(chunk.locator),
            _quote(chunk.text),
            _quote(chunk.source_version),
            _array(chunk.stroke_tags),
            _array(chunk.fault_tags),
            _array(chunk.phase_tags),
            _array(chunk.body_region_tags),
            _quote(chunk.audience),
            _quote(chunk.skill_level),
            _quote(chunk.page_locator),
            _quote(chunk.review_status),
            _quote(chunk.corpus_version),
            _quote(vector) + "::vector",
            _quote(LOCAL_EMBEDDING_MODEL),
        ]
    )
    return (
        f"INSERT INTO coaching_chunk ({columns}) VALUES ({values}) "
        "ON CONFLICT (chunk_id) DO UPDATE SET "
        "source_id = EXCLUDED.source_id, locator = EXCLUDED.locator, "
        "text_content = EXCLUDED.text_content, source_version = EXCLUDED.source_version, "
        "stroke_tags = EXCLUDED.stroke_tags, fault_tags = EXCLUDED.fault_tags, "
        "phase_tags = EXCLUDED.phase_tags, body_region_tags = EXCLUDED.body_region_tags, "
        "audience = EXCLUDED.audience, skill_level = EXCLUDED.skill_level, "
        "page_locator = EXCLUDED.page_locator, review_status = EXCLUDED.review_status, "
        "corpus_version = EXCLUDED.corpus_version, embedding = EXCLUDED.embedding, "
        "embedding_model = EXCLUDED.embedding_model;"
    )


def _quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _array(values: list[str]) -> str:
    if not values:
        return "ARRAY[]::text[]"
    return "ARRAY[" + ", ".join(_quote(value) for value in values) + "]"


def _approved_text(manifest_path: Path, source: SourceManifest) -> str | None:
    if source.review_status != "approved" or not source.text_file:
        return None
    return (manifest_path.parent / source.text_file).read_text(encoding="utf-8")
