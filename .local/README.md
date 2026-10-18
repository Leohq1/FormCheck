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

The root uv configuration excludes MediaPipe 1.1.1's transitive
`opencv-contrib-python` dependency so the explicit `opencv-python-headless`
dependency is the sole provider of `cv2`. This uses uv's supported
[dependency exclusion](https://docs.astral.sh/uv/concepts/resolution/#dependency-exclusions)
and is scoped to the reviewed MediaPipe version. The environment test checks
installed distribution records to prevent competing `cv2` providers.

If updating an environment created before this exclusion, repair shared files
while removing the old contrib distribution:

```powershell
uv sync --locked --all-groups --reinstall-package opencv-python-headless
```

This deliberately substitutes headless OpenCV for MediaPipe's declared contrib
distribution. Task 1 verifies dependency imports, not Pose Landmarker inference;
Task 4 must validate real inference with an explicitly supplied model and
synthetic video to establish whether the adapter needs any contrib-only APIs.
Review the exclusion and rerun those checks when upgrading MediaPipe. Use the
documented uv workflow so this project-level exclusion is respected.

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
