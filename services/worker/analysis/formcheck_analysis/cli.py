"""Development command. This is not the production worker adapter."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from formcheck_biomechanics.models import Handedness, ViewHint

from formcheck_analysis.pipeline import AnalysisFailure, AnalysisJobDraft, AnalysisPipeline


def main(argv: list[str] | None = None, *, pipeline_factory: Callable[[Path], AnalysisPipeline] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="formcheck-analyze")
    parser.add_argument("--analysis-id", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--handedness", required=True, choices=["left", "right"])
    parser.add_argument("--view", required=True, choices=["side", "rear_three_quarter"])
    parser.add_argument("--development-diagnostics", action="store_true")
    args = parser.parse_args(argv)
    source = Path(args.source)
    if not source.is_file():
        print("The source video was not found.", file=sys.stderr)
        return 2
    try:
        analysis_id = UUID(args.analysis_id)
    except ValueError:
        print("The analysis id is not a UUID.", file=sys.stderr)
        return 2
    job = AnalysisJobDraft(
        analysis_id=analysis_id,
        video_object_key=str(source),
        handedness=Handedness(args.handedness),
        view_hint=ViewHint(args.view),
    )
    factory = pipeline_factory or _unavailable_pipeline
    try:
        findings = factory(source).run(job, development_diagnostics=args.development_diagnostics)
    except Exception as exc:
        safe = getattr(exc, "safe_message", None) or "Analysis could not be completed."
        print(safe, file=sys.stderr)
        return 1
    payload = findings.to_development_dict() if args.development_diagnostics else findings.to_production_dict()
    print(json.dumps(payload))
    return 0


def _unavailable_pipeline(source: Path) -> AnalysisPipeline:
    del source
    raise AnalysisFailure(
        "Install FFmpeg and set MEDIAPIPE_POSE_MODEL_PATH before analyzing a video."
    )
