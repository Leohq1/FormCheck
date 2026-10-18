"""Generation checks that do not require a hosted model."""

from __future__ import annotations


def finding_faithfulness(tip_finding_ids: list[str], supplied_finding_ids: set[str]) -> float:
    if not tip_finding_ids:
        return 1.0
    faithful = sum(1 for finding_id in tip_finding_ids if finding_id in supplied_finding_ids)
    return faithful / len(tip_finding_ids)


def unsupported_claim_rate(claims: list[str], allowed_terms: set[str]) -> float:
    if not claims:
        return 0.0
    unsupported = sum(1 for claim in claims if claim not in allowed_terms)
    return unsupported / len(claims)
