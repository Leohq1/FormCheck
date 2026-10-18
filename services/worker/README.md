# Analysis worker

Integration owners: Persons 2, 3, and 4.

Person 2 owns the durable worker framework, queue integration, job retries, cancellation, progress persistence, and storage abstraction. Person 3 owns analysis-stage logic under `services/worker/analysis/`. Person 4 owns coaching-stage logic under `services/worker/coaching/`.

The worker runs video inspection and normalization, pose estimation, phase detection, feature extraction, rule evaluation, retrieval, and feedback generation. Approved stage inputs and outputs use `packages/contracts`. Before `analysis-findings.schema.json` is approved by both groups, Person 3 uses an internal model marked `schema_version: "0-draft"`; it is not an integration contract.
