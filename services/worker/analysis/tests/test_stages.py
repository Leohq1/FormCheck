from pathlib import Path

from formcheck_analysis.stages import build_real_stages
from formcheck_biomechanics.models import Handedness, ViewHint


def test_disabled_rules_emit_no_diagnostics(tmp_path: Path) -> None:
    stages = build_real_stages(
        tmp_path,
        tmp_path / "missing.task",
        Handedness.RIGHT,
        ViewHint.SIDE,
    )

    assert stages.rules((), False) == ()
