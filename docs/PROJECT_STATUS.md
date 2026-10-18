# Project status after the four-workstream merge

Date: 2026-10-17. Branch: `main` at `c521915` (`merge: add person 3 analysis workspace to main`). This file describes that tree plus the uncommitted consistency fixes in the working copy. The four handoffs below it are snapshots from before this merge and disagree with each other.

## Completed without an OpenAI key

The arm-extension feature, the disabled `clear.low_arm_extension.v1` rule, and the production findings assembler are implemented. A triggering measurement stays in diagnostics and does not become a finding. Local 1536-d vectors use model id `local-bow-1536` and are stored on the seven coaching chunks. Retrieval mixes those vectors with the existing keyword score. The worker cites the approved corpus for a completed clear, and smash or drop ends inconclusive because those strokes are not calibrated. The browser normalizes a contract result into the screen it already renders. The hosted generator calls the API only when `OPENAI_API_KEY` is present and otherwise uses the template.

Still outside this tree: FFmpeg normalization, the MediaPipe model file, coach-labeled video, and enabling the clear rule. Those need assets and a measured precision of at least 0.80. `uv` is not installed here, so the locked MediaPipe environment was not executed.

## Where each workstream stands

| Workstream | On this tree | Still open |
| --- | --- | --- |
| Person 1, frontend | React upload, wait, and result screens. The HTTP client maps a contract result onto the existing screen. | Vitest did not start on Node v20.16.0. |
| Person 2, platform | FastAPI app, worker, auth, idempotency, and contract validation. Completed clears get corpus feedback. Smash and drop return inconclusive. | The full Compose stack is described in `infra/local/docker-compose.yml` and has not been rebuilt in this session. |
| Person 3, analysis | Elbow-angle feature, disabled clear rule, and a findings assembler that omits diagnostics. | No FFmpeg or MediaPipe adapter yet. The rule stays disabled. |
| Person 4, RAG | Approved corpus, local vectors, mixed retrieval, template fallback, worker coaching, and eval metric tests. | Hosted generation waits for `OPENAI_API_KEY`. |

## What was checked

- `packages/rag/tests`: 22 passed.
- `services/tests`: 22 passed.
- `packages/contracts/validate_examples.py`: every example matched its schema, and the failed/completed/inconclusive error rules rejected the invalid cases.
- `npx tsc -b` in `apps/web`: passed.
- `docker compose -f infra/local/docker-compose.yml config`: passed.
- Person 3 package imports: succeeded.
- `npm test` in `apps/web`: did not start. Vitest's Rolldown binding looked for `@rolldown/binding-wasm32-wasi` under Node v20.16.0. The app's own engine range asks for Node `^20.19.0 || ^22.12.0 || >=24.0.0`. Typecheck still covered the upload change.

## Fixes in the working copy

The merge that brought Person 4 onto `main` kept the Postgres-only Compose file and dropped Person 2's Redis, S3-compatible store, API, and worker. `infra/local/docker-compose.yml` is the platform stack again. Postgres stays on image `pgvector/pgvector:pg16`, container `formcheck-postgres`, and volume `formcheck-pgvector`, and still mounts `infra/local/init` so a new volume creates the coaching tables.

The upload form sends stroke id `clear`. Jobs, findings, and the corpus use `overhead_clear`. `CreateAnalysisRequest` now accepts `clear` and stores `overhead_clear`. `smash` and `drop` still fail validation, and the upload form tells the user to choose Clear. The JSON Schema enum was not widened.

Retrieval treats frontend stroke id `clear` as `overhead_clear`. Findings accept severity words from all three current vocabularies: `minor|moderate|major`, `low|medium|high`, and `low|moderate|high`. The stored contract enum is still `minor|moderate|major`. GET result can still project those words to the interim frontend labels.

## Still inconsistent

These are real seams. They are recorded here so the next change does not pick one silently.

1. Stroke ids. Prose and the upload form say `clear`, `smash`, and `drop`. `packages/contracts`, the API job, Person 3, and the RAG corpus say `overhead_clear` only. Smash and drop have no rule, no finding schema value, and no approved clear-equivalent analysis path.
2. Severity words. The contract is `minor|moderate|major`. The frontend fixtures use `low|medium|high`. Older RAG fixtures use `low|moderate|high`. The API shim and the RAG parser tolerate the mix. One stored enum is still the right end state.
3. Findings version. Shared examples still use `schema_version: "0-draft"`. ADR 0001 says ratified messages use `"1"`, and its reviewer table is filled. Person 3 has not emitted production findings against that schema.
4. Result shape. The frontend still reads `recommendations`, string `evidence`, and error `message`. The contract result uses `feedback.tips`, structured evidence, and `safe_message`. `FORMCHECK_INTERIM_RESULT_SHIM` covers the demo path.
5. Two ways to reach Postgres. The coaching tables were created in the existing volume. Person 2's Alembic migration creates the platform tables. A volume that already has data does not rerun `init/`. Bringing the API up against this volume still needs that migration.
6. Person 4's handoff says this checkout is only PR #1. That is no longer true. `docs/HANDOFF_1.md` says Person 2 and Person 3 are absent from `main`. That is no longer true. `docs/HANDOFF_3.md` says the analysis branch and `main` have not been combined. That merge is `c521915`.

## Handoffs

| File | Use it for |
| --- | --- |
| `docs/HANDOFF_1.md` | Person 1's frontend history and the interim UI shape. Ignore its claim that analysis and the API are missing from `main`. |
| `docs/HANDOFF_PERSON2.md` | Platform routes, Compose services, and the contract file list. |
| `docs/HANDOFF_3.md` | Person 3 session plan, the disabled clear rule, and the normalized-video keys. Ignore the branch-divergence warning. |
| `docs/HANDOFF_PERSON_4.md` | RAG boundaries and the severity/stroke mismatch. Ignore the checkout description. The corpus has since moved past the synthetic fixtures. |
