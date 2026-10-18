from pydantic import BaseModel, Field

from formcheck_rag.chunking import Chunk
from formcheck_rag.findings import AnalysisFindings, Finding

PROMPT_VERSION = "1"
TEMPLATE_MODEL = "template-fallback"
_SEVERITY_RANK = {
    "high": 3,
    "major": 3,
    "moderate": 2,
    "medium": 2,
    "low": 1,
    "minor": 1,
}
_ANGLE_FEATURE = "dominant_elbow_angle_at_max_wrist_height_deg"
_INCONCLUSIVE_WARNINGS = {
    "unsupported_view",
    "low_pose_confidence",
    "body_not_fully_visible",
    "inconclusive_pose",
}
_WARNING_TEXT = {
    "contact_uncertain": (
        "Contact time was estimated from body motion because the racket and shuttle were not tracked."
    ),
    "uncertain_contact": (
        "Contact time was estimated from body motion because the racket and shuttle were not tracked."
    ),
    "unsupported_view": "The camera view is outside the supported side and rear three-quarter views.",
    "low_pose_confidence": "Pose confidence was too low to support a technique finding.",
    "body_not_fully_visible": "The full body was not visible throughout the stroke.",
    "inconclusive_pose": "Pose quality was inconclusive, so no technique fault was reported.",
}


class Citation(BaseModel):
    source_id: str
    chunk_id: str
    locator: str


class Tip(BaseModel):
    finding_id: str
    title: str
    explanation: str
    practice_cue: str
    citations: list[Citation]


class Feedback(BaseModel):
    summary: str
    tips: list[Tip] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    model: str
    prompt_version: str


class FeedbackValidationError(ValueError):
    pass


class TemplateFeedbackGenerator:
    """Deterministic coaching text. A hosted model can replace this later."""

    def generate(
        self,
        findings: AnalysisFindings,
        evidence: list[Chunk],
        *,
        user_facing: bool = False,
    ) -> Feedback:
        if user_facing:
            evidence = [chunk for chunk in evidence if chunk.citation_scope == "user"]
        ordered = sorted(
            findings.findings,
            key=lambda finding: (_SEVERITY_RANK.get(finding.severity, 0), finding.confidence),
            reverse=True,
        )
        tips: list[Tip] = []
        missing: list[str] = []
        for finding in ordered:
            if len(tips) == 3:
                break
            chunk = _matching_chunk(finding, evidence)
            if chunk is None:
                missing.append(finding.label)
                continue
            tips.append(_tip(finding, chunk))

        summary = _summary(findings, ordered)
        limitations = _limitations(findings, ordered)
        if missing:
            names = ", ".join(missing)
            limitations.append(
                f"No approved coaching passage was available for {names}, so no practice cue was generated."
            )
        return Feedback(
            summary=summary,
            tips=tips,
            limitations=limitations,
            model=TEMPLATE_MODEL,
            prompt_version=PROMPT_VERSION,
        )


def validate_feedback(feedback: Feedback, findings: AnalysisFindings, evidence: list[Chunk]) -> None:
    allowed_findings = {finding.rule_id for finding in findings.findings}
    allowed_citations = {(chunk.source_id, chunk.chunk_id) for chunk in evidence}
    if len(feedback.tips) > 3:
        raise FeedbackValidationError("A result may contain at most three recommendations.")
    for tip in feedback.tips:
        if tip.finding_id not in allowed_findings:
            raise FeedbackValidationError(f"Tip cites a finding that was not supplied: {tip.finding_id}")
        if not tip.citations:
            raise FeedbackValidationError(f"Recommendation {tip.finding_id} has no citation.")
        for citation in tip.citations:
            key = (citation.source_id, citation.chunk_id)
            if key not in allowed_citations:
                raise FeedbackValidationError(
                    f"Citation {citation.source_id}/{citation.chunk_id} was not retrieved."
                )


def _matching_chunk(finding: Finding, evidence: list[Chunk]) -> Chunk | None:
    tags = set(finding.retrieval_tags)
    for chunk in evidence:
        if tags & set(chunk.fault_tags) or tags & set(chunk.phase_tags):
            return chunk
    return None


def _tip(finding: Finding, chunk: Chunk) -> Tip:
    cue = chunk.text.split(".")[0].strip()
    evidence_text = ""
    if finding.evidence:
        item = finding.evidence[0]
        unit = f" {item.unit}" if item.unit else ""
        evidence_text = f" Evidence: {item.feature} was {item.value}{unit}."
    return Tip(
        finding_id=finding.rule_id,
        title=f"Work on {finding.label.lower()}",
        explanation=(
            f"The clip suggests {finding.label.lower()} at {finding.severity} severity, "
            f"with confidence {finding.confidence:.2f}.{evidence_text}"
        ),
        practice_cue=cue,
        citations=[
            Citation(source_id=chunk.source_id, chunk_id=chunk.chunk_id, locator=chunk.locator)
        ],
    )


def _summary(findings: AnalysisFindings, ordered: list[Finding]) -> str:
    if ordered:
        labels = ", ".join(finding.label.lower() for finding in ordered)
        return f"The clip suggests {labels}."
    warnings = set(_warnings(findings))
    if "unsupported_view" in warnings:
        base = "This camera view did not support a technique finding."
    elif warnings & _INCONCLUSIVE_WARNINGS:
        base = "This clip did not produce a supported technique finding."
    else:
        stroke = str(findings.stroke.get("type") or "overhead_clear").replace("_", " ")
        base = f"No supported technique fault was found for this {stroke}."
    measured = _measured_angle(findings)
    if measured is None:
        return base
    return f"{base} {measured}"


def _measured_angle(findings: AnalysisFindings) -> str | None:
    for feature in findings.features:
        if feature.name != _ANGLE_FEATURE or not feature.available or feature.value is None:
            continue
        return (
            f"The measured dominant elbow angle at maximum wrist height was {feature.value:g} degrees. "
            "This describes the arm position. It is not a validated technique finding."
        )
    return None


def _warnings(findings: AnalysisFindings) -> list[str]:
    raw = findings.quality.get("warnings", [])
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw]


def _limitations(findings: AnalysisFindings, ordered: list[Finding]) -> list[str]:
    limitations: list[str] = []
    raw = findings.quality.get("limitations", [])
    if isinstance(raw, list):
        limitations.extend(str(item) for item in raw)
    for warning in _warnings(findings):
        text = _WARNING_TEXT.get(warning)
        if text and text not in limitations:
            limitations.append(text)
    if findings.stroke.get("contact_time_ms") is not None:
        contact = _WARNING_TEXT["contact_uncertain"]
        if contact not in limitations:
            limitations.append(contact)
    if any(finding.confidence < 0.70 for finding in ordered):
        limitations.append(
            "At least one finding is below 0.70 confidence and is reported with that uncertainty."
        )
    return limitations
