# FormCheck — Unified Project Handoff

**Document purpose:** Single source of truth so one replacement agent can continue all four person-roles without relying on prior chat history.

**Snapshot date:** 2026-10-18 (local evening PDT)  
**Primary remote:** `https://github.com/Leohq1/FormCheck`  
**Verified tip of `origin/main` at investigation time:** `d8290b7` (`Merge pull request #5 from Leohq1/frontend/upload-flow`)

> **Accuracy rule used while writing:** Facts below are grounded in repository files, git history, merged PRs, and branch contents. Anything inferred (team-person mapping, unfinished private work) is labeled **Assumption** or **Unverified**. Do not treat assumptions as requirements.

---

## 1. Executive Summary

### What FormCheck is

FormCheck is a modular-monolith web MVP for **asynchronous badminton technique coaching**. A user uploads a short clip of one stroke (**clear, smash, or drop** per product docs / frontend), the system estimates pose with **MediaPipe**, applies **deterministic rules**, retrieves coaching from a **curated corpus**, and returns **cited** feedback. There are **no user accounts**; access is via analysis ID + high-entropy capability token. Default retention is **24 hours**.

### Current status (high level)

| Workstream | Status on `main` | Status elsewhere |
|---|---|---|
| **Person 1 — Frontend (`apps/web/`)** | **Largely complete** against an **interim mock/API TypeScript shape**; UI + mock E2E shipped (PRs #1, #2, #5) | Branch `frontend/upload-flow` merged into `main` |
| **Person 2 — Platform (`services/api/`, infra, worker orchestration)** | **Not implemented** (README placeholders only). Branch `platform/job-lifecycle` has **no unique platform code** beyond early shared commits | Person 2 authored Milestone A contracts (PR #4) |
| **Person 3 — Analysis packages** | **Not on `main`** (by design of PR #3 target) | **Session 1 complete** on `analysis/mediapipe-adapter` (Python/uv scaffold + docs). Sessions 2–10 not started |
| **Person 4 — RAG / evals** | **Not started** (README placeholders only) | No `rag/*` implementation branch observed |
| **Shared contracts (Milestone A)** | **Schemas + examples + validator landed on `main`** (PR #4) | ADR reviewer sign-off table still **TBD**; stroke enum still **`overhead_clear` only** — conflicts with frontend multi-stroke product change |

### Immediate priorities for the replacement agent

1. **Restore / sync awareness of Person 3’s branch** (`analysis/mediapipe-adapter`) — Session 1 lives there, not on `main`.
2. **Reconcile stroke ID divergence:** product/frontend/docs say `clear|smash|drop`; ratified contracts still enum `overhead_clear` only.
3. **Align frontend types with ratified contracts** (severity, quality, feedback object, error fields) — ADR 0001 explicitly deferred this remap.
4. **Unblock Milestone B:** Person 2 must implement real API + fake worker; frontend already has `VITE_API_BASE_URL` switch.
5. **Do not invent Person 4 corpus/RAG** until findings contract + Person 3 `0-draft` findings exist; start with source manifests when ready.
6. **Honor user ground rule (Person 1 context):** discuss design-doc changes with the human before editing design docs; update docs only after agreement.

---

## 2. Project Overview

### 2.1 Objectives and MVP scope

Authoritative MVP scope: `docs/TEAM_DECISIONS_AND_RESPONSIBILITIES.md` §1 and `README.md`.

In scope:

- Web app upload of one short clip
- Async job processing
- One selected stroke: **clear, smash, or drop** (team docs + frontend; see stroke conflict in §7)
- MediaPipe-only pose for MVP
- Rule-based faults (not LLM-decided faults)
- Curated RAG coaching with citations
- No accounts / no saved progress
- Local-first (Docker Compose later); cloud after eval gates

Out of MVP (explicitly deferred): multi-camera, live feedback, professional similarity scoring, YOLO/MMPose alongside MediaPipe, user accounts, mobile apps, separate managed vector DB.

First “complete analysis” target (team doc): one controlled stroke video → one trustworthy feature → one rule finding → one retrieved passage → one result in the web UI.

### 2.2 Architecture

```text
Browser (Person 1)
   ↓ HTTP /api/v1
API (Person 2) → object storage (MinIO local)
              → job queue (Redis + Dramatiq planned)
                    ↓ AnalysisJob
Worker orchestration (Person 2)
  → analysis stages (Person 3) → AnalysisFindings
  → coaching stages (Person 4) → AnalysisResult
   ↓ persist
API → Browser
```

Repository is a **modular monolith**: one git repo, clear ownership paths, multiple runtime processes planned.

### 2.3 Technology stack (agreed)

| Area | Decision |
|---|---|
| Frontend | React 19, TypeScript, Vite 8, React Router 7, TanStack Query 5, Tailwind CSS 4 |
| Frontend tests | Vitest, Testing Library, Playwright |
| API | Python 3.12, FastAPI, Pydantic (**planned**; not on `main` yet) |
| Worker | Python 3.12 (**partial scaffold on analysis branch**) |
| Pose | MediaPipe Pose Landmarker |
| Video | FFmpeg / ffprobe (Person 3) |
| DB | PostgreSQL + pgvector |
| Queue | Redis + Dramatiq |
| Object storage | MinIO locally |
| Local env | Docker Compose under `infra/local/` (**placeholder README only**) |
| Person 3 tooling | **uv** + committed `uv.lock` (on analysis branch); Python `>=3.12,<3.13` |

### 2.4 Repository layout (intended vs present)

Intended (README):

```text
apps/web/
services/api/
services/worker/          # analysis/ (P3), coaching/ (P4)
packages/contracts/
packages/video|pose|biomechanics|rules|rag/
corpus/manifests/
evals/
infra/local/
tests/
docs/
```

**On `main` today:**

- `apps/web/` — full frontend implementation
- `packages/contracts/` — JSON Schemas, examples, `validate_examples.py`
- Most other packages/services — **README-only**
- Person 3 Python packages / `pyproject.toml` / `uv.lock` — **on `origin/analysis/mediapipe-adapter`**, not `main`

### 2.5 Constraints and conventions

- JSON APIs; `snake_case`; UTC ISO 8601; UUIDs; confidence ∈ [0,1]
- Inter-module messages include `schema_version`
- Missing measurements marked unavailable — **never invented**
- LLM may explain findings but **must not invent/alter faults**
- Every coaching tip needs a valid citation; provider failure → deterministic fallback
- Do not commit videos, model weights, secrets, copyrighted corpus binaries
- Capability tokens: store hash server-side; frontend keeps token in `sessionStorage` only
- Shared contract changes need ≥1 Group A and ≥1 Group B reviewer

### 2.6 Analysis status vocabulary

```text
created, uploading, queued, preprocessing, pose_estimation,
phase_detection, rule_evaluation, retrieval, generating,
completed, inconclusive, failed, cancelled, expired
```

Frontend also treats `deleted` as a terminal UI status after DELETE.

`inconclusive` = system OK but cannot produce reliable findings.  
`failed` = technical failure.

---

## 3. Agent-by-Agent Work Summary

GitHub collaborators observed: `mzliu05`, `ZZeeZZ1127`, `Leohq1`, `junyu101`.

| Role | Likely GitHub identity | Confidence |
|---|---|---|
| Person 1 (Frontend) | `mzliu05` (Matthew Liu) | **High** — authored frontend PRs #1/#2/#5; matches this handoff requester’s local work |
| Person 2 (Platform + contracts author) | `ZZeeZZ1127` (Zeen) | **High** — authored PR #4; ADR assigns Person 2 ownership of job/progress/result/error schemas |
| Person 3 (Analysis) | `Leohq1` (Leo) | **High** — authored PR #3 analysis scaffold + Person 3 docs |
| Person 4 (RAG / evals) | `junyu101` | **Assumption** — collaborator with no merged implementation PRs yet |

### 3.1 Person 1 — Frontend

**Owns:** `apps/web/` (and planned `packages/contracts/generated/typescript/` — **does not exist yet**)

**Merged PRs:**

| PR | Title | Merged |
|---|---|---|
| [#1](https://github.com/Leohq1/FormCheck/pull/1) | FormCheck frontend MVP with Fierce UI | 2026-10-17 |
| [#2](https://github.com/Leohq1/FormCheck/pull/2) | Support clear, smash, and drop strokes + design-doc wording updates | 2026-10-18 |
| [#5](https://github.com/Leohq1/FormCheck/pull/5) | Shuttle logo in nav + favicon | 2026-10-18 |

**Accomplished:**

- Vite/React/TS app with routes `/`, `/upload`, `/analyses/:id`
- Mock API client (default) + HTTP client switch via `VITE_API_BASE_URL`
- Capture guidance (full-bleed Fierce hero), upload form (stroke dropdown, handedness, view hint, consent, dropzone), quiet analysis wait, results for completed/inconclusive/failed/expired/deleted
- Client video validation helpers + unit tests
- Playwright happy-path E2E
- Fierce palette + Cormorant Garamond / DM Sans typography
- Logo mark assets + `LogoMark` in header; PNG favicon

**Outstanding (Person 1):**

- Remap interim `apps/web/src/api/types.ts` / fixtures / UI to **ratified** schemas (ADR 0001 consequences)
- Generate TS types from JSON Schema (planned path unused)
- Wire real upload to signed URL flow when Person 2 API exists (HTTP client currently POSTs JSON only; mock simulates upload)
- Broader E2E coverage for terminal filename outcomes (`inconclusive`/`failed`/`expired` in filename)
- Accessibility pass beyond current structure (keyboard claimed in completion criteria — verify systematically)
- Align stroke enums with contracts after team resolves `overhead_clear` vs `clear|smash|drop`

**User preferences established in Person 1 sessions (treat as binding for UI work):**

- Landing page may be bold/high-energy; **inner pages stay calm**
- Avoid generic AI-slop aesthetics; Fierce palette (`#242E2D`, `#D9D9D7`, `#EFEFED`, `#AE3121`, `#691F15`, `#A8A8A5`)
- Multi-stroke upload dropdown: Clear / Smash / Drop
- **Discuss design-document changes with the user before editing design docs**; update docs only after agreement
- Logo: use the user-supplied shuttlecock mark (extracted into `public/images/logo-mark*.png`), not earlier experimental concepts

### 3.2 Person 2 — Platform

**Owns:** `services/api/`, worker framework/orchestration in `services/worker/`, DB migrations, `infra/local/`

**Merged contributions:**

- PR #4 — Milestone A shared contracts + ADR 0001 + validator (**schemas live on `main`**)

**Not found in repository (as of this snapshot):**

- FastAPI application code
- Docker Compose / Postgres / Redis / MinIO config beyond README stub
- Capability-token hashing/persistence
- Fake worker implementation
- Alembic migrations
- Path `services/formcheck/schemas.py` mentioned in ADR as interim — **does not exist in tree** (ADR language appears forward-looking or refers to work not pushed)

**Branch `origin/platform/job-lifecycle`:** tip equals early post-PR#1 history; **no unique API implementation commits**.

**Outstanding (Person 2) — first tasks from team doc §7:**

1. Initialize FastAPI in `services/api/`
2. Docker Compose in `infra/local/`
3. Initial migration
4. Capability token generate/hash/validate
5. Endpoints: create, complete-upload, get analysis, get result, delete
6. Job state machine + **fake worker** returning schema-valid examples
7. Stable local API for Person 1
8. Lifecycle/auth/retry/deletion tests

**Required endpoints:**

```http
POST   /api/v1/analyses
POST   /api/v1/analyses/{id}/complete-upload
GET    /api/v1/analyses/{id}
GET    /api/v1/analyses/{id}/result
DELETE /api/v1/analyses/{id}
```

### 3.3 Person 3 — Analysis

**Owns:** `packages/video|pose|biomechanics|rules/`, `evals/pose|rules/`, `services/worker/analysis/`

**Merged PR:**

- [#3](https://github.com/Leohq1/FormCheck/pull/3) — Session 1 Python workspace  
  - **Base branch was `analysis/mediapipe-adapter`, not `main`** (intentional)
  - Therefore **`main` does not contain** `pyproject.toml`, `uv.lock`, or `formcheck_*` packages

**Where the code lives:** `origin/analysis/mediapipe-adapter` (includes merge commit `33dbd54`)

**Session 1 accomplished:**

- Root `formcheck-analysis` project via uv; Python 3.12 pin
- Packages: `formcheck_video`, `formcheck_pose`, `formcheck_biomechanics`, `formcheck_rules`, `formcheck_analysis` (version `0.1.0` skeletons)
- Dependency groups: base NumPy/Pydantic; analysis MediaPipe + opencv-python-headless + SciPy; test pytest/Hypothesis; dev Ruff/mypy
- **Critical fix:** exclude MediaPipe 1.1.1’s transitive `opencv-contrib-python` so only headless OpenCV provides `cv2`
- Import smoke + sole-cv2-provider tests
- Design + 10-session implementation plan + Session 1 handoff under `packages/pose/docs/` (on that branch)
- `.local/README.md` asset policy

**Not done (Sessions 2–10):** domain models, video normalize, MediaPipe inference, quality/phases/features/rules, provisional ports, eval harnesses.

**Authoritative Person 3 docs (on analysis branch):**

- `packages/pose/docs/person3-session-1-handoff.md`
- `packages/pose/docs/person3-analysis-pipeline-design.md`
- `packages/pose/docs/person3-analysis-pipeline-implementation-plan.md`

### 3.4 Person 4 — RAG and evaluation

**Owns:** `packages/rag/`, `corpus/manifests/`, `evals/retrieval|generation|system/`, `services/worker/coaching/`

**Status:** README stubs only; **no implementation commits observed**.

**Outstanding — first tasks from team doc §9:**

1. Select 5–10 rights-cleared sources  
2. Manifest format in `corpus/manifests/`  
3. Extract/clean/chunk/tag  
4. Embeddings in Postgres/pgvector  
5. Retrieval test with hard-coded finding  
6. Feedback generator + strict schema  
7. Citation validation + deterministic fallback  
8. Eval sets coordination  

**Hard rules:** no unapproved sources; never send video/frames/pose/tokens/URLs to LLM; LLM cannot create faults; no tip without citation; provider failure must not fail whole analysis.

---

## 4. Consolidated Implementation Details

### 4.1 Frontend (`apps/web/`) — what exists and how it works

**Entry / routing**

- `apps/web/src/main.tsx` → `App.tsx`
- Routes in `App.tsx`: `GuidancePage` `/`, `UploadPage` `/upload`, `AnalysisPage` `/analyses/:analysisId`
- Shell: `components/AppShell.tsx` (landing absolute header over hero; constrained layout elsewhere)
- Brand: `components/LogoMark.tsx` swaps `/images/logo-mark.png` vs `logo-mark-light.png`

**API abstraction**

- Interface: `src/api/client.ts` → `AnalysisApi`
- Factory: `src/api/index.ts` → mock if `VITE_API_BASE_URL` unset; else `httpClient.ts`
- Types: `src/api/types.ts` (**interim**, diverges from contracts — see §5/§7)
- Mock: `src/api/mockClient.ts` advances stages every ~350ms; outcome from filename via `mockOutcome.ts`
- Fixtures: `src/api/fixtures/results.ts`
- Session token storage: `src/api/session.ts` (`sessionStorage`)

**Domain config**

- `src/sports/config.ts`: `StrokeId = 'clear'|'smash'|'drop'`, tips, video constraints (100MB, 30s, mp4/mov)

**UI components**

- `VideoDropzone`, `TipsList`, `StatusBanner`, `ResultsPanel`
- Pages implement upload mutation (TanStack Query), polling on analysis page, delete flow

**Styling**

- `src/index.css` — CSS variables for Fierce palette; Tailwind v4 `@import 'tailwindcss'`
- Fonts loaded in `index.html` (Cormorant Garamond, DM Sans)

**Tests**

- Unit: `src/lib/videoValidation.test.ts`, `src/api/mockOutcome.test.ts`
- E2E: `e2e/happy-path.spec.ts`
- Commands: see §10

### 4.2 Shared contracts (`packages/contracts/`) — on `main`

| File | Role |
|---|---|
| `common.schema.json` | Shared `$defs`: quality, strokeInfo, evidence, finding |
| `analysis-job.schema.json` | Person 2 → Person 3 job message |
| `analysis-progress.schema.json` | Worker → Person 2 progress |
| `analysis-findings.schema.json` | Person 3 → Person 4 |
| `analysis-result.schema.json` | Persisted/displayed final result (`feedback` object) |
| `analysis-error.schema.json` | Stable error object |
| `examples/*.json` | Seven examples including failed/inconclusive results |
| `validate_examples.py` | Draft 2020-12 validation with shared registry |
| `requirements.txt` | `jsonschema`, `referencing` |
| `docs/adr/0001-shared-analysis-contracts.md` | Decision record for Milestone A |

**Ratified result shape highlights:**

- `quality.overall` is a **number [0,1]** + `warnings[]` (not frontend’s enum/`notes`)
- Finding severity: **`minor|moderate|major`** (frontend uses `low|medium|high`)
- Finding `evidence` is **array of `{feature,value,unit}`** (frontend uses string)
- Coaching under **`feedback`** (`summary`, `tips[]`, `limitations`, `model`, `prompt_version`) — not frontend `recommendations[]`
- Tips/findings `maxItems: 3`
- When status ∈ inconclusive/failed/expired/cancelled → **`error` required**; completed → `error: null`
- `stroke.type` enum currently **only `overhead_clear`**

### 4.3 Person 3 scaffold (on `analysis/mediapipe-adapter`)

Key root files:

- `pyproject.toml`, `uv.lock`, `.python-version`
- Package dirs under `packages/*/formcheck_*` and `services/worker/analysis/formcheck_analysis`
- Tests: `services/worker/analysis/tests/test_imports.py`

Logical storage keys Person 3 expects (via Person 2 ports later):

```text
analyses/{analysis_id}/source/{filename}
analyses/{analysis_id}/normalized/video.mp4
analyses/{analysis_id}/normalized/timestamps.json
```

First planned feature/rule (still future sessions):

- Feature: `dominant_elbow_angle_at_max_wrist_height_deg`
- Rule candidate: `clear.low_arm_extension.v1` — **disabled / not_calibrated** until ≥0.80 precision on held-out coach labels
- Internal findings use `schema_version: "0-draft"` until findings schema approved (note: findings schema file now exists on `main` from PR #4 — Person 3 still needs cross-group confirmation that this is the version to implement against, and ADR reviewer table is incomplete)

### 4.4 Integration points (must stay stable)

```text
Person 1  ←HTTP→  Person 2 API
Person 2  --AnalysisJob-->  Person 3 analysis stage
Person 3  --AnalysisFindings-->  Person 4 coaching stage
Person 4  --AnalysisResult-->  Person 2 persistence → Person 1
```

Progress messages: worker → Person 2 → (optionally) Person 1 via GET analysis.

Person 3 must **not** import MinIO/Redis/Dramatiq/DB/API.  
Person 1 must **not** call worker/storage/LLM directly.  
Person 4 must derive faults **only** from `findings`.

### 4.5 Normalized video contract (Person 3 ownership; Person 2 storage)

Documented in `packages/video/README.md` and team decisions §4.4:

- MP4 H.264 `yuv420p`
- CFR 60 fps if source ≥50 fps else 30 fps
- Rotation baked in; audio removed; long edge ≤1920; even dimensions
- PTS from 0 monotonic; timestamps.json maps frames to nearest source PTS (earlier on ties)

---

## 5. Decision Log

| Decision | Rationale | Alternatives / trade-offs | Status |
|---|---|---|---|
| Modular monolith, four ownership lanes | Parallel work with schema boundaries | Microservices too heavy for hackathon MVP | Established |
| MediaPipe only in MVP | Ship one estimator; adapters later | YOLO/MMPose deferred | Established |
| Rules decide faults; LLM explains only | Safety, evalability, no hallucinated diagnoses | End-to-end LLM coaching rejected for MVP | Established |
| No accounts; capability tokens | Speed + privacy simplicity | Accounts deferred | Established |
| Local MinIO/Postgres/Redis first | Controllable eval before cloud | Cloud-first deferred | Established |
| Milestone A JSON Schemas as integration source of truth | Stop private TS/Pydantic drift (ADR 0001) | Continue ad-hoc shapes — rejected | Schemas merged; ADR reviewers **still TBD** |
| Severity `minor/moderate/major` in contract; UI may map low/medium/high | Align design docs | Keep UI labels as contract — rejected | Contract ratified; frontend **not remapped yet** |
| Quality as numeric overall + warnings | Align tech design | Frontend enum quality — presentation only | Contract ratified; frontend **not remapped yet** |
| Result uses `feedback` object (Person 4 shape) | Align ImplementationPlan §7.7 | Frontend `recommendations` list — interim | Contract ratified; frontend **not remapped yet** |
| Inconclusive carries remediation via required `error` object | Avoid duplicate inconclusive_reason fields | Separate retake fields on result — rejected in ADR | Contract ratified; frontend still has `inconclusive_reason` / `retake_guidance` |
| Object keys `analyses/{id}/source/...` + `normalized/video.mp4` | Resolve doc conflict (ADR) | Flat `original`/`normalized.mp4` | Established in ADR |
| Pose version as single `pose_estimator` string | Simpler than split name/version for now | Split fields later if eval needs | Established in ADR |
| Frontend Fierce redesign + hero only on landing | Brand energy without overwhelming upload/results | Uniform bold marketing chrome — rejected by user | Shipped |
| Multi-stroke UI: clear/smash/drop | Product expansion beyond overhead-clear-only | Keep locked overhead clear — superseded | Frontend + many docs updated; **contracts still `overhead_clear`** |
| Person 3 uses uv + single headless OpenCV | Avoid dual `cv2` providers from MediaPipe contrib dep | Allow contrib OpenCV — unsafe collision | On analysis branch; MediaPipe upgrades must re-validate |
| Person 3 PRs target `analysis/mediapipe-adapter` before `main` | Gate root Python config with reviews; staged merge | Merge Session 1 straight to `main` — intentionally avoided | Session 1 on feature branch only |
| Design-doc edits require human discussion first (Person 1 working rule) | Prevent silent scope drift | Agent auto-updates docs — disallowed by user | Process rule |

### Abandoned / rejected approaches (do not revive casually)

- **Generic soft cream/green “AI SaaS” UI** — user rejected as bland; replaced with Fierce palette + sports hero
- **Logo exploration rounds** (checkmark-C, FC monograms, freeform surreal marks, over-complex badminton illustrations) — user rejected; final mark is the **user-supplied shuttlecock icon**
- **Baking FormCheck wordmark into raster for nav** — superseded by PNG mark + live Cormorant text for font consistency
- **Allowing both OpenCV contrib + headless** — abandoned after file collision; use exclusion + sole-provider test
- **LLM as fault detector** — out of MVP by design
- **Runtime web search for coaching** — forbidden on coaching path

---

## 6. Current Project State

### What works (verified on `main`)

- Frontend builds and runs with mock API (`npm run dev` in `apps/web`)
- Mock happy path: guidance → upload → processing stages → completed result
- Mock terminal outcomes via filename keywords
- Shared JSON Schemas + examples exist; validator script present (requires `pip install -r packages/contracts/requirements.txt`)
- Logo/favicon present

### What is incomplete

- Real API / worker / infra (**Person 2**)
- Analysis pipeline beyond Session 1 scaffold (**Person 3**, and scaffold not on `main`)
- RAG / corpus / evals (**Person 4**)
- Frontend ↔ contract alignment
- Contract stroke enum vs product multi-stroke
- ADR 0001 reviewer table not filled despite merge
- `packages/contracts/generated/typescript/` missing
- Cross-module `tests/` empty of real suites
- Docker Compose not written

### What has been verified in this investigation

- `origin/main` history and PR merge graph
- PR #3 target branch = `analysis/mediapipe-adapter` (explains absence on `main`)
- `platform/job-lifecycle` has no API code delta vs early main
- Contract examples validate conceptually via schema files (local `jsonschema` import failed in investigator env until deps installed — run validator after install)
- Frontend types file contents vs contract schemas compared directly

### Milestone status

| Milestone | Intent | Status |
|---|---|---|
| **A — Contracts** | Five schemas approved | **Schemas merged**; formal ADR reviewer sign-off **incomplete**; stroke enum conflict open |
| **B — Platform vertical slice** | Real FE → real API → storage → fake worker → result UI | **Blocked on Person 2 implementation**; FE mock slice exists |
| **C — Analysis prototypes** | Sample video → PoseSequence; hard-coded finding → retrieval | **Not started** (P3 Session 1 env only; P4 not started) |
| **D — Group B integration** | Findings → RAG → Result | **Not started** |
| **E — Full integration** | Replace fake worker with real pipeline | **Not started** |

---

## 7. Known Issues and Risks

### 7.1 Critical / high

1. **Stroke ID divergence**  
   - Frontend/docs: `clear|smash|drop`  
   - Contracts: `overhead_clear` only  
   - Risk: Person 2/3/4 implement incompatible enums; upload metadata rejected  
   - Action: cross-group decision + schema bump **before** API freeze

2. **Frontend interim types vs ratified contracts**  
   - Remap required (severity, quality, feedback, error field names, stroke object shape)  
   - Shipping Milestone B without remap will break UI against real API

3. **Person 3 code not on `main`**  
   - Easy for a new agent to assume analysis packages exist under `packages/pose/` on `main` (they do not)  
   - Must check out `analysis/mediapipe-adapter` or merge it intentionally

4. **ADR sign-off incomplete**  
   - PR #4 body required filling reviewer table before merge; table still `_TBD_`  
   - Treat schemas as “landed but governance incomplete” until named sign-off recorded

5. **No platform implementation**  
   - Blocks all true E2E integration

### 7.2 Medium

- Person 3 MediaPipe+headless OpenCV: imports OK ≠ inference OK (Task 4 must validate)
- Sample video / model assets not in repo (correct); tests must skip without env vars
- ImplementationPlan still contains some `overhead_clear` examples alongside multi-stroke language — residual inconsistency
- Vite dev server historically dies when orphaned — restart with `npm run dev -- --host 127.0.0.1 --port 5173`

### 7.3 Technical debt

- Mock client simulates upload URL without PUT to object storage
- No OpenAPI-generated client; hand-written types
- Multiple unused logo concept assets may exist under Cursor `assets/` cache — not needed in repo
- `.cursor/` skill trees in workspace are tooling, not product — do not commit secrets; `.cursor/` currently untracked locally in some worktrees

### 7.4 Unresolved questions (need human / team answers)

- Final stroke enum: keep multi-stroke product and update contracts, or temporarily constrain API to clear-only?
- Who fills ADR 0001 Group A/B sign-off names?
- When to merge `analysis/mediapipe-adapter` → `main`?
- Person 4 identity confirmation (`junyu101`?) and corpus rights status
- Hosted LLM provider choice (deferred but blocks real generation)
- UUIDv7 vs uuid4 alignment (ADR notes schemas don’t pin version)

---

## 8. Remaining Tasks (Prioritized)

### P0 — Unblock everyone

| ID | Task | Owner lens | Depends on | Acceptance |
|---|---|---|---|---|
| P0.1 | Resolve stroke enum (`overhead_clear` vs `clear|smash|drop`) and update contracts **or** temporarily constrain frontend — **discuss with humans first for design docs** | All / contracts | Team decision | Schemas, examples, FE, docs agree; validator passes |
| P0.2 | Complete ADR 0001 reviewer table or explicitly reaffirm schemas | Group A+B | Humans | Named approvals dated |
| P0.3 | Document / merge strategy for Person 3 Session 1 onto integration branch/`main` | P3 + leads | Review of root uv config | `pyproject.toml` discoverable for downstream |

### P1 — Milestone B platform slice

| ID | Task | Acceptance |
|---|---|---|
| P1.1 | Person 2: FastAPI + Compose + MinIO/Postgres/Redis | `docker compose up` documented |
| P1.2 | Person 2: analysis CRUD + capability tokens + retention hooks | Unauthorized access denied; delete wipes objects |
| P1.3 | Person 2: fake worker emits schema-valid progress/results | FE with `VITE_API_BASE_URL` completes flow |
| P1.4 | Person 1: remap types/UI to contracts; regenerate fixtures | Mock + HTTP fixtures validate against schemas |
| P1.5 | E2E against fake worker | Playwright (or cross-module test) green |

### P2 — Group B prototypes (Milestone C)

| ID | Task | Acceptance |
|---|---|---|
| P2.1 | Person 3 Session 2: domain models + `0-draft` findings serialization | Failing→passing tests per plan |
| P2.2 | Person 3 Sessions 3–4: video normalize + MediaPipe adapter | PoseSequence from synthetic/asset video |
| P2.3 | Person 4: source manifests + 5–10 approved sources | Manifest schema + rights fields complete |
| P2.4 | Person 4: retrieval prototype from hard-coded finding | Cited chunks returned |

### P3 — Deepen pipeline / RAG (Milestone D–E)

| ID | Task | Acceptance |
|---|---|---|
| P3.1 | Person 3 Sessions 5–8: quality, phases, feature, disabled rule isolation | Diagnostics never in production findings |
| P3.2 | Person 3 Session 9: ports + Person 2 adapter approval | No direct infra imports in P3 |
| P3.3 | Person 4 generation + fallback + eval harnesses | Faithfulness/citation metrics reported |
| P3.4 | Replace fake worker with real pipeline | Public API unchanged |

---

## 9. Unified Execution Plan

Recommended order for a **single** replacement agent covering all roles:

### Phase 0 — Orient (half day)

1. Read this handoff + `docs/TEAM_DECISIONS_AND_RESPONSIBILITIES.md` + ADR 0001  
2. Checkout `main` and run frontend mock path  
3. Checkout `analysis/mediapipe-adapter` in a worktree; read Person 3 Session 1 handoff  
4. Run contract validator after installing deps  
5. List open human decisions (stroke enum, ADR sign-off)

### Phase 1 — Contract hygiene (before coding platform)

1. Drive stroke-enum decision with the team  
2. Patch `packages/contracts` + examples + ADR note  
3. Remap `apps/web` types/fixtures/ResultsPanel to match  
4. Add `packages/contracts/generated/typescript/` **or** document manual sync process

### Phase 2 — Person 2 Milestone B

1. Implement API + infra + fake worker against **updated** schemas  
2. Point frontend at API; fix gaps (upload PUT, auth headers already sketched)  
3. Prove delete/expire/unauthorized cases

### Phase 3 — Person 3 Sessions 2–4 (parallelizable after ports sketched)

1. Continue from Session 1 on `analysis/mediapipe-adapter`  
2. Do **not** claim production worker integration until Person 2 approves ports  
3. Keep findings `0-draft` until findings schema explicitly accepted for implementation

### Phase 4 — Person 4 corpus + retrieval

1. Rights-approved sources only  
2. Hard-coded finding retrieval before generation  
3. Generation last; enforce citation validator + fallback

### Phase 5 — Integrate Group B into worker; drop fake worker

Follow Milestone D→E; keep public HTTP stable for Person 1.

### Conflict / overlap watchlist

- **Contracts ownership:** P2 authored most schemas; P3 owns findings semantics; any stroke/severity change needs both groups  
- **Worker directory:** P2 owns framework; P3 `analysis/`; P4 `coaching/` — do not collapse into one package  
- **Frontend vs contracts:** never “fix” schemas to match interim FE without ADR update  
- **Design docs:** Person 1 rule — ask human before editing

---

## 10. Environment and Testing Guide

### 10.1 Frontend (Person 1)

```bash
cd apps/web
npm install
npm run dev
# optional: npm run dev -- --host 127.0.0.1 --port 5173
```

Mock API: leave `VITE_API_BASE_URL` unset (see `.env.example`).

```bash
npm test
npx playwright install chromium   # first time
npm run test:e2e
npm run build
```

Real API (when exists):

```bash
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

Mock outcome trick: name upload file containing `inconclusive`, `failed`, or `expired`.

### 10.2 Contracts

```bash
pip install -r packages/contracts/requirements.txt
python packages/contracts/validate_examples.py
```

### 10.3 Person 3 analysis env (on `analysis/mediapipe-adapter`)

```powershell
uv python install 3.12
uv sync --locked --all-groups
uv lock --check
uv run --locked pytest -v
uv run --locked ruff check packages services/worker/analysis
uv run --locked mypy packages/video/formcheck_video packages/pose/formcheck_pose packages/biomechanics/formcheck_biomechanics packages/rules/formcheck_rules services/worker/analysis/formcheck_analysis
```

Optional assets (never committed):

```text
FORMCHECK_SAMPLE_VIDEO=.local/samples/overhead_clear.mp4
MEDIAPIPE_POSE_MODEL_PATH=.local/models/pose_landmarker_full.task
```

If an environment predates the OpenCV exclusion:

```powershell
uv sync --locked --all-groups --reinstall-package opencv-python-headless
```

### 10.4 Person 2 / Person 4

No runnable service instructions exist yet beyond README aspirations. Prefer implementing Compose from `infra/local/README.md` stub when starting P2.

### 10.5 Git branches of record

| Branch | Purpose |
|---|---|
| `main` | Integration trunk (FE + contracts as of PR #5) |
| `frontend/upload-flow` | Person 1 feature branch (merged) |
| `contracts/milestone-a-signoff` | Contracts PR branch (merged) |
| `analysis/mediapipe-adapter` | Person 3 parent feature branch (**has Session 1**) |
| `analysis/session-1-python-scaffold` | Session 1 PR head (merged into mediapipe-adapter) |
| `platform/job-lifecycle` | Reserved for Person 2 — **empty of API code today** |
| `rag/corpus-retrieval` (planned name in team doc) | **Not observed on remote** |

---

## 11. Critical Context and Lessons Learned

1. **`main` ≠ complete project.** Analysis Python workspace is on a side branch by design.  
2. **ADR text mentioning Milestone B / `services/formcheck/schemas.py` does not mean platform code exists** — verify the tree.  
3. **Product stroke expansion happened in FE/docs first; contracts lagged** — highest integration footgun.  
4. **OpenCV dual-provider bug** is subtle: `import cv2` can succeed while files conflict — rely on metadata ownership test.  
5. **User prefers discussion before design-doc edits** (Person 1 sessions).  
6. **UI: bold landing, quiet tool pages**; don’t over-card or purple-glow.  
7. **Logo:** use checked-in shuttle PNGs derived from the user’s mark; don’t regenerate random concepts into the product.  
8. **Fake worker is intentional for Milestone B** — do not block UI on MediaPipe.  
9. **Rules stay disabled until eval precision gate** — empty findings are valid; Person 4 must not invent faults.  
10. **Capability tokens in sessionStorage** — never log them; server stores hashes only (when implemented).  
11. **Conventional commits + ownership-scoped PRs** — see `CONTRIBUTING.md` and `.cursor/rules/git.mdc` if present.  
12. **Person 3 Session plan is test-first / subagent-driven** — follow `person3-analysis-pipeline-implementation-plan.md`; don’t skip to MediaPipe before Session 2 models.

---

## 12. First Actions for the New Agent

Checklist — do these before writing feature code:

- [ ] `git fetch --all --prune` and note `origin/main` SHA  
- [ ] Skim this file + `docs/TEAM_DECISIONS_AND_RESPONSIBILITIES.md` + `docs/adr/0001-shared-analysis-contracts.md`  
- [ ] Run frontend mock app; complete one happy-path upload  
- [ ] Diff `apps/web/src/api/types.ts` against `packages/contracts/analysis-result.schema.json` and list mismatches  
- [ ] Confirm contracts still enum `overhead_clear`; raise stroke decision with humans  
- [ ] `git checkout analysis/mediapipe-adapter` (or add worktree); confirm `pyproject.toml` + Session 1 handoff exist  
- [ ] Install contract validator deps and run `validate_examples.py`  
- [ ] Confirm `services/api/` still README-only (no accidental duplicate platform)  
- [ ] Ask humans: (1) stroke enum resolution, (2) ADR sign-off names, (3) whether to merge analysis Session 1 to `main` now  
- [ ] Only then pick **one** lane to implement (prefer P0 contract hygiene or P1 platform — not RAG first)

**Do not:**

- Re-implement the frontend from scratch  
- “Fix” OpenCV by installing both distributions  
- Send videos/landmarks to an LLM  
- Enable `clear.low_arm_extension.v1` without eval evidence  
- Edit design docs without human agreement (Person 1 established rule)  
- Assume Person 2/4 code exists because READMEs describe future ownership  

---

## Appendix A — Key file index

| Path | Notes |
|---|---|
| `README.md` | Architecture + ownership |
| `CONTRIBUTING.md` | PR/branch agreements |
| `docs/TEAM_DECISIONS_AND_RESPONSIBILITIES.md` | Binding team contract |
| `docs/ImplementationPlan.md` | Per-person detailed plan |
| `docs/BADMINTON_MOVEMENT_ASSISTANT_TECHNICAL_DESIGN.md` | Long-form technical design |
| `docs/adr/0001-shared-analysis-contracts.md` | Milestone A decisions |
| `packages/contracts/*` | Integration schemas |
| `apps/web/**` | Person 1 implementation |
| `packages/pose/docs/*` | Person 3 design/plan/handoff (**on analysis branch**) |
| `packages/*/README.md` | Ownership stubs on `main` |
| `services/*/README.md` | Ownership stubs on `main` |
| `infra/local/README.md` | Compose TBD |

## Appendix B — Merged PR index

| # | Author | Title | Target / notes |
|---|---|---|---|
| 1 | mzliu05 | Frontend MVP Fierce UI | `main` via `frontend/upload-flow` |
| 2 | mzliu05 | Multi-stroke + doc wording | `main` |
| 3 | Leohq1 | Person 3 Session 1 Python scaffold | **`analysis/mediapipe-adapter`** |
| 4 | ZZeeZZ1127 | Milestone A contracts | `main` |
| 5 | mzliu05 | Logo favicon/nav | `main` |

## Appendix C — Frontend vs contract mismatch cheat sheet

| Topic | Frontend interim | Contract (PR #4) |
|---|---|---|
| Stroke id | `clear\|smash\|drop` | `overhead_clear` |
| Stroke on result | flat `stroke: StrokeId` + confidences | object `stroke: {type, times, confidence}` |
| Quality | `overall: acceptable\|borderline\|poor`, `notes[]` | `overall: number`, `warnings[]` |
| Severity | `low\|medium\|high` | `minor\|moderate\|major` |
| Evidence | `string` | `{feature,value,unit}[]` |
| Coaching | `recommendations[]` + top-level `citations`/`limitations` | `feedback.{summary,tips,limitations,model,prompt_version}` |
| Error fields | `message`, `retry_may_work`, `recording_remediation` | `safe_message`, `retryable`, `remediation[]` |
| Inconclusive | `inconclusive_reason`, `retake_guidance[]` | use required `error` object |

---

*End of handoff. Update this document when Milestone B lands or when `analysis/mediapipe-adapter` merges to `main`.*
