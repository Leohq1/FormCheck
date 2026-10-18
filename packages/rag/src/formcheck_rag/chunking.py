from pydantic import BaseModel, Field

from formcheck_rag.manifest import SourceManifest

MAX_WORDS = 500
WINDOW_WORDS = 450
OVERLAP_WORDS = 40


class Chunk(BaseModel):
    chunk_id: str
    source_id: str
    text: str
    locator: str
    stroke_tags: list[str]
    fault_tags: list[str]
    phase_tags: list[str] = Field(default_factory=list)
    review_status: str
    corpus_version: str
    relevance_score: float = 0.0


def chunk_document(text: str, source: SourceManifest, corpus_version: str) -> list[Chunk]:
    sections = _sections(text)
    chunks: list[Chunk] = []
    for locator, body in sections:
        for piece in _windows(body):
            cleaned = piece.strip()
            if not cleaned:
                continue
            chunks.append(
                Chunk(
                    chunk_id=f"{source.source_id}-{len(chunks) + 1:03d}",
                    source_id=source.source_id,
                    text=cleaned,
                    locator=locator,
                    stroke_tags=list(source.stroke_tags),
                    fault_tags=list(source.fault_tags),
                    phase_tags=list(source.phase_tags),
                    review_status=source.review_status,
                    corpus_version=corpus_version,
                )
            )
    return chunks


def _sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = []
    locator = "Introduction"
    buffer: list[str] = []
    for line in text.splitlines():
        if line.startswith("#"):
            if buffer:
                sections.append((locator, buffer))
            locator = line.lstrip("#").strip() or locator
            buffer = []
            continue
        buffer.append(line)
    if buffer:
        sections.append((locator, buffer))
    return [(name, "\n".join(lines).strip()) for name, lines in sections if "\n".join(lines).strip()]


def _windows(body: str) -> list[str]:
    words = body.split()
    if len(words) <= MAX_WORDS:
        return [body]
    windows: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + WINDOW_WORDS, len(words))
        windows.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - OVERLAP_WORDS
    return windows
