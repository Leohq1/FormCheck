import os
import shutil
from pathlib import Path

import pytest
from formcheck_video.inspection import inspect_video
from formcheck_video.normalization import normalize_video


@pytest.mark.assets
@pytest.mark.integration
def test_sample_video_inspection_and_normalization(tmp_path: Path) -> None:
    raw = os.environ.get("FORMCHECK_SAMPLE_VIDEO")
    if not raw or not Path(raw).is_file():
        pytest.skip("FORMCHECK_SAMPLE_VIDEO is not set or does not point to a file")
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        pytest.skip("ffmpeg and ffprobe are required for the sample video test")

    source = Path(raw)
    inspection = inspect_video(source)
    video_output = tmp_path / "video.mp4"
    timestamps = tmp_path / "timestamps.json"
    from formcheck_video.process import SubprocessRunner

    result = normalize_video(
        source,
        video_output,
        timestamps,
        runner=SubprocessRunner(),
        inspection=inspection,
    )

    assert inspection.decode_ok
    assert result.contract_version == "normalization.v1"
    assert video_output.is_file()
    assert timestamps.is_file()
