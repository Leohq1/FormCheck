# Analysis worker

Integration owners: Persons 2, 3, and 4.

Person 2 owns durable orchestration in `formcheck/worker/` (Dramatiq broker, fake pipeline, deletion outbox processing).

- `formcheck.worker.tasks.run_fake_analysis` — accepts a full `AnalysisJob` dict, emits `analysis-progress` events, persists `analysis-result` fixtures validated against `packages/contracts`.
- `formcheck.worker.tasks.process_deletion` — removes `analyses/{id}/` objects from MinIO.

Person 3 analysis stages and Person 4 coaching stages will replace the fake pipeline without changing the public HTTP API.

Run via Docker Compose (`worker` service) or:

```bash
cd services
set PYTHONPATH=.
dramatiq formcheck.worker.tasks --processes 1 --threads 2
```
