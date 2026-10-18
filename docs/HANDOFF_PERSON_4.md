# FormCheck — Unified Project Handoff

**Document purpose:** One source of truth so a single replacement agent can continue all four person-roles without the original chats.

**Written:** 2026-10-17 evening PDT (session clock), after reading this workspace, GitHub, and the earlier handoff.

**Remote:** `https://github.com/Leohq1/FormCheck`

**Verified `origin/main` tip:** `f8a71239f706ba2889b440922a78662db7583fa4`  
Message: `Merge pull request #7 from Leohq1/docs/project-handoff`

**This workspace checkout:** branch `rag/corpus-retrieval` at `47e4b2b` (`Merge pull request #1`). That commit is only the frontend MVP merge. It does **not** contain later `main` commits (multi-stroke UI, contracts, platform, or `docs/HANDOFF.md`). Person 4’s RAG code and a second Compose file are **uncommitted** on top of that old commit.

> Do not treat `docs/HANDOFF.md` on `origin/main` as current. It was written when `main` was still `d8290b7` (after PR #5) and it says Person 2 and Person 4 have no implementation. Both statements are now false. PR #6 merged onto `main` immediately before PR #7, so the published handoff and the platform code landed together and contradict each other.

Anything not verified by a file read, a test run in this session, or a GitHub API/raw fetch is marked **Unverified** or **Claimed**.

---

## 1. Executive Summary

FormCheck is a modular-monolith MVP that accepts one short badminton clip, estimates pose with MediaPipe, applies deterministic rules, and returns short coaching text grounded in a curated corpus. There are no accounts. Access is an analysis ID plus a high-entropy capability token. Default retention is 24 hours.

Four people were building in parallel. A replacement agent now owns all four lanes, but the code is **not in one tree**:

| Lane | Where the real work is | What a new agent can run today |
|---|---|---|
| Person 1, frontend | `origin/main` `apps/web/` (PRs #1, #2, #5) | Mock UI. This checkout’s `apps/web` is the older overhead-clear-only PR #1 app. |
| Person 2, platform | `origin/main` `services/formcheck/` and `infra/local/docker-compose.yml` (PR #6). Hardening is open PR #8, not merged. | API, fake worker, Postgres, Redis, S3-compatible storage. **Not present in this checkout.** |
| Person 3, analysis | `origin/analysis/mediapipe-adapter` (PR #3). Open PR #9 proposes merging that branch to `main`. | Python 3.12/uv skeletons only. No pose inference, no rules. |
| Person 4, RAG | **Uncommitted** on local `rag/corpus-retrieval` | Fixture retrieval and template feedback. 17 pytest tests passed in the Person 4 session. Not on GitHub. |

Immediate priorities:

1. `git fetch` and understand that this working tree is behind `origin/main`. Do not commit the local Compose file over Person 2’s stack.
2. Rebase or otherwise preserve Person 4’s uncommitted `packages/rag` work onto current `main` without deleting `services/formcheck`.
3. Treat three different severity vocabularies as a real integration bug (section 7).
4. Keep `clear.low_arm_extension.v1` disabled. Empty `findings` must not produce coaching tips.
5. Do not edit design docs until a human agrees. That rule came from Person 1’s sessions and is recorded in the older handoff.

---

## 2. Project Overview

### 2.1 What the product must do

Authoritative product text lives in `docs/TEAM_DECISIONS_AND_RESPONSIBILITIES.md`, `docs/ImplementationPlan.md`, and `docs/BADMINTON_MOVEMENT_ASSISTANT_TECHNICAL_DESIGN.md`. On `origin/main` those docs were updated by PR #2 to talk about clear, smash, and drop. This checkout’s copies of those docs are older if they were not modified locally. **Unverified in this checkout’s working tree:** whether the local doc files still say overhead-clear only. Git status at handoff time did not list them as modified, and this branch is PR #1, so they are the pre-PR-#2 versions.

Agreed MVP behavior:

- Web upload of one short clip (MP4 or MOV, max 100 MB, max 30 seconds, 30–120 fps).
- Async processing. The browser polls status. It never calls the worker, database, or model provider.
- MediaPipe is the only pose estimator.
- A rule engine creates technique findings. A language model must not.
- Retrieval-augmented coaching cites approved passages.
- No accounts, no saved progress, no live camera, no multi-camera, no professional-similarity score.
- Raw video retention defaults to 24 hours. The server stores a hash of the capability token, not the token.

The first end-to-end target in the team doc is still: one controlled clip, one trustworthy feature, one rule finding, one retrieved passage, one result on screen. The first feature/rule pair is `dominant_elbow_angle_at_max_wrist_height_deg` and disabled candidate `clear.low_arm_extension.v1`.

### 2.2 Architecture

```text
Browser (Person 1)
  HTTP /api/v1
API (Person 2) → object storage
              → Redis / Dramatiq
                    AnalysisJob
Worker (Person 2 orchestration)
  → analysis stages (Person 3) → AnalysisFindings
  → coaching stages (Person 4) → feedback inside AnalysisResult
API persists the result
Browser polls and renders it
```

### 2.3 Stack

| Area | Decision | Where it actually exists |
|---|---|---|
| Frontend | React 19, TypeScript, Vite 8, React Router 7, TanStack Query 5, Tailwind 4 | `apps/web` on `main` and, older, in this checkout |
| Frontend tests | Vitest, Testing Library, Playwright | `apps/web` |
| API | Python 3.12, FastAPI, Pydantic | `origin/main` `services/formcheck/` |
| Worker | Dramatiq, fake pipeline today | `origin/main` `services/formcheck/worker/` |
| Contracts | JSON Schema draft 2020-12 | `origin/main` `packages/contracts/` |
| Analysis packages | uv, NumPy, Pydantic, MediaPipe, headless OpenCV, SciPy | `origin/analysis/mediapipe-adapter` only |
| RAG | Pydantic package `formcheck-rag`, pytest | Uncommitted `packages/rag/` |
| Database | PostgreSQL 16 + pgvector 0.8.7 | Person 2 Compose on `main`; a second local-only Compose in this working tree |
| Queue | Redis 7 | Person 2 Compose on `main` |
| Object storage | `pgsty/silo` and `pgsty/mc`, not `minio/minio` | Person 2 Compose on `main`. Official MinIO Hub images were removed in 2026 (stated in that Compose file). |

### 2.4 Ownership

| Person | GitHub login | Confidence | Paths |
|---|---|---|---|
| 1 Frontend | `mzliu05` | High. Authored PRs #1, #2, #5, #7. | `apps/web/` |
| 2 Platform | `ZZeeZZ1127` | High. Authored PRs #4, #6, #8. | `services/formcheck/`, `services/api` README, `infra/local` on `main`, `packages/contracts` |
| 3 Analysis | `Leohq1` | High. Authored PRs #3 and #9. | `packages/video`, `pose`, `biomechanics`, `rules`, `services/worker/analysis`, `evals/pose`, `evals/rules` |
| 4 RAG | `junyu101` | The human in this Person 4 session. No RAG PR exists. | `packages/rag`, `corpus/manifests`, `evals/retrieval`, `evals/generation`, `evals/system`, future `services/worker/coaching` |

Group A is Persons 1 and 2. Group B is Persons 3 and 4. Shared contract changes need one reviewer from each group.

### 2.5 Status vocabulary

```text
created, uploading, queued, preprocessing, pose_estimation,
phase_detection, rule_evaluation, retrieval, generating,
completed, inconclusive, failed, cancelled, expired
```

The frontend also treats `deleted` as a terminal UI state after DELETE. `inconclusive` means the system worked but could not support a technique finding. `failed` means a technical failure.

---

## 3. Agent-by-Agent Work Summary

### 3.1 Person 1 — Frontend

**On `origin/main` (not fully present in this checkout):**

- PR #1: React/Vite app, Fierce landing, calm inner pages, mock `AnalysisApi`, Vitest, Playwright happy path.
- PR #2: stroke dropdown Clear / Smash / Drop and stroke ids `clear | smash | drop`. Also rewrote product docs on that branch. **This checkout still has `StrokeId = 'overhead_clear'` in `apps/web/src/sports/config.ts`.**
- PR #5: shuttlecock logo in the header and favicon. `LogoMark` is cited by the older handoff at `apps/web/src/components/LogoMark.tsx`. **Not verified in this checkout** because this branch predates PR #5.

**How the app is structured (true of both trees unless noted):**

- `apps/web/src/App.tsx` routes `/`, `/upload`, `/analyses/:analysisId`.
- `src/api/client.ts` defines `AnalysisApi`: `createAnalysis`, `completeUpload`, `getAnalysis`, `getResult`, `deleteAnalysis`.
- `src/api/index.ts` uses the mock client unless `VITE_API_BASE_URL` is set, then `httpClient.ts`.
- `src/api/mockClient.ts` walks stages about every 350 ms (timing from the older handoff; **not re-read this session**).
- `src/api/mockOutcome.ts` maps filenames containing `inconclusive`, `failed`, or `expired` to those outcomes.
- `src/api/session.ts` stores the capability token in `sessionStorage`.
- Results UI: `src/components/ResultsPanel.tsx`, `TipsList.tsx`, `StatusBanner.tsx`, `VideoDropzone.tsx`.

**Interim frontend result shape** in this checkout’s `apps/web/src/api/types.ts`:

- Severity `low | medium | high`.
- Finding evidence is a **string**.
- Coaching is `recommendations[]` with `title`, `body`, `exercise`, `citation_ids`, plus top-level `citations` and `limitations`.
- Quality is `acceptable | borderline | poor` plus `notes[]`.
- Errors use `message`, `retry_may_work`, `recording_remediation`.

**Still open for Person 1:** remap the UI to the ratified contract (section 7), cover terminal states in Playwright, and only then point `VITE_API_BASE_URL` at `http://localhost:8000`. PR #6 says a server shim currently projects the ratified result back into this interim shape so the old UI does not break. That shim is **claimed in the PR #6 body** (`FORMCHECK_INTERIM_RESULT_SHIM=1` default). The file `services/formcheck/compat.py` exists on `main`. Its exact behavior was **not read** for this handoff.

**Binding UI preferences from Person 1 sessions** (recorded in `docs/HANDOFF.md` on `main`; this agent did not re-watch those chats):

- Bold landing, calm upload and results.
- Fierce palette `#242E2D`, `#D9D9D7`, `#EFEFED`, `#AE3121`, `#691F15`, `#A8A8A5`.
- Fonts Cormorant Garamond and DM Sans.
- Use the user-supplied shuttlecock mark, not generated logo concepts.
- Discuss design-doc edits with the human before changing them.

Abandoned UI work in an earlier local chat (`ccac8b3f-…`): a studio color-swap preview was built and then scrapped because it was not the product. Do not restore it.

### 3.2 Person 2 — Platform and contracts

**Merged to `origin/main`:**

- PR #4, contracts and `docs/adr/0001-shared-analysis-contracts.md`. Validator: `packages/contracts/validate_examples.py`.
- PR #6, FastAPI app and fake worker realigned to those contracts.

**Files on `origin/main` (tree listing of `f8a7123`, not checked out here):**

```text
services/formcheck/api/main.py
services/formcheck/api/routes.py
services/formcheck/api/deps.py
services/formcheck/auth.py
services/formcheck/compat.py
services/formcheck/config.py
services/formcheck/contract_validate.py
services/formcheck/db.py
services/formcheck/models.py
services/formcheck/schemas.py
services/formcheck/storage.py
services/formcheck/worker/broker.py
services/formcheck/worker/fixtures.py
services/formcheck/worker/tasks.py
services/Dockerfile.api
services/Dockerfile.worker
services/requirements.txt
services/pytest.ini
services/tests/test_auth.py
services/tests/test_schemas_align.py
services/tests/test_storage_keys.py
infra/local/docker-compose.yml
infra/local/.env.example
infra/local/README.md
```

**Compose services on `main`:** `postgres` (`pgvector/pgvector:pg16`, port 5432), `redis` (6379), `minio` (`pgsty/silo`, ports 9000 and 9001), `minio-init` (`pgsty/mc`), `api` (8000), `worker` (Dramatiq fake pipeline). Database, user, and password default to `formcheck`. MinIO root password default in the Compose file is `formchecksecret`. API docs are documented as `http://localhost:8000/docs`.

**Claimed in PR #6, not re-run here:** `cd services && pytest tests -q` passed 10 tests. `complete-upload` enqueues an `AnalysisJob`. GET result validates against `analysis-result.schema.json`. Filename tokens `inconclusive`, `failed`, and `expired` still force fake-worker outcomes.

**Open PR #8** (`platform/lifecycle-hardening` → `platform/contract-realignment`): Alembic, `Idempotency-Key`, retention sweeper, `POST /analyses/{id}/cancel`, and a claim of 21 API tests. **Not merged.** Do not describe those behaviors as already on `main`.

**Person 2 comment on PR #3 (review text, not a merged code change):** analysis packages must stay infrastructure-neutral (no MinIO, Redis, Dramatiq, or retention policy). Person 3 proposes ports in Session 9; Person 2 writes adapters. Logical keys:

```text
analyses/{analysis_id}/source/{filename}
analyses/{analysis_id}/normalized/video.mp4
analyses/{analysis_id}/normalized/timestamps.json
```

`platform/job-lifecycle` was an early empty branch. Later platform work used `platform/contract-realignment` and `platform/lifecycle-hardening`.

### 3.3 Person 3 — Analysis

PR #3 merged into `analysis/mediapipe-adapter`, not `main`. Open PR #9 asks to merge `analysis/mediapipe-adapter` into `main`. Until that merges, `main` has README stubs under `packages/pose` and friends, not the Python packages.

Session 1, verified by reading `pyproject.toml` and `packages/pose/docs/person3-session-1-handoff.md` on branch `analysis/session-1-python-scaffold`:

- Project name `formcheck-analysis` `0.1.0`, Python `>=3.12,<3.13`, uv lock, 39 packages.
- Importable skeletons: `formcheck_video`, `formcheck_pose`, `formcheck_biomechanics`, `formcheck_rules`, `formcheck_analysis`.
- MediaPipe `>=1.1.1,<2` must not install `opencv-contrib-python`. The lock excludes that dependency for MediaPipe 1.1.1. `opencv-python-headless` is the only `cv2` provider. A regression test checks installed distribution metadata.
- setuptools discovers only those five packages. `packages/rag` is not included.
- Docs on that branch: `packages/pose/docs/person3-session-1-handoff.md`, `person3-analysis-pipeline-design.md`, `person3-analysis-pipeline-implementation-plan.md`.
- Claimed verification: `uv run --locked pytest -v` 2 passed, Ruff and mypy passed. **Not re-run in this workspace.**

Sessions 2–10 are not done: domain models, FFmpeg normalize, MediaPipe inference, quality, phases, features, rules, worker ports, pose/rule evals.

Rules that later sessions must keep:

- `clear.low_arm_extension.v1` stays `enabled: false` until held-out coach precision is at least 0.80.
- `would_trigger` is a development diagnostic, not a finding. Production serialization omits diagnostics.
- Internal output uses `schema_version: "0-draft"` until both groups accept the shared findings schema.
- Do not infer handedness or view. Those come from Person 2’s `AnalysisJob`.
- Do not treat MediaPipe relative z as metric depth.
- Sample video and the Pose Landmarker `.task` file stay outside git:

```text
FORMCHECK_SAMPLE_VIDEO=.local/samples/overhead_clear.mp4
MEDIAPIPE_POSE_MODEL_PATH=.local/models/pose_landmarker_full.task
```

### 3.4 Person 4 — RAG and evaluation

Implemented only in this working tree. Nothing has been committed or pushed. Last test run in the Person 4 session: **17 passed**.

Package `packages/rag/` (`formcheck-rag` 0.1.0):

| Module | Behavior |
|---|---|
| `src/formcheck_rag/manifest.py` | `load_manifest` requires a non-empty `license` and `allowed_use`. |
| `src/formcheck_rag/chunking.py` | Splits on Markdown headings. A section over 500 words is windowed at 450 words with 40 words of overlap. Sections are never merged. |
| `src/formcheck_rag/retrieval.py` | `InMemoryIndex` keeps only `review_status == approved`, matching stroke tag, and overlapping fault tags. Rank is token overlap, not vectors. Returns at most 6 chunks. |
| `src/formcheck_rag/findings.py` | Pydantic model. `extra = ignore`, so `diagnostics` and `would_trigger` are dropped. Severity pattern is `low\|moderate\|high`. Default `schema_version` is `0-draft`. |
| `src/formcheck_rag/feedback.py` | `TemplateFeedbackGenerator` writes at most three tips, only for findings that share a fault or phase tag with a retrieved chunk. `validate_feedback` rejects unknown finding ids and citations that were not retrieved. Model id is `template-fallback`, `prompt_version` is `1`. |

Fixtures under `packages/rag/tests/fixtures/`:

- `findings.json` — one moderate finding, rule `clear.low_arm_extension.v1`, evidence `dominant_elbow_angle_at_max_wrist_height_deg` = 128 `deg`.
- `findings-empty.json` — usable quality, empty findings, no tips.
- `findings-diagnostics.json` — low angle plus `would_trigger: true`, still no tips.
- `findings-multiple.json` — arm extension plus fixture-only `clear.limited_trunk_rotation.v1` with no corpus passage, so only the first becomes a tip.
- `findings-low-confidence.json` — confidence 0.42 is kept and a limitation says it is below 0.70.
- `findings-inconclusive.json`, `findings-uncertain-contact.json`, `findings-unsupported-view.json`.

The corpus text in those fixtures is synthetic and labeled `license: project-test`. It is not a coaching authority. `corpus/manifests/` is still only a README. `evals/` is still only a README. There is no `services/worker/coaching/` package.

**Not built:** rights-approved sources, OpenAI embeddings, pgvector queries from Python, GPT-6 Luna adapter, cost logging, Ollama, eval harness, worker stages.

---

## 4. Consolidated Implementation Details

### 4.1 Two checkouts

| | This workspace | `origin/main` @ `f8a7123` |
|---|---|---|
| Branch | `rag/corpus-retrieval` | `main` |
| Commit | `47e4b2b` (PR #1 only) | PR #7 merge, which contains PR #6 |
| Frontend strokes | `overhead_clear` only | `clear`, `smash`, `drop` (PR #2) |
| Contracts | README only | Six schemas, examples, validator, ADR 0001 |
| API | README only | `services/formcheck` |
| RAG | Uncommitted package | README only |
| Compose | Uncommitted pgvector-only file | Full stack, no coaching tables |

Rebasing this branch onto `main` will conflict at least in `infra/local/README.md` and `infra/local/docker-compose.yml`.

### 4.2 Ratified contracts on `main`

`packages/contracts/common.schema.json` was fetched from `main` and read:

- `stroke.type` enum is only `overhead_clear`.
- `quality.overall` is a number from 0 to 1. `warnings` is an array of strings. Warning codes are **not** enumerated in the schema.
- Finding severity enum is `minor | moderate | major`.
- Evidence items require `feature`, numeric `value`, and `unit`.
- Findings require `retrieval_tags`.

The older handoff, which compared the other schema files, also states: result coaching lives under `feedback` (`summary`, `tips`, `limitations`, `model`, `prompt_version`); tips and findings `maxItems` 3; inconclusive, failed, expired, and cancelled results require `error`; completed results require `error: null`. Error fields are `safe_message`, `retryable`, `remediation[]`. **Those details were not re-fetched from each schema file in this session.** Re-read `analysis-result.schema.json` and `analysis-error.schema.json` before coding against them.

ADR 0001 reviewer table was still `_TBD_` when the previous handoff was written. **Not re-checked after PR #6**, which claimed it filled the table. Open the ADR before assuming sign-off is done.

### 4.3 Person 4 code versus the contract

Local `Finding.severity` accepts `low | moderate | high`. The contract accepts `minor | moderate | major`. The frontend in this checkout accepts `low | medium | high`. The frontend on `main` was not re-read; PR #2 did not claim a severity remap.

Local feedback tips use `finding_id`, `explanation`, `practice_cue`, and citation objects `{source_id, chunk_id, locator}`. The contract’s `feedback.tips` shape must be checked in `analysis-result.schema.json` before wiring the worker. Do not assume they match.

`TemplateFeedbackGenerator` does not read `features`. A low elbow angle with an empty `findings` list produces:

```text
No supported technique fault was found for this overhead clear.
```

Quality warnings the template turns into sentences: `contact_uncertain`, `uncertain_contact`, `unsupported_view`, `low_pose_confidence`, `body_not_fully_visible`, `inconclusive_pose`. `unsupported_view` changes the summary to “This camera view did not support a technique finding.” These warning strings are a Person 4 proposal. They are not in the JSON Schema enum.

### 4.4 Local database that is not Person 2’s database

Uncommitted `infra/local/docker-compose.yml` starts one container, `formcheck-postgres`, image `pgvector/pgvector:pg16`, host port 5432, user/password/database `formcheck`, named volume `formcheck-pgvector`. Init script `infra/local/init/001-coaching.sql` creates extension `vector`, tables `coaching_source` and `coaching_chunk`, and an HNSW index on `embedding vector(1536)` using `vector_cosine_ops`.

Verified in the Person 4 session after `docker compose up -d`:

- Container healthy.
- `vector` extension version 0.8.7.
- Both tables present.
- `'[1,2,3]'::vector <=> '[3,1,2]'` returned a cosine distance.

The Python retriever never connects to this database. Embeddings are null. Opening `http://localhost:5432` in a browser logs `invalid length of startup packet` because Postgres is not HTTP. That log line was observed and is not a crash.

Person 2’s Compose on `main` also binds port 5432 and uses a different volume (`postgres-data`) and **does not** mount `001-coaching.sql`. Running both Compose projects at once will fail on the port. Prefer Person 2’s Compose after rebase, and add the coaching tables with a migration Person 2 owns rather than a second Compose file.

### 4.5 Integration boundaries that must stay

- Person 1 calls only the HTTP API.
- Person 3 does not import storage, queue, or database clients. Ports are proposed later in `services/worker/analysis/ports.py` (**file does not exist yet**).
- Person 4 creates tips only from `findings`.
- Person 2 is the only component that shows results to the browser.
- Do not send video, frames, pose trajectories, capability tokens, or object URLs to a model provider.

---

## 5. Decision Log

| Decision | Why | Alternative rejected | Status |
|---|---|---|---|
| Modular monolith, four owners | Parallel work with schema borders | Microservices | Established in team docs |
| MediaPipe only | One estimator for the MVP | YOLO or MMPose beside it | Established |
| Rules own faults; the model only explains | Stops invented diagnoses | LLM watches the video | Established |
| No accounts; capability tokens | Smaller privacy surface | User accounts | Established |
| JSON Schema draft 2020-12 as the integration contract | Stop private TypeScript and Pydantic drift | Keep the frontend types as the contract | On `main` via PR #4. Frontend not remapped. |
| Severity `minor/moderate/major` in the contract | ADR 0001 | Frontend words as the contract | Contract on `main`. Person 4 local model still uses `low/moderate/high`. |
| `feedback` object on the result | Matches the implementation plan | Frontend `recommendations` | Contract on `main`. Local RAG emits a similar but unverified shape. |
| Object keys `analyses/{id}/source/{filename}` and `normalized/video.mp4` | ADR resolved an earlier flat-key conflict | `original` and `normalized.mp4` | Established in ADR and Person 2 Compose comments |
| uv + one headless OpenCV | MediaPipe 1.1.1 pulled `opencv-contrib-python` and the two distributions overwrite `cv2` | Install both | On the analysis branch |
| Person 3 PRs land on `analysis/mediapipe-adapter` first | Root Python config needs cross-group review | Merge Session 1 straight to `main` | PR #9 now proposes the merge to `main` and is **open** |
| First rule disabled until precision ≥ 0.80 | No coach labels yet | Enable a plausible biomechanics threshold | Established. Person 4 tests assume empty production findings. |
| `schema_version: "0-draft"` before shared-schema approval | Do not pretend fixtures are the contract | Call local models schema v1 | Person 3 and Person 4 agreed in this session. The findings schema file **does exist** on `main` from PR #4. Person 3 has not retargeted Session 2 onto it. |
| Template generator before a hosted model | Works with no API key and cannot invent citations | Call GPT immediately | Implemented locally only |
| In-memory keyword retrieval before pgvector | Docker was not installed when the package was written | Block on Postgres | Keyword index remains the code path. Postgres was added later and is not wired. |
| Person 4 Compose with coaching tables | Need a database before Person 2’s stack was on this branch | Wait for Person 2 | Now a conflict. Person 2’s Compose is the one on `main`. |
| `pgsty/silo` instead of MinIO | Official MinIO images left Docker Hub | Keep `minio/minio` | In Person 2 Compose on `main` |
| Synthetic test corpus | No rights-cleared manuals yet | Paste copyrighted coaching text | Fixtures only |
| Design-doc edits need a human yes | Person 1 stopped silent doc rewrites | Agents update docs whenever code changes | Process rule from the prior handoff |
| Fierce UI, shuttle logo | User rejected bland and experimental marks | Studio color-swap preview, generated logos | Shipped on `main` through PR #5. Studio preview was deleted locally. |

Abandoned:

- Dual OpenCV distributions.
- Using the language model to decide whether a fault exists.
- Runtime web search on the coaching path.
- Treating `would_trigger` or a raw feature value as a finding.
- Opening Postgres in a browser to “see localhost.”
- A second full product UI (the studio color-swap preview).

---

## 6. Current Project State

### Works, and where

- **`origin/main` frontend** (PRs #1, #2, #5): mock upload flow, multi-stroke copy, logo. **Not what `npm run dev` uses if you start it in this checkout.**
- **This checkout frontend:** mock flow for a single overhead clear. Routes and mock client exist. Logo from PR #5 does not.
- **`origin/main` platform:** Compose file and FastAPI/worker tree exist. Tests were claimed green in PR #6 (10) and PR #8 (21, unmerged). **Not run from this checkout.**
- **Analysis branch:** import skeletons and OpenCV guard. Inference not implemented.
- **This checkout RAG:** 17 unit tests passed in the Person 4 session against fixtures. Template citation checks pass. Database tables exist only if the local Compose project is the one that was started.

### Incomplete everywhere

- Real pose, phases, features, and enabled rules.
- Rights-approved corpus and embeddings.
- Hosted generator and eval reports.
- Frontend types equal to `packages/contracts`.
- Coaching worker stage.
- One stroke vocabulary shared by UI, job schema, and RAG fixtures.
- ADR reviewer names, unless PR #6 actually filled them (**unread**).

### Milestones

| Milestone | Status |
|---|---|
| A Contracts | Schemas on `main`. Stroke enum still `overhead_clear` while PR #2 docs/UI say three strokes. Sign-off table must be re-read. |
| B Platform vertical slice | Fake worker and API are on `main`, not in this checkout. Frontend remap and a live browser pass against `localhost:8000` are not done. |
| C Prototypes | Person 3 stopped after Session 1. Person 4 has fixture retrieval only. |
| D Group B integration | Not started. |
| E Replace fake worker | Not started. |

---

## 7. Known Issues and Risks

1. **This checkout is stale.** Implementing on `rag/corpus-retrieval` without rebasing will miss the API, contracts, and multi-stroke UI, and the local Compose file will fight `origin/main`.
2. **Three severity vocabularies:** contract `minor|moderate|major`, this frontend `low|medium|high`, Person 4 code `low|moderate|high`. A finding cannot cross all three without a mapping.
3. **Three stroke vocabularies:** contract and this checkout `overhead_clear`; `origin/main` frontend `clear|smash|drop`; Person 4 queries use `overhead_clear`.
4. **`docs/HANDOFF.md` on `main` is stale** about Person 2 and Person 4. Replacing it, or adding this file, is a docs change. Person 1’s rule says ask before editing design docs. This file was explicitly requested.
5. **Two Postgres Compose definitions, one port.** Local volume `formcheck-pgvector` has the coaching tables. Person 2’s volume `postgres-data` does not.
6. **Person 4 package is outside Person 3’s uv project.** After PR #9, adding RAG dependencies means a reviewed `uv lock` change, not a hand-edited lockfile, and not MediaPipe in the RAG group.
7. **OpenCV exclusion is version-scoped to MediaPipe 1.1.1.** An upgrade can silently bring `opencv-contrib-python` back. Re-run the sole-provider test. Imports do not prove Pose Landmarker inference.
8. **Empty findings are the expected production payload** until a coach labels data. Generating tips from features would violate the Person 3/4 agreement.
9. **No API key and no approved corpus.** Do not commit `.env` or copyrighted manuals.
10. **PR #8 is not merged.** Idempotency keys, Alembic, cancel, and the sweeper are proposed, not on `main`.
11. **Browser `localhost` with no port** hits nothing useful. The API, when the `main` stack is running, is port 8000. The Vite app is port 5173. Postgres is port 5432 and speaks its own protocol.
12. **`gh` is not installed** on this machine. GitHub inspection used the REST API and raw file URLs.

---

## 8. Remaining Tasks

### P0 — Make one tree

| ID | Task | Done when |
|---|---|---|
| P0.1 | Fetch `origin`. Inspect `main`, `analysis/mediapipe-adapter`, and `platform/lifecycle-hardening`. | The agent can name the SHAs and does not edit the stale checkout by accident. |
| P0.2 | Preserve uncommitted `packages/rag/**` and move it onto current `main` without taking Person 2’s Compose. | `packages/rag` tests still pass on a branch that contains `services/formcheck`. |
| P0.3 | Ask the human which stroke ids are canonical before changing schemas or design docs. | One enum is written down. |
| P0.4 | Map severity in one place. Do not silently change the contract or the UI. | Person 4’s model either matches `minor\|moderate\|major` or documents a single adapter. |

### P1 — Finish Milestone B on `main`

| ID | Task | Done when |
|---|---|---|
| P1.1 | `docker compose up --build` from `origin/main` `infra/local`. | `http://localhost:8000/docs` responds. |
| P1.2 | Run `services` pytest from that tree. | PR #6’s 10 tests pass locally, or failures are recorded. |
| P1.3 | Decide whether to merge PR #8. | Cancel, Alembic, and idempotency are either on `main` or explicitly deferred. |
| P1.4 | Remap `apps/web` types and fixtures to the contract, then turn off `FORMCHECK_INTERIM_RESULT_SHIM` only after the UI can read `feedback`. | Mock and HTTP fixtures validate. A browser upload against the fake worker completes. |

### P2 — Person 3 Sessions 2–4

| ID | Task | Done when |
|---|---|---|
| P2.1 | Follow `person3-analysis-pipeline-implementation-plan.md` Session 2 only. | `0-draft` models serialize, and tests fail before the code exists. |
| P2.2 | Do not enable `clear.low_arm_extension.v1`. | Production-shaped fixtures have `findings: []`. |
| P2.3 | Sessions 3–4: normalize video and run MediaPipe with the headless OpenCV provider. | A skipped test explains missing `FORMCHECK_SAMPLE_VIDEO` or model path. Inference is actually tried once assets exist. |

### P3 — Person 4 remainder

| ID | Task | Done when |
|---|---|---|
| P3.1 | 5–10 rights-approved sources in `corpus/manifests/`. Files themselves stay out of git unless the license allows them. | Every record has license, allowed use, reviewer, and content hash. |
| P3.2 | Load approved chunks into Postgres using Person 2’s database, with `vector(1536)`. | Pending rows are not returned. |
| P3.3 | Embed with `text-embedding-3-small` when an untracked API key exists. | Model id and corpus version are stored. Keyword rank still applies. At most 6 chunks. |
| P3.4 | GPT-6 Luna adapter: timeout, limited retries, schema validation, token-cost log. Template remains the fallback. | A provider failure still returns a cited or honestly empty result and does not fail the analysis. |
| P3.5 | `evals/retrieval`, `evals/generation`, `evals/system`. | Reports include Recall@5, citation validity, faithfulness, unsafe claims, latency, and cost. Coach labels can wait; the harness cannot. |
| P3.6 | After PR #9, register `formcheck_rag` in the uv project without MediaPipe. | `uv lock` is regenerated and reviewed. The lockfile is not hand-edited. |

### P4 — Integrate

| ID | Task | Done when |
|---|---|---|
| P4.1 | Person 3 Session 9 ports. Person 2 adapters. | Analysis packages still do not import Redis, Dramatiq, or object storage. |
| P4.2 | Worker stages `retrieval` and `generating` call Person 4. | Fake worker can be replaced without changing the public HTTP API. |
| P4.3 | Eval gates: rule precision ≥ 0.80 before enable; retrieval Recall@5 ≥ 0.90; citations 100%; faithfulness ≥ 95%; no critical unsafe output. | A report exists. The rule stays off if the report misses. |

---

## 9. Unified Execution Plan

1. Fetch and read `origin/main` `docs/adr/0001-shared-analysis-contracts.md`, `packages/contracts/analysis-result.schema.json`, and `services/formcheck/api/routes.py`. Do this on a new worktree, not by resetting this dirty branch.
2. Copy or commit the uncommitted `packages/rag` work onto a branch cut from current `main`. Leave Person 2’s `infra/local/docker-compose.yml` in place. Keep `001-coaching.sql` as a proposal for a Person 2 migration, not as a second running database, unless `main` is not running.
3. Ask the human the stroke-id question. Do not edit `docs/ImplementationPlan.md` or the technical design until they answer.
4. Align Person 4 severity with the contract in the RAG package and add a test that a `minor|moderate|major` payload is what the generator accepts if that is the ratified enum.
5. Run Person 2’s Compose and the frontend on `main` with `VITE_API_BASE_URL=http://localhost:8000`. Confirm the shim before removing it.
6. Continue Person 3 at Session 2 on `analysis/mediapipe-adapter` (or `main` if PR #9 merges).
7. Only after findings fixtures from Session 2 exist, point Person 4 tests at those fixtures instead of the local copies.
8. Add corpus, embeddings, and the hosted adapter. Wire worker stages last.

Conflicts to avoid:

- Do not “fix” the contract so it matches whichever frontend happens to be checked out.
- Do not put coaching logic in `services/formcheck/api/routes.py`.
- Do not put MinIO or Redis imports in `packages/rag` or `packages/pose`.
- Do not start a second Postgres on 5432 while Person 2’s stack is up.
- Do not regenerate the shuttle logo or the Fierce palette.

---

## 10. Environment and Testing Guide

### 10.1 This checkout (Person 4 only)

From the repository root:

```text
.\.venv\Scripts\python.exe -m pytest packages/rag/tests --rootdir=packages/rag -q
```

If `.venv` is missing:

```text
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e "packages/rag[dev]"
```

Frontend in **this** checkout (overhead clear only, mock API):

```text
cd apps/web
npm install
npm run dev
```

Open the printed URL, usually `http://localhost:5173`. Leave `VITE_API_BASE_URL` unset to use the mock.

Local pgvector container, only if port 5432 is free and Person 2’s stack is not running. Commands run in `infra/local`:

```text
docker compose up -d
docker compose ps
docker compose exec postgres psql -U formcheck -d formcheck -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
docker compose stop
```

`docker compose down -v` deletes the coaching tables. Docker Desktop 4.95.0 and engine 29.8.2 were installed on this Windows machine. `docker` may be missing from a shell until `C:\Program Files\Docker\Docker\resources\bin` is on `PATH`.

### 10.2 `origin/main` platform

Documented in `origin/main` `infra/local/README.md`:

```text
cd infra/local
cp .env.example .env
docker compose up --build
```

Then the API docs URL is `http://localhost:8000/docs`, storage console `http://localhost:9001` (user `formcheck`, password `formchecksecret` per that README). Web app:

```text
cd apps/web
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

Contract validator, from a checkout that actually contains `packages/contracts/validate_examples.py`:

```text
pip install -r packages/contracts/requirements.txt
python packages/contracts/validate_examples.py
```

The previous handoff said this expects 7 examples and 3 semantic guards. **Not re-run here.**

### 10.3 Person 3 branch

On `analysis/mediapipe-adapter`:

```text
uv python install 3.12
uv sync --locked --all-groups
uv run --locked pytest -v
```

If `cv2` was installed before the exclusion:

```text
uv sync --locked --all-groups --reinstall-package opencv-python-headless
```

### 10.4 What not to commit

`.env`, videos, MediaPipe `.task` files, copyrighted corpus bodies, `node_modules`, `.venv`. Local passwords in Compose are development defaults already visible in the files. Do not reuse them outside this machine.

---

## 11. Critical Context and Lessons Learned

- `main` on GitHub and the folder open in Cursor are different commits. Read `git status` and `git rev-parse HEAD` before editing.
- The published `docs/HANDOFF.md` was already outdated on the day it merged because PR #6 landed in the previous minute.
- `import cv2` succeeding does not mean a single OpenCV distribution is installed.
- A healthy Postgres container does not create a website at `localhost`.
- Person 4’s first retrieval implementation is keyword overlap on purpose. It is not the final ranker.
- The late-elbow finding used in the first RAG fixture was replaced after Person 3’s message. The rule id is now `clear.low_arm_extension.v1`. Do not bring `clear.late_elbow_extension.v1` back.
- `clear.limited_trunk_rotation.v1` exists only in a local test fixture. It is not an enabled rule.
- Candidate diagnostics must be structurally absent. The local model ignores extra JSON keys so a leaked `would_trigger` cannot become a tip. That is a safety net, not an invitation to send diagnostics.
- WSL was not installed when Docker Desktop was first installed. Docker later started successfully (engine 29.8.2). If the engine is down, start Docker Desktop; do not install a second engine.
- `gh` is not on PATH.
- User name for this workspace is junyu101. They prefer working in the code. They asked for design-doc changes to be discussed first during Person 1 work.

---

## 12. First Actions for the New Agent

- [ ] `git fetch origin` and record `git rev-parse HEAD` versus `origin/main`. Expect this checkout to be behind.
- [ ] Stash or copy uncommitted `packages/rag` and `infra/local/init` before any checkout or rebase.
- [ ] Read `origin/main` `packages/contracts/common.schema.json`, `analysis-findings.schema.json`, `analysis-result.schema.json`, and `docs/adr/0001-shared-analysis-contracts.md`.
- [ ] Confirm whether the ADR reviewer table is still blank.
- [ ] Read `services/formcheck/compat.py` on `main` before changing frontend types or the shim flag.
- [ ] Do not start the uncommitted Compose file if `origin/main` Compose is already bound to port 5432.
- [ ] Re-run `packages/rag` pytest after the package sits on current `main`.
- [ ] Ask the human one question: are stroke ids `overhead_clear` or `clear|smash|drop`?
- [ ] Then continue at P0.4 or Person 3 Session 2. Do not rebuild the frontend, do not enable the arm-extension rule, and do not call a hosted model with video.

---

## Appendix A — Pull requests

| PR | State | Author | What it is |
|---|---|---|---|
| [#1](https://github.com/Leohq1/FormCheck/pull/1) | Merged 2026-10-17 | mzliu05 | Frontend MVP. This checkout is here. |
| [#2](https://github.com/Leohq1/FormCheck/pull/2) | Merged 2026-10-18 | mzliu05 | Clear/smash/drop UI and doc wording. On `main` only. |
| [#3](https://github.com/Leohq1/FormCheck/pull/3) | Merged into `analysis/mediapipe-adapter` | Leohq1 | Person 3 Session 1. |
| [#4](https://github.com/Leohq1/FormCheck/pull/4) | Merged to `main` | ZZeeZZ1127 | Milestone A schemas and ADR 0001. |
| [#5](https://github.com/Leohq1/FormCheck/pull/5) | Merged to `main` | mzliu05 | Shuttle logo and favicon. |
| [#6](https://github.com/Leohq1/FormCheck/pull/6) | Merged to `main` 2026-10-18T02:23:21Z | ZZeeZZ1127 | FastAPI, fake worker, Compose, contract realignment, interim result shim. |
| [#7](https://github.com/Leohq1/FormCheck/pull/7) | Merged to `main` 2026-10-18T02:23:42Z | mzliu05 | `docs/HANDOFF.md`, already stale relative to #6. |
| [#8](https://github.com/Leohq1/FormCheck/pull/8) | Open | ZZeeZZ1127 | Alembic, idempotency, retention sweeper, cancel. |
| [#9](https://github.com/Leohq1/FormCheck/pull/9) | Open | Leohq1 | Merge `analysis/mediapipe-adapter` into `main`. |

## Appendix B — Local Person 4 files

```text
packages/rag/pyproject.toml
packages/rag/README.md
packages/rag/src/formcheck_rag/__init__.py
packages/rag/src/formcheck_rag/manifest.py
packages/rag/src/formcheck_rag/chunking.py
packages/rag/src/formcheck_rag/retrieval.py
packages/rag/src/formcheck_rag/findings.py
packages/rag/src/formcheck_rag/feedback.py
packages/rag/tests/test_manifest.py
packages/rag/tests/test_chunking.py
packages/rag/tests/test_retrieval.py
packages/rag/tests/test_feedback.py
packages/rag/tests/test_findings_boundary.py
packages/rag/tests/fixtures/*
infra/local/docker-compose.yml          # conflicts with origin/main
infra/local/init/001-coaching.sql
infra/local/README.md                    # modified; conflicts with origin/main
```

Virtualenv: `.venv` at the repo root (gitignored). Python used: 3.12.10 (`py -3.12`).

## Appendix C — Chats in this Cursor project

| Transcript | What it covers |
|---|---|
| `fcc9fa2d-2b89-45aa-a8c8-060c4c1b9882` | Installing agent skills. Not product code. |
| `ccac8b3f-7581-4baf-ae83-2a383c521f8d` | Early UI planning. Studio color-swap preview was scrapped. |
| `a969954d-958b-48d4-b182-fe9dee2628da` | Person 4 RAG, Person 3 boundary agreement, Docker, this handoff. |

Person 1, 2, and 3 implementation detail beyond those chats comes from GitHub, not from additional local transcripts. If their Cursor transcripts live in other project folders, they were **not** found here.
