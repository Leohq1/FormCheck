# Analysis worker

Integration owners: Persons 2, 3, and 4.

Person 2 owns durable orchestration in `formcheck/worker/` (Dramatiq broker, fake pipeline, deletion outbox processing).

- `formcheck.worker.tasks.run_fake_analysis` — accepts a full `AnalysisJob` dict, emits `analysis-progress` events, persists `analysis-result` fixtures validated against `packages/contracts`.
- `formcheck.worker.tasks.process_deletion` — removes `analyses/{id}/` objects from MinIO.

Person 3's provisional pipeline lives in `services/worker/analysis/`. `run_fake_analysis` uses it for an overhead clear whose filename is not an `inconclusive`, `failed`, or `expired` fixture. Smash and drop stay on the scripted inconclusive result. Public findings stay empty until a technique rule is calibrated. Gemini coaching runs only when findings are already present.

The worker image installs FFmpeg and reads the pose model from `MEDIAPIPE_POSE_MODEL_PATH` (`/models/pose_landmarker_full.task` in Compose). A missing tool or model persists `ANALYSIS_ASSETS_MISSING` instead of a sample finding.

Run via Docker Compose (`worker` service) or:

```bash
cd services
set PYTHONPATH=.
dramatiq formcheck.worker.tasks --processes 1 --threads 2
```
