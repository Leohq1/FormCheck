# Provisional analysis pipeline

This package composes video, pose, biomechanics, and rule stages behind provisional ports. It is a development pipeline, not the Dramatiq worker in `services/formcheck/worker/`.

The port signatures in `formcheck_analysis/ports.py` are marked provisional and need Person 2's review before production adapters are added. Analysis code does not import Redis, the database, or object storage.

## Setup

From the repository root, with Python 3.12:

```text
uv sync --locked --all-groups
uv run --locked pytest packages/video/tests packages/pose/tests packages/biomechanics/tests packages/rules/tests services/worker/analysis/tests -ra
```

FFmpeg and ffprobe are required for real normalization. Synthetic tests do not need them.

Optional local assets, never committed:

```text
FORMCHECK_SAMPLE_VIDEO=.local/samples/clear/overhead_clear.mov
MEDIAPIPE_POSE_MODEL_PATH=.local/models/pose_landmarker_full.task
```

Tests marked `assets` skip when those variables are unset or do not point to a file. The skip reason names each missing requirement.

## Development command

```text
uv run formcheck-analyze --analysis-id <uuid> --source <path> --handedness right --view rear_three_quarter
uv run formcheck-analyze --analysis-id <uuid> --source <path> --handedness right --view rear_three_quarter --development-diagnostics
```

Production JSON omits `diagnostics`. `--development-diagnostics` may include a disabled `would_trigger` evaluation. That is not a technique finding.

## Current limitation

`clear.low_arm_extension.v1` is not calibrated. Public `findings` stay empty. The UI says "No supported fault detected." Enabling the rule is future validation work and requires coach-labeled evidence. This README does not claim the sample-video flow has been run.

Local Docker Compose is configured in `infra/local` and was not started in the environment that added this pipeline.
