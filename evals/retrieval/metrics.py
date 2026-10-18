"""Retrieval metrics for a labeled query set."""

from __future__ import annotations


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 5) -> float:
    if not relevant_ids:
        return 1.0
    window = set(retrieved_ids[:k])
    return len(window & relevant_ids) / len(relevant_ids)


def citation_validity(citations: list[tuple[str, str]], allowed: set[tuple[str, str]]) -> float:
    if not citations:
        return 1.0
    valid = sum(1 for citation in citations if citation in allowed)
    return valid / len(citations)
