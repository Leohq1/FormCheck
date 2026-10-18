import json
from pathlib import Path

from formcheck_analysis.cli import main
from formcheck_analysis.models import AnalysisFindings
from formcheck_analysis.pipeline import AnalysisJobDraft
from formcheck_biomechanics.models import Handedness, QualityDisposition, QualityReport, ViewHint
from formcheck_rules.models import CalibrationStatus, CandidateRuleEvaluation, DiagnosticOutcome


class _Pipeline:
    def run(self, job: AnalysisJobDraft, *, development_diagnostics: bool = False) -> AnalysisFindings:
        diagnostics = None
        if development_diagnostics:
            from formcheck_analysis.models import AnalysisDiagnostics

            diagnostics = AnalysisDiagnostics(
                candidate_rule_evaluations=[
                    CandidateRuleEvaluation(
                        rule_id="clear.low_arm_extension.v1",
                        enabled=False,
                        calibration_status=CalibrationStatus.NOT_CALIBRATED,
                        evaluation=DiagnosticOutcome.WOULD_TRIGGER,
                        message="Candidate evaluation only; not a validated technique finding.",
                    )
                ]
            )
        return AnalysisFindings(
            analysis_id=str(job.analysis_id),
            quality=QualityReport(overall=0.5, eligible=True, disposition=QualityDisposition.ELIGIBLE),
            features=[],
            findings=[],
            versions={
                "pipeline": "2026.10.0",
                "pose_estimator": "mediapipe-pose-landmarker",
                "feature_schema": "1",
                "rule_set": "clear.low_arm_extension.v1",
            },
            diagnostics=diagnostics,
            handedness=Handedness.RIGHT,
            view_hint=ViewHint.REAR_THREE_QUARTER,
        )


def test_cli_production_json_omits_diagnostics(tmp_path: Path, capsys) -> None:
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"video")
    code = main(
        [
            "--analysis-id",
            "11111111-1111-4111-8111-111111111111",
            "--source",
            str(source),
            "--handedness",
            "right",
            "--view",
            "rear_three_quarter",
        ],
        pipeline_factory=lambda _path: _Pipeline(),
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert code == 0
    assert payload["findings"] == []
    assert "diagnostics" not in payload


def test_missing_source_is_a_safe_nonzero_exit(tmp_path: Path, capsys) -> None:
    code = main(
        [
            "--analysis-id",
            "11111111-1111-4111-8111-111111111111",
            "--source",
            str(tmp_path / "missing.mp4"),
            "--handedness",
            "right",
            "--view",
            "side",
        ]
    )
    captured = capsys.readouterr()

    assert code == 2
    assert "not found" in captured.err.lower()
    assert "Traceback" not in captured.err


def test_unconfigured_tools_return_actionable_stderr(tmp_path: Path, capsys) -> None:
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"video")
    code = main(
        [
            "--analysis-id",
            "11111111-1111-4111-8111-111111111111",
            "--source",
            str(source),
            "--handedness",
            "right",
            "--view",
            "side",
        ]
    )
    captured = capsys.readouterr()

    assert code == 1
    assert "FFmpeg" in captured.err
    assert "Traceback" not in captured.err
