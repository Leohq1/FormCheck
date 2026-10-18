# FormCheck — Unified Project Handoff

**Document purpose:** Single source of truth so one replacement agent can continue all four person-roles without prior chat history.

**Snapshot date:** 2026-10-18 (evening PDT)  
**Primary remote:** `https://github.com/Leohq1/FormCheck`  
**Verified tip of `origin/main` when writing:** `f8a7123` (`Merge pull request #7 from Leohq1/docs/project-handoff`)  
**Also verified:** `origin/platform/contract-realignment` = `0be018c` (includes PR **#8** lifecycle hardening, **not yet on `main`**)  
**Also verified:** `origin/analysis/mediapipe-adapter` (Person 3 Session 1 + design docs; **not on `main`**)

> **Accuracy rule:** Facts below are grounded in repository files, git history, and GitHub PR metadata. Inferences are labeled **Assumption** / **Unverified**. Do not treat assumptions as requirements.
>
> **Supersedes:** `docs/HANDOFF.md` (PR #7). That document was authored against tip `d8290b7` and incorrectly states Person 2 platform code is absent from `main`. **PR #6 has since merged.** Prefer **this root `HANDOFF.md`**.

---

## 1. Executive Summary

### What FormCheck is

FormCheck is a modular-monolith MVP for **asynchronous badminton technique coaching**. A user uploads a short clip of one stroke, the system estimates pose with **MediaPipe**, applies **deterministic rules**, retrieves coaching from a **curated corpus**, and returns **cited** feedback. There are **no user accounts**; access uses `analysis_id` + a high-entropy capability token (returned once; server stores hash only). Default retention is **24 hours**.

### Current status (high level)

| Workstream | On `main` now | Elsewhere / notes |
|---|---|---|
| **Person 1 — Frontend** | **Shipped** (PRs #1, #2, #5): mock-first Vite/React app, multi-stroke UI (`clear`/`smash`/`drop`), Fierce design, logo | Still on **interim** result/types shape; ADR says remap after contracts |
| **Person 2 — Platform** | **Milestone B + contract realignment shipped** (PR #6): FastAPI `services/formcheck/`, Compose, MinIO-compatible storage (`pgsty/silo`), Dramatiq fake worker, contract validation, interim result shim | **PR #8 hardening** (Alembic, Idempotency-Key, cancel, retention sweeper, API tests) is on `platform/contract-realignment` only — **merge to `main` still needed** |
| **Person 3 — Analysis** | README stubs only under `packages/{video,pose,biomechanics,rules}` | **Session 1 complete** on `analysis/mediapipe-adapter` (uv workspace, package skeletons, OpenCV sole-provider fix). Sessions 2–10 not started. PR #9 closed **unmerged** |
| **Person 4 — RAG / evals** | README stubs only | No implementation branch observed |
| **Shared contracts (Milestone A)** | **On `main`** (PR #4): schemas, examples, validator, ADR 0001 | ADR status on merged realignment commit records reviewers; stroke enum still **`overhead_clear` only** — conflicts with frontend multi-stroke product |

### Immediate priorities (replacement agent)

1. **Merge platform hardening into `main`:** open/merge PR from `platform/contract-realignment` → `main` (brings Alembic, idempotency, cancel, sweeper, lifecycle tests).
2. **Fix frontend ↔ API binary upload gap:** UI does `create → complete-upload` **without PUT** to `upload_url`; API rejects complete if object missing. Add `uploadFile` PUT (or temporary API bypass for demos).
3. **Resolve stroke ID conflict:** product/frontend/docs use `clear|smash|drop`; contracts + platform Pydantic still `overhead_clear` only.
4. **Person 1 remap** to ratified result shape (or keep `FORMCHECK_INTERIM_RESULT_SHIM=1` until remap).
5. **Bring Person 3 branch awareness:** continue Sessions 2+ on `analysis/mediapipe-adapter`; do not expect analysis packages on `main` yet.
6. **Do not invent Person 4 RAG** until Person 3 can emit findings (`0-draft` OK for early wiring).

---

## 2. Project Overview

### 2.1 Objectives and MVP scope

Authoritative sources: `docs/TEAM_DECISIONS_AND_RESPONSIBILITIES.md`, `docs/ImplementationPlan.md`, `docs/BADMINTON_MOVEMENT_ASSISTANT_TECHNICAL_DESIGN.md`, root `README.md`.

**In scope:** web upload; async jobs; MediaPipe-only pose; rule-based faults (LLM must not invent faults); curated RAG with citations; no accounts; local-first Docker; retention/deletion.

**Out of MVP:** multi-camera, live feedback, pro similarity, YOLO/MMPose alongside MediaPipe, accounts, separate managed vector DB.

**First integration target (team):**

```text
Real frontend → real API → stored upload → fake worker → sample result → real result screen
```

**Parallel Group B demos:**

```text
Sample video → MediaPipe → PoseSequence
Sample finding → coaching retrieval → cited passages
```

### 2.2 Architecture

```text
Browser (Person 1)
  → HTTP /api/v1
API (Person 2) → object storage (S3-compatible; local pgsty/silo)
              → Redis + Dramatiq
                    → AnalysisJob (full payload)
Worker orchestration (Person 2)
  → analysis stages (Person 3) → AnalysisFindings
  → coaching stages (Person 4) → AnalysisResult
  → persist result_json
API → Browser (poll progress / fetch result)
```

Modular monolith: one git repo, path ownership, multiple processes (api, worker, postgres, redis, object store).

### 2.3 Technology stack

| Area | Decision | Status |
|---|---|---|
| Frontend | React 19, TypeScript, Vite 8, React Router 7, TanStack Query 5, Tailwind 4 | On `main` |
| Frontend tests | Vitest, Playwright | On `main` |
| API | Python 3.12, FastAPI, Pydantic, SQLAlchemy, psycopg | On `main` (`services/formcheck/`) |
| Worker | Dramatiq + Redis; fake pipeline today | On `main` |
| DB | PostgreSQL + pgvector image | Compose on `main` |
| Object storage | MinIO API via **`pgsty/silo` + `pgsty/mc`** (official `minio/*` removed from Docker Hub Sep 2026) | On `main` |
| Contracts | JSON Schema 2020-12 + `jsonschema`/`referencing` | On `main` |
| Person 3 tooling | **uv** + `uv.lock`, Python `>=3.12,<3.13` | On analysis branch only |

### 2.4 Repository layout

```text
apps/web/                      # Person 1
services/api/                  # README + pointer to formcheck package
services/worker/               # README; orchestration in formcheck/worker
services/formcheck/            # Person 2 implementation package (PR #6)
services/Dockerfile.api|worker
services/requirements.txt
services/tests/
infra/local/                   # docker-compose.yml, .env.example
packages/contracts/            # Shared schemas (PR #4)
packages/video|pose|biomechanics|rules/   # Person 3 (skeletons on analysis branch)
packages/rag/                  # Person 4 stub
corpus/manifests/              # Person 4 stub
evals/                         # stubs
docs/                          # design + ADR + (stale) docs/HANDOFF.md
HANDOFF.md                     # THIS FILE (preferred)
```

On `analysis/mediapipe-adapter` additionally:

```text
pyproject.toml, uv.lock, .python-version
packages/*/formcheck_*/
services/worker/analysis/formcheck_analysis/
packages/pose/docs/person3-*.md
```

### 2.5 Constraints and conventions

- JSON; `snake_case`; UTC ISO 8601; UUIDs; confidence ∈ [0,1]
- Inter-module messages include `schema_version`
- Missing measurements marked unavailable — **never invented**
- LLM may explain findings but **must not invent/alter faults**
- Coaching tips need citations; provider failure → deterministic fallback
- Do not commit videos, weights, secrets, copyrighted corpus binaries
- Capability tokens: hash at rest; frontend `sessionStorage` only
- Contract changes need ≥1 Group A and ≥1 Group B reviewer

### 2.6 Status vocabulary

```text
created, uploading, queued, preprocessing, pose_estimation,
phase_detection, rule_evaluation, retrieval, generating,
completed, inconclusive, failed, cancelled, expired
```

Frontend also uses `deleted` after DELETE.  
`inconclusive` = operated correctly but cannot produce reliable findings.  
`failed` = technical failure.

---

## 3. Agent-by-Agent Work Summary

GitHub collaborators: `mzliu05`, `ZZeeZZ1127`, `Leohq1`, `junyu101`.

| Role | Likely GitHub | Confidence |
|---|---|---|
| Person 1 (Frontend) | `mzliu05` | **High** — authored PRs #1, #2, #5 |
| Person 2 (Platform + contracts author) | `ZZeeZZ1127` (Zeen) | **High** — authored PRs #4, #6, #8 |
| Person 3 (Analysis) | `Leohq1` | **High** — authored PR #3 + Person 3 docs |
| Person 4 (RAG / evals) | `junyu101` | **Assumption** — collaborator; no implementation PRs observed |

### 3.1 Person 1 — Frontend (`apps/web/`)

**Merged PRs:** #1 (MVP Fierce UI), #2 (clear/smash/drop + doc wording), #5 (logo/favicon).

**Accomplished:**

- Routes: `/` (GuidancePage), `/upload` (UploadPage), `/analyses/:analysisId` (AnalysisPage)
- Mock client by default; HTTP when `VITE_API_BASE_URL` set (`apps/web/src/api/index.ts`)
- Types/fixtures in interim shape: severity `low|medium|high`, string `evidence`, `recommendations`/`citations`, quality enum, error `message`/`retry_may_work` (`apps/web/src/api/types.ts`, `fixtures/results.ts`)
- Stroke config: `clear|smash|drop` (`apps/web/src/sports/config.ts`)
- Capability token in `sessionStorage` (`apps/web/src/api/session.ts`)
- Vitest + Playwright happy-path
- Design: Fierce palette; calm inner pages; shuttlecock logo assets under `apps/web/public/images/`

**Critical gap vs platform:**

- `AnalysisApi` on `main` has **no `uploadFile`**; UploadPage does `createAnalysis` then **`completeUpload` immediately** without PUT to `upload_url`.
- Platform `complete-upload` **requires** the object to exist in storage → real-API happy path **fails** unless fixed.

**Outstanding:**

- Remap UI to ratified contracts (ADR 0001) and set `FORMCHECK_INTERIM_RESULT_SHIM=0`
- Implement PUT to presigned `upload_url` before complete
- Align stroke IDs with contracts after team decision
- Broader E2E for filename-driven outcomes (`inconclusive`/`failed`/`expired`)

**User preferences (Person 1 sessions — treat as binding for UI):**

- Landing may be bold; **inner pages stay calm**
- Avoid generic “AI slop” aesthetics; Fierce palette
- Discuss design-doc edits with the human before changing design docs

### 3.2 Person 2 — Platform

**Merged on `main`:**

| PR | Content |
|---|---|
| #4 | Milestone A contracts + ADR + validator |
| #6 | FastAPI package, Compose, storage, fake worker, job enqueue, schema validation, interim result shim |

**Merged to `platform/contract-realignment` but not `main`:**

| PR | Content |
|---|---|
| #8 | Alembic, Idempotency-Key, cancel endpoint, retention sweeper, API lifecycle tests (21 passed locally when authored) |

**Implementation locations (PR #6 on `main`):**

| Path | Role |
|---|---|
| `services/formcheck/api/main.py` | FastAPI app, CORS, lifespan (init DB, ensure bucket) |
| `services/formcheck/api/routes.py` | HTTP endpoints |
| `services/formcheck/api/deps.py` | Bearer → analysis auth (404 for bad token/missing) |
| `services/formcheck/auth.py` | Token generate/hash/match |
| `services/formcheck/storage.py` | S3 client: presign PUT, head/stat, delete prefix; key helper `analyses/{id}/source/{filename}` |
| `services/formcheck/schemas.py` | **Ratified** Pydantic models (`feedback`, numeric quality, structured evidence, `safe_message`…) |
| `services/formcheck/compat.py` | `to_interim_result()` for Person 1 shim |
| `services/formcheck/contract_validate.py` | JSON Schema registry validation |
| `services/formcheck/worker/tasks.py` | `run_fake_analysis(job: dict)`, `process_deletion` |
| `services/formcheck/worker/fixtures.py` | completed / inconclusive(+error) / failed / expired fixtures |
| `services/formcheck/models.py` | SQLAlchemy `Analysis`, `DeletionOutbox`, `AuditEvent` |
| `services/formcheck/db.py` | Engine; `init_db` uses `create_all` on #6 main (Alembic on #8 branch) |
| `infra/local/docker-compose.yml` | postgres, redis, silo/minio, api, worker |
| `services/Dockerfile.api` / `Dockerfile.worker` | Copy `formcheck` + `packages/contracts` → `/contracts` |

**HTTP API (on `main` from #6):**

```http
POST   /api/v1/analyses
POST   /api/v1/analyses/{id}/complete-upload   # requires uploaded object
GET    /api/v1/analyses/{id}
GET    /api/v1/analyses/{id}/result            # validates schema; optional interim shim
DELETE /api/v1/analyses/{id}
GET    /api/v1/health
```

**On #8 branch additionally:**

```http
POST   /api/v1/analyses/{id}/cancel
```

+ `Idempotency-Key` on create/delete; Alembic `20261018_0001_initial`; `sweep_expired_analyses` Dramatiq actor.

**Env flags:**

- `FORMCHECK_INTERIM_RESULT_SHIM` (default `true` / `1`) — project ratified → interim on GET `/result`
- `FORMCHECK_CONTRACTS_DIR` — schema root (Docker: `/contracts`)
- `FORMCHECK_START_SWEEPER=1` — worker kicks retention loop (#8)
- `VITE_API_BASE_URL` — frontend → real API

**Fake worker outcome convention:** filename containing `inconclusive` / `failed` / `expired` forces that terminal state (same idea as frontend mock).

**Outstanding (Person 2):**

1. Land #8 onto `main`
2. Coordinate Person 1 upload PUT + stroke enum + shim off
3. Replace fake worker with Person 3/4 stages when ready
4. UUIDv7 migration (optional; ADR notes schemas don’t pin version; code still `uuid.uuid4()`)
5. Rate limits / request-size polish (explicitly deferred)

### 3.3 Person 3 — Analysis

**Where code lives:** `origin/analysis/mediapipe-adapter` (PR #3 merged into that branch). **Not on `main`.**

**PR #9** (`Analysis/mediapipe adapter` → `main`) was **closed without merge** (2026-10-18). Unverified why; do not assume rejection of Session 1 content.

**Authoritative Person 3 docs (on analysis branch):**

- `packages/pose/docs/person3-analysis-pipeline-design.md`
- `packages/pose/docs/person3-analysis-pipeline-implementation-plan.md` (10 sessions; only Session 1 done)
- `packages/pose/docs/person3-session-1-handoff.md`

**Session 1 accomplished:**

- uv project `formcheck-analysis` 0.1.0; Python 3.12
- Importable skeletons: `formcheck_video`, `formcheck_pose`, `formcheck_biomechanics`, `formcheck_rules`, `formcheck_analysis`
- **OpenCV sole-provider fix:** exclude MediaPipe’s `opencv-contrib-python`; keep `opencv-python-headless` only (critical — dual providers corrupt `cv2`)
- Smoke + sole-provider tests; Ruff/mypy configured

**Ownership paths:**

```text
packages/video/, pose/, biomechanics/, rules/
services/worker/analysis/
evals/pose/, evals/rules/
```

**Hard rules:** no MinIO/Redis/Dramatiq imports in packages; read/write artifacts via Person 2 ports; findings `schema_version: "0-draft"` until shared schema treated as approved (schemas exist on `main` now — Person 3 should align to ratified findings shape when emitting).

**Sessions remaining (from plan — names approximate from checklists):** environment done → domain models → video → pose adapter → quality/normalization → stroke/phase → features → rules → worker composition → evaluation/readiness.

**Ports for Person 2 (Session 9 intent, from earlier cross-agent review):** provisional Protocols for artifact I/O, progress reporting, cancellation — Person 2 implements adapters. **Unverified** whether Session 9 text is fully drafted in the plan file; design says infrastructure-neutral.

### 3.4 Person 4 — RAG / evaluation

**Owns:** `packages/rag/`, `corpus/manifests/`, `evals/retrieval|generation|system/`, `services/worker/coaching/`

**Status:** README placeholders only. No code branch found.

**Depends on:** Person 3 findings (approved or `0-draft` for early fixtures); Person 2 result persistence; feedback object shape already in `analysis-result.schema.json`.

**Must not:** invent technique faults; send raw video/landmarks/tokens to LLM.

---

## 4. Consolidated Implementation Details

### 4.1 Shared contracts (Milestone A)

**Location:** `packages/contracts/`

| File | Producer → Consumer |
|---|---|
| `common.schema.json` | Shared `$defs` (quality, stroke, evidence, finding) |
| `analysis-job.schema.json` | Person 2 → Person 3 |
| `analysis-progress.schema.json` | Worker → Person 2 |
| `analysis-findings.schema.json` | Person 3 → Person 4 |
| `analysis-result.schema.json` | Group B → Person 2 → Person 1 |
| `analysis-error.schema.json` | Safe error object |
| `examples/*.json` | 7 examples including inconclusive |
| `validate_examples.py` | Registry harness + semantic guards |

**Validate:**

```bash
pip install -r packages/contracts/requirements.txt
python packages/contracts/validate_examples.py
```

Expect example pairs OK + guards:

- failed + `error=null` rejected  
- completed + non-null error rejected  
- inconclusive + `error=null` rejected  

**Pinned resolutions (ADR 0001):** see §5. Error rule: only `completed` has `error: null`; `inconclusive|failed|expired|cancelled` require non-null error (remediation lives on error for inconclusive — §8.5).

**Sign-off record:** PR #4 merged; ADR reviewer table filled on realignment commit (`mzliu05` Group B merge; Group A listed as Leohq1/junyu101 with team confirmation). **Note:** GitHub review API showed empty formal “APPROVED” reviews; merge + team confirmation used as sign-off.

### 4.2 Frontend API flow

```text
validateVideoFile
→ POST /api/v1/analyses  (CreateAnalysisRequest)
→ storeCapabilityToken(sessionStorage)
→ POST .../complete-upload   ⚠️ no PUT of bytes on main
→ navigate /analyses/:id
→ poll GET .../analyses/:id every ~600ms
→ on terminal with result: GET .../result
```

Mock advances stages ~350ms; filename tokens force outcomes.

### 4.3 Platform job flow

```text
POST create → Analysis row + presigned upload_url
browser PUT to upload_url (required for complete)
POST complete-upload → verify object → status queued
→ run_fake_analysis.send(AnalysisJob dict)
worker validates job → progress events (schema) → fixture result (schema) → result_json
GET result → validate → optional to_interim_result()
```

**AnalysisJob fields:** `schema_version="1"`, `analysis_id`, `video_object_key`, `stroke`, `handedness`, `view_hint`, `pipeline_version`.

### 4.4 Integration seams

| Seam | Contract |
|---|---|
| Browser ↔ API | Interim TS types today; ratified JSON via shim |
| API ↔ storage | Logical keys `analyses/{id}/source|normalized/...` |
| API ↔ worker | Full `AnalysisJob` JSON via Dramatiq |
| Person 3 ↔ storage | Via Person 2 abstraction/ports (not credentials) |
| Person 3 ↔ Person 4 | `AnalysisFindings` |
| Person 4 ↔ Person 2 | `AnalysisResult` with `feedback` |

### 4.5 Local Compose services

| Service | Port | Notes |
|---|---|---|
| api | 8000 | `/docs` OpenAPI |
| postgres | 5432 | formcheck/formcheck |
| redis | 6379 | Dramatiq |
| minio (silo) | 9000 / console 9001 | formcheck / formchecksecret |

```bash
cd infra/local
cp .env.example .env   # if needed
docker compose up --build
cd ../../apps/web
# PowerShell:
$env:VITE_API_BASE_URL="http://localhost:8000"; npm run dev
```

---

## 5. Decision Log

| Decision | Rationale | Alternatives / trade-offs |
|---|---|---|
| Modular monolith, path ownership | Clear 4-person boundaries without microservices | More coordination on contracts |
| Milestone A = design-doc shapes, not interim frontend | Docs + Group B need structured findings/feedback | Forced Person 1 remap; temporary shim |
| Severity `minor\|moderate\|major` | Matches tech design / rules | UI may map to low/medium/high |
| Quality numeric `[0,1]` + `warnings[]` | Matches §6.12 / evaluation | Frontend had enum+notes |
| Feedback object (Person 4) not flat recommendations | ImplementationPlan §7.7 | Frontend interim list |
| Evidence as `{feature,value,unit}[]` | Groundable for RAG | Frontend had string evidence |
| Error `safe_message`/`retryable`/`remediation[]` | Privacy-safe UX | Interim `message`/`retry_may_work` |
| Inconclusive **requires** error object | §8.5 remediation/retake | Early mistake forced `error:null` for inconclusive — **fixed** |
| Single `pose_estimator` string | Avoid split fields until needed | §3.3 separate name/version |
| `format: uuid` any version; code uuid4 | Schema can’t pin v7 easily | Tech design prefers UUIDv7 later |
| Fake worker + filename outcomes | Unblocks UI without MediaPipe | Not real analysis |
| Interim result shim default on | Avoid breaking Person 1 overnight | Must turn off after remap |
| `pgsty/silo` instead of `minio/minio` | Docker Hub removed official MinIO images (2026) | Fork/community image risk |
| uv + sole OpenCV headless (Person 3) | Dual OpenCV providers corrupt `cv2` | Version-scoped MediaPipe exclusion must be revisited on upgrade |
| Person 3 PR targets analysis branch not main | Isolate incomplete pipeline | Main lacks analysis packages until deliberate merge |
| Multi-stroke product (`clear/smash/drop`) on frontend | Product decision PR #2 | **Diverges from contracts `overhead_clear`** — unresolved |

**Abandoned / corrected approaches:**

- Treating Milestone B interim TS/Pydantic as the long-term contract — reversed by ADR 0001.
- `error: const null` for both completed **and** inconclusive — contradicted §8.5; corrected to completed-only null.
- Official MinIO Docker Hub images — pull fails; switched to pgsty.
- MediaPipe + opencv-contrib + headless together — unsafe; locked to headless only.

---

## 6. Current Project State

### What works (verified)

| Item | Evidence |
|---|---|
| Frontend mock E2E path | Vitest/Playwright present; mock client |
| Contracts validate | `validate_examples.py` + semantic guards |
| Platform API + fake worker + Compose | PR #6 on `main`; local smoke previously: health → create → PUT → complete → poll → completed |
| Interim shim | `compat.to_interim_result` + config flag |
| Person 3 Session 1 env | Analysis branch tests (2 passed per their handoff) |

### Incomplete

| Item | State |
|---|---|
| Hardening #8 on `main` | Only on `platform/contract-realignment` |
| Frontend PUT upload | Missing on `main` |
| Frontend ↔ ratified types | Shim hides gap |
| Stroke enum alignment | Conflict |
| Real MediaPipe pipeline | Sessions 2–10 not done; not on `main` |
| RAG / corpus / evals | Not started |
| `services/worker/coaching/` | Missing |
| Generated TS from schemas | Planned path unused |
| Cross-module `tests/` | README only |

### Discrepancies to remember

1. **`docs/HANDOFF.md` is stale** (claims no platform on `main`).
2. **Local checkouts** may be on old branches (`platform/job-lifecycle`) without formcheck sources — always `git fetch` and inspect `origin/main`.
3. **Stroke IDs:** frontend/docs vs contracts/platform.
4. **ADR Status line** may still say “Proposed” in some views; reviewer table was filled in realignment — treat PR #4 merge as acceptance.

---

## 7. Known Issues and Risks

| Issue | Severity | Notes |
|---|---|---|
| No browser PUT before complete-upload | **Blocker** for real UI↔API | Fix frontend or relax API for demos |
| Stroke enum mismatch | **High** | create with `clear` will fail Pydantic/enum on API |
| Hardening not on main | Medium | Re-introduce create_all-only DB until #8 merges |
| Shim masks Person 1 debt | Medium | Easy to forget `FORMCHECK_INTERIM_RESULT_SHIM=0` |
| Person 3 not on main | Medium | Agents cloning only `main` miss analysis work |
| Dual OpenCV risk on MediaPipe upgrade | Medium | Re-run sole-provider test |
| Rate limits / abuse controls | Low (deferred) | Needed before external users |
| UUIDv4 vs v7 | Low | Documented; optional later |
| Formal GitHub review records sparse | Process | Prefer ADR table + merge commits |

**Unresolved questions:**

- Official stroke vocabulary for MVP: keep multi-stroke product and expand contracts, or revert UI to `overhead_clear`?
- When to merge `analysis/mediapipe-adapter` into `main`?
- Person 4 start trigger and corpus licensing sources?
- Who owns mapping `clear` → analysis rules for smash/drop?

---

## 8. Remaining Tasks (prioritized)

### P0 — Unblock integration

1. **Merge `platform/contract-realignment` → `main`** (includes #8).  
   *Acceptance:* Alembic, cancel, idempotency, sweeper, lifecycle tests on `main`.
2. **Add frontend `uploadFile` PUT** using `upload_url` + `Content-Type` before complete.  
   *Acceptance:* Compose + Vite with `VITE_API_BASE_URL` completes analysis in UI.
3. **Stroke decision + contract/API/UI align.**  
   *Acceptance:* One enum everywhere; examples/fixtures updated; validator green.

### P1 — Contract completion for UI

4. Person 1 remaps `types.ts`, fixtures, ResultsPanel to ratified shape; turn shim off.  
5. Optional: generate TS types from JSON Schema into shared package.

### P2 — Analysis pipeline

6. Continue Person 3 Session 2+ on analysis branch per implementation plan.  
7. Define/review Session 9 ports with Person 2; implement adapters.  
8. Emit `0-draft` then ratified findings; keep candidate rules disabled until precision gate.

### P3 — Coaching

9. Person 4 corpus manifests + ingestion + retrieval + feedback generation.  
10. Wire `services/worker/coaching/` into worker after findings exist.  
11. System evals coordination.

### P4 — Production hygiene

12. Rate limits, upload quotas, observability.  
13. UUIDv7 if desired.  
14. Replace fake worker entirely.  
15. Cross-module tests under `tests/`.

---

## 9. Unified Execution Plan

```text
Week-now:
  A. git fetch; work from origin/main
  B. PR merge hardening branch → main
  C. Fix upload PUT + smoke UI against Compose
  D. Decide stroke enum; patch contracts + API + web together

Then parallel:
  E. Person 1 remap / shim off
  F. Person 3 Sessions 2–N on analysis branch
  G. Person 4 manifests when findings fixtures exist

Then:
  H. Ports + real analysis stages replace fake worker
  I. Coaching stage + evals
  J. Hardening for external users
```

**Integration conflict watchlist:**

- Stroke enums  
- Result shape (shim vs remap race)  
- Object key layouts  
- OpenCV dependency when adding MediaPipe inference  
- Root `pyproject.toml` (Person 3) vs `services/requirements.txt` (Person 2) — two Python worlds until unified

---

## 10. Environment and Testing Guide

### Frontend

```bash
cd apps/web
npm install
npm run test          # vitest
npm run dev           # mock API
# Real API:
# PowerShell: $env:VITE_API_BASE_URL="http://localhost:8000"; npm run dev
```

### Contracts

```bash
pip install -r packages/contracts/requirements.txt
python packages/contracts/validate_examples.py
```

### Platform (from `main` / after hardening merge)

```bash
cd infra/local && docker compose up --build
# API docs: http://localhost:8000/docs
cd ../../services
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=.
pytest tests -q
```

### Manual API smoke (requires PUT)

```text
POST /api/v1/analyses
PUT  upload_url  (Content-Type: video/mp4)
POST /api/v1/analyses/{id}/complete-upload  (Authorization: Bearer …)
GET  /api/v1/analyses/{id}   # poll until terminal
GET  /api/v1/analyses/{id}/result
```

### Person 3 (analysis branch)

```bash
git checkout analysis/mediapipe-adapter
# install uv 0.13.x per their handoff
uv lock --check
uv sync --locked --all-groups
uv run --locked pytest -v
```

---

## 11. Critical Context and Lessons Learned

1. **Contracts before more platform** was the correct sequence after interim Milestone B drift.
2. **Inconclusive carries remediation on `error`**, not separate frontend-only fields.
3. **MinIO Docker Hub removal** will surprise fresh machines — Compose already uses `pgsty/silo`.
4. **Never install two OpenCV wheels** with MediaPipe.
5. **`docs/HANDOFF.md` can be wrong** if written mid-merge race — always re-verify `origin/main` file tree.
6. **Dramatiq must receive full `AnalysisJob`**, not bare id (ADR pin).
7. **Frontend mock success ≠ real API success** while PUT is missing.
8. **Person 3 isolation on a long-lived branch** is intentional; cloning `main` alone is incomplete for analysis work.
9. **Capability token privacy:** uniform 404 on bad token; don’t leak existence.
10. **Design-doc edits:** Person 1 preference — ask human before changing design docs.

---

## 12. First Actions for the New Agent

Checklist — do in order:

1. [ ] `git fetch origin` and `git checkout main && git pull`.
2. [ ] Confirm `services/formcheck/` exists on `main` (PR #6). Read `docs/adr/0001-shared-analysis-contracts.md`.
3. [ ] Diff `origin/main...origin/platform/contract-realignment` — open PR to land #8 if still missing Alembic/idempotency/cancel.
4. [ ] Run `python packages/contracts/validate_examples.py` and `cd services && pytest tests -q`.
5. [ ] Skim `apps/web/src/api/types.ts` vs `packages/contracts/examples/analysis-result.example.json` — list remap fields.
6. [ ] Confirm UploadPage lacks PUT; implement or document temporary API bypass.
7. [ ] `git log origin/analysis/mediapipe-adapter -5` and read `packages/pose/docs/person3-session-1-handoff.md` from that branch.
8. [ ] Do **not** start Person 4 RAG or rate limits until P0 integration items move.
9. [ ] Prefer this root **`HANDOFF.md`** over `docs/HANDOFF.md`.
10. [ ] Before changing stroke enums or design docs, get explicit human confirmation (product + Person 1 preference).

---

## Appendix A — PR index

| # | Title | Author | Result |
|---|---|---|---|
| 1 | Frontend MVP Fierce UI | mzliu05 | Merged → main |
| 2 | clear/smash/drop strokes + doc wording | mzliu05 | Merged → main |
| 3 | Person 3 Python scaffold | Leohq1 | Merged → **analysis/mediapipe-adapter** |
| 4 | Milestone A contracts sign-off | ZZeeZZ1127 | Merged → main |
| 5 | Logo / favicon | mzliu05 | Merged → main |
| 6 | Platform contract realignment | ZZeeZZ1127 | Merged → main |
| 7 | docs handoff (now stale) | mzliu05 | Merged → main (`docs/HANDOFF.md`) |
| 8 | Alembic/idempotency/cancel/tests | ZZeeZZ1127 | Merged → **platform/contract-realignment** (not main at snapshot) |
| 9 | Analysis/mediapipe adapter → main | Leohq1 | **Closed, not merged** |

## Appendix B — Key absolute paths (Windows workspace)

```text
D:\zeenz27\projects\dubhacks26\FormCheck\
```

Remote clone path may differ; prefer repo-relative paths above.

## Appendix C — Cursor / agent transcript context (non-authoritative)

Local agent transcripts under Cursor project `D-zeenz27-projects-dubhacks26` captured Person 2 sessions: architecture report of frontend, Milestone A drafting, Docker Desktop install, Compose smoke tests, PR #4/#6/#8 authoring, Person 3 boundary reviews. Use repo + PRs as source of truth if transcripts disagree.

---

*End of handoff. Replacement agent: start at §12.*
