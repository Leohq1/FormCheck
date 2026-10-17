# FormCheck

FormCheck is a web application for asynchronous badminton movement analysis. The MVP accepts one overhead-clear video, extracts pose information with MediaPipe, applies rule-based technique checks, and produces coaching feedback grounded in curated sources.

## Architecture

The project is a modular monolith: one repository with clear internal module boundaries and multiple runtime processes.

```text
Browser -> API -> object storage
              -> job queue -> analysis worker
                              -> pose and quality checks
                              -> phases, features, and rules
                              -> coaching retrieval and generation
Browser <- API <- PostgreSQL
```

## Repository layout

```text
apps/web/                 React and TypeScript web client
services/api/             FastAPI endpoints and orchestration
services/worker/          Background analysis worker
packages/contracts/       Shared JSON schemas and examples
packages/video/           Video inspection and normalization
packages/pose/            PoseEstimator interface and MediaPipe adapter
packages/biomechanics/    Phases, normalization, and features
packages/rules/           Rule-based fault detection
packages/rag/             Corpus ingestion, retrieval, and feedback
corpus/manifests/         Source metadata and rights records
evals/                    Evaluation datasets, metrics, and reports
infra/local/              Local containers and configuration
tests/                    Cross-module and end-to-end tests
docs/                     Architecture decisions and runbooks
```

## Team ownership

- Person 1: `apps/web`
- Person 2: `services/api`, worker orchestration, database, and `infra/local`
- Person 3: `packages/video`, `packages/pose`, `packages/biomechanics`, and `packages/rules`
- Person 4: `packages/rag`, `corpus/manifests`, and evaluation coordination

Shared contracts require review from at least one member of each group before they change.

## Initial integration target

```text
Real frontend -> real API -> stored upload -> fake worker -> sample result -> real result screen
```

In parallel, the analysis group should demonstrate:

```text
Sample video -> MediaPipe -> PoseSequence
Sample finding -> coaching retrieval -> cited passages
```

See [contracts](packages/contracts/README.md) for the integration boundary and [contributing guidance](CONTRIBUTING.md) for working agreements.
