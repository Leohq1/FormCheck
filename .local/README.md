# Local Python setup and analysis assets

The initial lockfile was generated with uv 0.13.1 and verified on Python 3.12.
Install uv from https://docs.astral.sh/uv/getting-started/installation/ and run
these commands from the repository root:

```powershell
uv lock --check
uv sync --locked --all-groups
uv run --locked python -c "import cv2, mediapipe, numpy, pydantic, scipy"
uv run --locked pytest
uv run --locked ruff check packages services/worker/analysis
uv run --locked mypy packages/video/formcheck_video packages/pose/formcheck_pose packages/biomechanics/formcheck_biomechanics packages/rules/formcheck_rules services/worker/analysis/formcheck_analysis
```

The default `dev` group includes `analysis` (MediaPipe, headless OpenCV, SciPy),
`test` (pytest, Hypothesis), Ruff, and mypy. Base dependencies are NumPy and
Pydantic. Use `uv lock --upgrade-package <package>` for deliberate upgrades,
then repeat the import smoke check and tests before accepting the new lockfile.
FFmpeg and ffprobe are separate system tools required by later video integration
tests; uv does not install them.

The initial MediaPipe lock also brings in `opencv-contrib-python` alongside the
requested `opencv-python-headless`. Both provide `cv2`; the locked Windows
environment passes the import smoke check, but this does not establish a purely
headless deployment. Review that overlap before choosing a production image.

## Optional local assets

Only this README is tracked under `.local/`. Recommended asset locations are:

- Sample video: `.local/samples/overhead_clear.mp4`
- Pose model: `.local/models/pose_landmarker_full.task`

Explicitly provide their paths for asset-dependent tests or development runs:

```powershell
$env:FORMCHECK_SAMPLE_VIDEO = (Resolve-Path '.local/samples/overhead_clear.mp4').Path
$env:MEDIAPIPE_POSE_MODEL_PATH = (Resolve-Path '.local/models/pose_landmarker_full.task').Path
```

`FORMCHECK_SAMPLE_VIDEO` must identify a readable, consented participant video.
Record participant permission, permitted use, retention/deletion requirements,
and any redistribution restrictions privately alongside the asset. Do not commit
videos, frames, extracted pose data, or other participant-derived artifacts.

`MEDIAPIPE_POSE_MODEL_PATH` must identify a separately obtained Pose Landmarker
model. Check its license and permitted use before downloading or using it. Keep
the source URL, model name/version, download date, license, and SHA-256 hash in a
local provenance record. Do not commit model binaries or restricted assets.

Assets are never downloaded implicitly. The developer supplies both files and
explicit paths; missing or invalid paths cause the relevant asset tests to skip
with setup guidance. Synthetic tests require neither asset. Later end-to-end
tests require both variables and FFmpeg/ffprobe.
