import re

from pydantic import BaseModel, Field

from formcheck_rag.chunking import Chunk
from formcheck_rag.embeddings import embed_text
from formcheck_rag.findings import AnalysisFindings

_TOKEN = re.compile(r"[a-z0-9_]+")


class RetrievalQuery(BaseModel):
    stroke: str
    finding: str
    phase: str | None = None
    severity: str | None = None
    fault_tags: list[str] = Field(default_factory=list)
    evidence_summary: str = ""


class InMemoryIndex:
    """Metadata-filtered keyword index used until pgvector is available."""

    def __init__(self) -> None:
        self._chunks: list[Chunk] = []

    def add(self, chunks: list[Chunk]) -> None:
        self._chunks.extend(chunks)

    def search(self, query: RetrievalQuery, limit: int = 6) -> list[Chunk]:
        scored: list[Chunk] = []
        seen: set[str] = set()
        for chunk in self._chunks:
            if chunk.review_status != "approved":
                continue
            if query.stroke not in chunk.stroke_tags:
                continue
            if query.fault_tags and not set(query.fault_tags) & set(chunk.fault_tags):
                continue
            key = " ".join(chunk.text.lower().split())
            if key in seen:
                continue
            score = _score(query, chunk)
            if score <= 0:
                continue
            seen.add(key)
            scored.append(chunk.model_copy(update={"relevance_score": score}))
        scored.sort(key=lambda chunk: chunk.relevance_score, reverse=True)
        return scored[:limit]

    def search_findings(self, findings: AnalysisFindings, limit: int = 6) -> list[Chunk]:
        merged: list[Chunk] = []
        seen: set[str] = set()
        for query in queries_from_findings(findings):
            for chunk in self.search(query, limit=limit):
                if chunk.chunk_id in seen:
                    continue
                seen.add(chunk.chunk_id)
                merged.append(chunk)
        return merged[:limit]


_STROKE_ALIASES = {
    "clear": "overhead_clear",
    "smash": "overhead_smash",
    "drop": "overhead_drop",
}


def queries_from_findings(findings: AnalysisFindings) -> list[RetrievalQuery]:
    raw_stroke = str(findings.stroke.get("type") or "overhead_clear")
    stroke = _STROKE_ALIASES.get(raw_stroke, raw_stroke)
    phase = findings.stroke.get("phase")
    queries: list[RetrievalQuery] = []
    for finding in findings.findings:
        tags = [tag for tag in finding.retrieval_tags if tag != stroke]
        evidence = "; ".join(
            " ".join(
                part
                for part in (item.feature, str(item.value), item.unit)
                if part
            )
            for item in finding.evidence
        )
        queries.append(
            RetrievalQuery(
                stroke=stroke,
                finding=finding.rule_id,
                phase=str(phase) if phase else None,
                severity=finding.severity,
                fault_tags=tags,
                evidence_summary=evidence,
            )
        )
    return queries


def _tokens(value: str) -> set[str]:
    return set(_TOKEN.findall(value.lower()))


def _score(query: RetrievalQuery, chunk: Chunk) -> float:
    query_text = " ".join([query.finding, query.evidence_summary, query.phase or "", *query.fault_tags])
    query_tokens = _tokens(query_text)
    text_tokens = _tokens(chunk.text)
    tag_tokens = _tokens(" ".join([*chunk.fault_tags, *chunk.phase_tags, chunk.locator]))
    lexical = float(len(query_tokens & text_tokens) + (2 * len(query_tokens & tag_tokens)))
    return lexical + _cosine(embed_text(query_text), embed_text(chunk.text))


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))
