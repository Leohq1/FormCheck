# FormCheck handoff

Prepared: 2026-10-17 evening (America/Los_Angeles). Git event times below are UTC.

This document is the single briefing for one replacement agent who now owns all four original workstreams. It was written by reading the repository, both diverged branch tips, GitHub pull requests, and the Person 3 design/plan/handoff. It does not start unfinished implementation.

Anything not present in git or in a cited pull-request comment is labeled unverified. Do not treat Person 2’s description of a local API as code you can run from this clone.

## 1. Executive summary

FormCheck is a local-first web application that accepts one short badminton video, estimates body pose, applies deterministic technique rules, and returns coaching text grounded in a curated corpus. There are no user accounts. Access is an analysis ID plus a high-entropy capability token. Raw video and results are meant to expire 24 hours after completion.

The product boundary that must not be crossed: only the rule engine may create a technique finding. A language model may explain findings that already exist. It may not add, remove, reverse, or strengthen them. Missing measurements stay unavailable. MediaPipe relative depth is not metric distance.

**Current status.** No end-to-end analysis exists. The four workstreams are real only to the following extent:

| Workstream | What exists in git | Where |
|---|---|---|
| Person 1, frontend | A mock-driven React app. A later `main` revision adds three strokes and a logo. | `apps/web/` on both tips, contents differ |
| Person 2, platform | Shared JSON Schemas and an ADR on `main` only. No API, database, queue, or Compose files are in any branch. | `packages/contracts/`, `docs/adr/` on `origin/main` |
| Person 3, analysis | Python 3.12/uv workspace and empty package skeletons. Session 1 of 10. | `analysis/mediapipe-adapter` at `33dbd54`, not on `main` |
| Person 4, coaching | No corpus, retrieval, or generator code. One “LGTM!” comment on the analysis PR. | None |

**Immediate priority.** Do not start Session 2, the API, or RAG until you reconcile `analysis/mediapipe-adapter` with `origin/main`. Those tips have diverged, and `main` itself disagrees about the stroke vocabulary. Building Pydantic models or a worker against only one tip will throw away or contradict the other.

The checkout this document was written from is `analysis/mediapipe-adapter` at `33dbd54`, even with `origin/analysis/mediapipe-adapter`. `origin/main` was `d8290b7` and is **not** an ancestor or descendant of this branch.

## 2. Project overview

### 2.1 What the product must do

Authoritative product intent, before the later frontend scope edit, is in:

- `docs/TEAM_DECISIONS_AND_RESPONSIBILITIES.md`
- `docs/ImplementationPlan.md`
- `docs/BADMINTON_MOVEMENT_ASSISTANT_TECHNICAL_DESIGN.md`
- `README.md`
- `CONTRIBUTING.md`

On this branch those files still describe an overhead-clear-only MVP. On `origin/main`, Person 1 edited the same files so the MVP text says clear, smash, and drop. Section 6 records that conflict. The technical design is Version 1.0, dated 16 October 2026.

Intended user journey:

1. Read capture guidance.
2. Upload one MP4 or MOV, at most 100 MB and 30 seconds, with dominant hand, camera-view hint, and processing consent.
3. Receive an analysis ID immediately and poll status.
4. See quality, phase information, at most three findings, evidence, and cited coaching.
5. Delete the analysis, or let the 24-hour retention policy expire it.

`inconclusive` means the pipeline ran and the clip cannot support a reliable finding. `failed` means a technical error. Do not show invented technique advice for either case.

Explicit non-goals in the original design: live feedback, multi-camera 3D, racket or shuttle tracking, rally-wide stroke classification, medical advice, injury prediction, accounts, subscriptions, progress history, and a single imitation score. Professional-video sourcing is unresolved and is a legal gate, not an implementation detail.

### 2.2 Architecture

Modular monolith: one repository, separate processes.

```text
Browser -> API -> private object storage
              -> Redis/Dramatiq job -> analysis worker
                                      -> normalize video
                                      -> MediaPipe pose and quality gates
                                      -> phases, features, deterministic rules
                                      -> retrieval and grounded generation
Browser <- API <- PostgreSQL (pgvector planned)
```

Only the analysis worker reads video objects. The generator receives structured findings and retrieved text, never raw frames, full pose trajectories, capability tokens, or object URLs.

Planned stack, from the team decision document:

| Area | Decision |
|---|---|
| Frontend | React, TypeScript, Vite |
| API | Python 3.12, FastAPI, Pydantic |
| Worker | Python 3.12 |
| Pose | MediaPipe Pose Landmarker only for the MVP |
| Video | FFmpeg and ffprobe, invoked as argument arrays, no Python FFmpeg binding |
| Database | PostgreSQL with pgvector |
| Queue | Redis and Dramatiq |
| Objects | S3-compatible storage. Design docs say MinIO. Person 2 later reported `pgsty/silo` because official MinIO images were gone from Docker Hub. That report is unverified in git. |
| Local env | Docker Compose, not present in git |
| Frontend tests | Vitest, Testing Library, Playwright |
| Python tests | pytest, Hypothesis, Ruff, mypy |

Conventions that are established in the docs and contracts:

- JSON, `snake_case` fields, UTC ISO 8601 timestamps, UUID identifiers.
- Confidence values are `0.0` to `1.0`.
- Inter-module messages carry `schema_version`.
- Ratified messages use `"1"`. Person 3 provisional findings may use `"0-draft"`.
- The frontend mock currently sends `"1.0.0"`. That value is not the ratified contract.
- Capability tokens are returned once, stored only as a hash on the server, and must not be logged or sent to a model.
- Server-side media validation is authoritative. Frontend checks are only fast feedback.

### 2.3 Ownership

| Person | GitHub identity seen in this repo | Group | Owned paths |
|---|---|---|---|
| 1 | `mzliu05` (Matthew Liu), author of frontend PRs | A, web and platform | `apps/web/` |
| 2 | `ZZeeZZ1127` (Zeen), author of the contracts PR and the integration comment on PR #3 | A | `services/api/`, worker orchestration, database, `infra/local/` |
| 3 | `Leohq1` (Leo), author of the analysis scaffold PR | B, analysis and coaching | `packages/video/`, `packages/pose/`, `packages/biomechanics/`, `packages/rules/`, `services/worker/analysis/`, `evals/pose/`, `evals/rules/` |
| 4 | `junyu101`, commenter on PR #3 only | B | `packages/rag/`, `corpus/manifests/`, `evals/retrieval/`, `evals/generation/`, `evals/system/`, `services/worker/coaching/` |

Shared: `packages/contracts/`, root configuration, cross-module tests, architecture decisions. Contract and root Python changes need at least one Group A reviewer and one Group B reviewer.

Each person may depend on another person’s documented output, not on their private implementation.

### 2.4 How the workstreams connect

```text
Person 1 HTTP client
    -> Person 2 API (create, upload, status, result, delete)
        -> AnalysisJob
            -> Person 3 pipeline
                -> AnalysisFindings
                    -> Person 4 retrieval and feedback
                        -> AnalysisResult
                            -> Person 2 persistence
                                -> Person 1 result screen
```

Logical object keys, agreed in team decisions, Person 3’s design, Person 2’s PR #3 comment, and `analysis-job.schema.json` on `main`:

```text
analyses/{analysis_id}/source/{filename}
analyses/{analysis_id}/normalized/video.mp4
analyses/{analysis_id}/normalized/timestamps.json
```

`ImplementationPlan.md` section 5.6 still shows an older flat layout (`original`, `normalized.mp4`, `landmarks.parquet`, `features.json`, `result.json`). ADR 0001 explicitly resolves that conflict in favor of the three keys above. Do not resurrect the flat keys.

Person 3 reads and writes artifacts only through ports Person 2 will adapt. Person 3 must not import MinIO, boto3, Redis, Dramatiq, database models, or API code, and must not decide retries, credentials, retention, or deletion.

## 3. Agent-by-agent work summary

### 3.1 Person 1 — frontend

**Responsibility.** Capture guidance, upload, processing status, completed / inconclusive / failed / expired / deleted results, a typed API client, and mocks so the UI does not wait on the real API.

**Accomplished, and present on this branch (`33dbd54`).** PR #1, merged to `main` at `47e4b2b` on 2026-10-17T22:56:23Z, title `feat(web): FormCheck frontend MVP with Fierce UI`. This branch contains that frontend because it was cut after that merge.

Working tree:

- `apps/web/src/App.tsx` — routes `/`, `/upload`, `/analyses/:analysisId`, unknown paths redirect home. TanStack Query client retries once and does not refetch on window focus.
- `apps/web/src/pages/GuidancePage.tsx` — landing hero, recording tips, medical-advice disclaimer, 24-hour expiry notice. Heading: “Record one clear. Get coaching you can use.”
- `apps/web/src/pages/UploadPage.tsx` — file, dominant hand, side or rear three-quarter view, consent. Stroke is a read-only overhead clear.
- `apps/web/src/pages/AnalysisPage.tsx` — polls progress every 600 ms until a terminal status, then loads the result. Delete requires a second confirmation. Missing `sessionStorage` token shows a credentials warning.
- `apps/web/src/api/client.ts` — `AnalysisApi` interface.
- `apps/web/src/api/index.ts` — if `VITE_API_BASE_URL` is set, use HTTP; otherwise use the in-browser mock.
- `apps/web/src/api/httpClient.ts` — `Authorization: Bearer <capability token>` on every call except create.
- `apps/web/src/api/mockClient.ts` — walks queued → preprocessing → pose_estimation → phase_detection → rule_evaluation → retrieval → generating, 350 ms per stage, then a terminal outcome chosen from the filename.
- `apps/web/src/api/mockOutcome.ts` — filename containing `inconclusive`, `failed`, or `expired` selects that outcome; otherwise `completed`.
- `apps/web/src/api/fixtures/results.ts` — mock completed, inconclusive, failed, and expired payloads. Finding IDs are `oc-reach-001` and `oc-elbow-002`. Severity is `low` / `medium` / `high`. Evidence is a string.
- `apps/web/src/api/session.ts` — token key `formcheck:capability:<analysisId>` in `sessionStorage`.
- `apps/web/src/api/types.ts` — hand-written types, not generated from JSON Schema. Includes a `deleted` status that the shared progress/result enums do not.
- `apps/web/src/lib/videoValidation.ts` — extension, MIME type, 100 MB, empty file. Does not inspect duration, fps, or resolution.
- `apps/web/src/sports/config.ts` — `StrokeId` is only `'overhead_clear'`.
- `apps/web/src/components/` — `AppShell`, `VideoDropzone`, `TipsList`, `StatusBanner`, `ResultsPanel`. Results show at most three findings.
- `apps/web/e2e/happy-path.spec.ts` — guidance → upload `clear.mp4` → analyzing → coaching feedback.
- `apps/web/README.md` — setup and mock-vs-HTTP instructions.
- Styling is Tailwind v4 via `@tailwindcss/vite`. Display font and color tokens live in `apps/web/src/index.css`.
- Images: `apps/web/public/images/hero-badminton.jpg`, `hero-court.jpg`.

**Also accomplished, but only on `origin/main`, not in this checkout.**

- PR #2, merged 2026-10-18T00:57:43Z, `feat(web): support clear, smash, and drop strokes`. Stroke IDs become `'clear' | 'smash' | 'drop'`. Upload uses a dropdown. Landing heading becomes “Record one clip. Get coaching you can use.” The same PR rewrote README, technical design, implementation plan, team decisions, and `packages/rules/README.md` so the MVP text includes smash and drop. Commit messages: `18b04eb`, `e6b4a78`.
- PR #5, merged as `d8290b7`, `feat(web): add FormCheck shuttle logo to nav and favicon`. Adds `apps/web/src/components/LogoMark.tsx` and several `apps/web/public/images/logo-*` and favicon files. Removes `apps/web/public/favicon.svg`.

**Unfinished for Person 1.**

- Types and fixtures do not match `packages/contracts` on `main`. ADR 0001 says the current UI shapes are presentation mappings and must be remapped after sign-off.
- No generated TypeScript types.
- No real upload of file bytes. The mock ignores the file contents after validation. The HTTP client posts JSON metadata and then calls complete-upload; it does not PUT the file to `upload_url`.
- Accessibility is partial: labels, alerts, and keyboard-reachable controls exist. A full WCAG pass is not evidenced.
- Playwright covers only the happy path.
- `cancelled` is a terminal type but has no dedicated result panel.

### 3.2 Person 2 — platform

**Responsibility.** FastAPI, capability tokens, private upload, job state machine, PostgreSQL, Redis/Dramatiq, object storage, deletion, retention, and a fake worker that returns schema-valid results until Group B is ready.

**Accomplished in git.** Only Milestone A contract files, on `origin/main` via PR #4 (`36e4486`, merge `827d030`, 2026-10-18T02:05:29Z), title `feat(contracts): Milestone A shared analysis contracts (sign-off)`.

Files, all absent from `analysis/mediapipe-adapter`:

- `docs/adr/README.md`
- `docs/adr/0001-shared-analysis-contracts.md`
- `packages/contracts/common.schema.json`
- `packages/contracts/analysis-job.schema.json`
- `packages/contracts/analysis-progress.schema.json`
- `packages/contracts/analysis-findings.schema.json`
- `packages/contracts/analysis-result.schema.json`
- `packages/contracts/analysis-error.schema.json`
- `packages/contracts/examples/*.json` (seven examples)
- `packages/contracts/validate_examples.py`
- `packages/contracts/requirements.txt` (`jsonschema==4.23.0`, `referencing==0.35.1`)

On this branch, `packages/contracts/README.md` only lists the planned filenames. `services/api/README.md`, `services/worker/README.md`, and `infra/local/README.md` are placeholders.

The remote branch `origin/platform/job-lifecycle` exists and points at `47e4b2b` (the PR #1 merge). It contains no API code. `git log` shows no commits unique to that branch.

**Reported by Person 2, not found in this repository.** On 2026-10-18T01:17:55Z, `ZZeeZZ1127` commented on PR #3 (https://github.com/Leohq1/FormCheck/pull/3#issuecomment-6244137592). The comment says a local Compose stack is running with Postgres, Redis, S3-compatible storage via `pgsty/silo`, an API, and a fake worker, and that code lives under `services/formcheck/` with `formcheck.storage.ObjectStorage` and Dramatiq. ADR 0001 likewise mentions `services/formcheck/schemas.py` and `uuid.uuid4()` as the current ID generator. A search of every GitHub branch and of `C:\Users\haoqi\UW` found no `schemas.py` and no `services/formcheck` tree. Treat that stack as Person 2’s unpublished local work. Do not reimplement it from the comment, and do not assume it matches the schemas that were merged later the same night.

The same comment approves the analysis package layout and says Person 3 may keep building packages against fakes. It says storage can accept uploads and delete objects, but does not yet expose “download source / write normalized artifact.” That gap is expected until Session 9 ports exist. It is not a defect in the Python scaffold.

**Unfinished for Person 2.**

- Publish or discard the unpublished local stack, then align it to the schemas.
- Production adapters for Person 3’s future ports.
- Alembic, idempotency keys, retention sweeper, and API integration tests. PR #4 lists these as follow-ups.
- Fill the ADR reviewer table. It is still `_TBD_` even though the PR merged. GitHub `reviews` on PR #4 was an empty list at investigation time. The ADR status line still says “Proposed (awaiting cross-group sign-off).” Merging the files is not the same as the sign-off procedure the PR body required.
- Fake worker outcomes that validate against `analysis-result.schema.json`.
- Endpoints named in the plan: `POST /api/v1/analyses`, `POST /api/v1/analyses/{id}/complete-upload`, `GET /api/v1/analyses/{id}`, `GET /api/v1/analyses/{id}/result`, `DELETE /api/v1/analyses/{id}`.

### 3.3 Person 3 — analysis

**Responsibility.** Turn a privately stored source video into normalized media and then into conservative, explainable findings. Detailed design and the ten-session plan:

- `packages/pose/docs/person3-analysis-pipeline-design.md`
- `packages/pose/docs/person3-analysis-pipeline-implementation-plan.md`
- `packages/pose/docs/person3-session-1-handoff.md`

**Accomplished.** Session 1 only. PR #3 merged into `analysis/mediapipe-adapter` at `33dbd54` on 2026-10-18T01:50:15Z. It was not merged to `main`. Implementation commits:

- `4241373` — `build: initialize person 3 python workspace`
- `6bf18c2` — `fix: keep a single headless OpenCV provider`
- `f7cd4f6` — `docs: add session 1 analysis handoff`

What Session 1 actually contains:

- Root project `formcheck-analysis` `0.1.0` in `pyproject.toml`.
- `requires-python = ">=3.12,<3.13"`, `.python-version` = `3.12`.
- One committed `uv.lock`. No `requirements.txt` for this project. Do not introduce a pip workflow for these packages.
- Base dependencies: `numpy>=2.5.4,<3`, `pydantic>=2.14.1,<3`.
- `analysis` group: `mediapipe>=1.1.1,<2`, `opencv-python-headless>=5.0.0.93,<6`, `scipy>=1.18.1,<2`.
- `test` group: `pytest>=9.1.1,<10`, `hypothesis>=6.170.1,<7`.
- `dev` group includes `analysis`, `test`, `ruff>=0.17.1,<0.18`, `mypy>=2.4.0,<3`.
- setuptools discovery for five packages. pytest markers `integration` and `assets`. Ruff target 3.12, line length 100. mypy `strict = true`.
- Importable skeletons, each only `__version__ = "0.1.0"`:
  - `packages/video/formcheck_video/`
  - `packages/pose/formcheck_pose/`
  - `packages/biomechanics/formcheck_biomechanics/`
  - `packages/rules/formcheck_rules/`
  - `services/worker/analysis/formcheck_analysis/`
- `services/worker/analysis/tests/test_imports.py` — import/version smoke test, and a test that exactly one installed distribution owns `cv2/` files and that distribution is `opencv-python-headless`.
- `.local/README.md` — uv commands, asset policy, and the OpenCV exclusion note. `.gitignore` ignores `.local/*` except that README, plus `.worktrees/`, media, models, and virtualenvs.

There are no `models.py` files, no FFmpeg calls, no MediaPipe inference, no features, and no rules.

**Review of PR #3.** Person 2 commented an ownership approval (section 3.2). Person 4 (`junyu101`) commented “LGTM!” at 2026-10-18T01:48:42Z (https://github.com/Leohq1/FormCheck/pull/3#issuecomment-6244412379). Neither submitted a formal GitHub review object. The pull request was merged anyway.

**Unfinished.** Sessions 2–10 in the implementation plan. Summary and acceptance criteria are in section 8. Session 2 was the agreed next step after PR #3 merged, but it is now blocked by the branch and stroke conflicts in section 6. The plan forbids drafting `analysis-findings.schema.json` inside those sessions. Person 2 has since added a provisional copy of that schema on `main`. Session 2 should target that shape once the branches are combined, not invent a second findings document.

A leftover git worktree remains at `.worktrees/session-1-python-scaffold`, branch `analysis/session-1-python-scaffold`, commit `f7cd4f6`. The session-1 handoff said to keep it until review finished. Review has finished. The worktree is now redundant with `33dbd54`. Do not commit `.venv` or `.local/tooling` from it. uv 0.13.1 was installed only inside that ignored worktree path for Session 1. Other machines should install uv themselves.

### 3.4 Person 4 — coaching and evaluation

**Responsibility.** Rights-cleared corpus, chunking, embeddings, pgvector retrieval, a `FeedbackGenerator` provider adapter, citation checks, deterministic fallback when the model fails, and evaluation coordination.

**Accomplished.** Nothing in the tree. `packages/rag/README.md`, `corpus/manifests/README.md`, and `evals/README.md` are ownership notes. The only Person 4 action found is the “LGTM!” on PR #3. There is no corpus manifest, no embedding code, and no eval harness.

**Unfinished.** The whole Person 4 plan in `docs/ImplementationPlan.md` section 7. Do not send video, frames, pose trajectories, tokens, or object URLs to a provider. Empty `findings` must not become invented coaching. A failed model call must not fail the whole analysis.

The technical design recommends OpenAI `text-embedding-3-small` and “GPT-6 Luna” as of 16 October 2026, with prices cited from that date. Those vendor names and prices are time-stamped claims in the design doc. Reconfirm them before any provider integration. The result example on `main` uses `model: "gpt-placeholder"` and does not lock a real model.

## 4. Consolidated implementation details

### 4.1 Frontend behavior that exists today (this branch)

Create flow in `UploadPage`:

1. `validateVideoFile` plus a consent check.
2. `createAnalysis` with `stroke: 'overhead_clear'`, handedness, `view_hint`, `consent: true`, filename, content type, byte size.
3. Store the returned capability token.
4. `completeUpload`.
5. Navigate to `/analyses/:id`.

Mock create returns `schema_version: '1.0.0'`, a UUID, a 24-byte hex token, and `upload_url: mock://upload/<id>`. Status advances from `createdAt` using wall clock time, so a refresh continues the same timeline.

HTTP client base path is `VITE_API_BASE_URL` with a trailing slash stripped. Paths are `/api/v1/analyses` and the four subpaths in section 3.2. Non-OK responses throw `Error('API request failed (<status>)')`. The client does not parse the shared error object.

`AnalysisPage` treats `completed`, `inconclusive`, `failed`, `expired`, `cancelled`, and `deleted` as terminal. It fetches a result only for completed, inconclusive, failed, and expired. Inconclusive uses `inconclusive_reason`, `quality.notes`, and `retake_guidance`. Those fields are not on the ratified result schema. The ratified schema carries that guidance in `error.safe_message` and `error.remediation`, and requires `error` to be non-null for inconclusive, failed, expired, and cancelled. Completed results must have `error: null`.

`formatConfidence` renders “About N% model confidence”. The UI copy tries not to present confidence as certainty.

### 4.2 Contract shapes on `origin/main`

JSON Schema draft 2020-12. Validate with the registry in `validate_examples.py`. Do not validate one file in isolation; `$ref`s use relative `$id`s.

`common.schema.json` holds `analysisId`, `qualityReport`, `strokeInfo`, `evidenceItem`, and `finding`.

| Message | `schema_version` | Produced by | Consumed by | Notable constraints |
|---|---|---|---|---|
| `AnalysisJob` | const `"1"` | Person 2 | Person 3 | `stroke` enum is only `overhead_clear`. `video_object_key` must match `^analyses/[^/]+/source/.+$`. Handedness `left`/`right`. View `side` / `rear_three_quarter`. |
| `AnalysisProgress` | const `"1"` | worker | Person 2 | `stage` is the pipeline enum including terminal states. `progress` is a number in `[0,1]` or null. `message_key` is string or null. |
| `AnalysisFindings` | `"0-draft"` or `"1"` | Person 3 | Person 4 | Description says the file is a provisional scaffold and is authoritative only after Group A and Group B review. `features[]` items require `name`, `value` (number or null), `unit`, `confidence` (number or null), `available`, `feature_version`. `findings` max 3. `versions` requires `pose_estimator`, `feature_schema`, `rule_set`. |
| `AnalysisResult` | const `"1"` | Group B via Person 2 | Person 1 | `feedback` is `{summary, tips, limitations, model, prompt_version}`. Each tip requires `finding_id`, `title`, `explanation`, `practice_cue`, and at least one citation `{source_id, chunk_id, locator}`. Tips max 3. `versions.result_schema` const `"1"`. |
| `AnalysisError` | none; it is embedded | worker / API | UI | `code`, `safe_message`, `retryable`, `remediation[]`, `correlation_id`, optional `details` object. |

`strokeInfo.type` is enum `["overhead_clear"]` even on `main`, which is the same branch whose prose docs now say clear, smash, and drop.

`qualityReport.overall` is a number from 0 to 1 plus a `warnings` string array. The frontend mock uses `'acceptable' | 'borderline' | 'poor'` and `notes`.

`finding.severity` is `minor | moderate | major`. Evidence is an array of `{feature, value, unit}` with at least one item. The frontend mock uses `low | medium | high` and a single evidence string. ADR 0001 says the UI may map severity for display.

`pose_estimator` is one string that embeds name and version, for example `mediapipe-0.10`. Do not split it unless evaluation later requires it.

Findings and result schemas do **not** include phase intervals, candidate-rule diagnostics, an eligibility flag, or an unavailability reason on features. Person 3’s working design wants all of those internally. Diagnostics must stay out of production JSON. Phases and unavailability reasons are a real schema gap: either extend `common.schema.json` with cross-group review, or keep them internal and only emit the ratified projection.

The findings example includes a populated `clear.low_arm_extension.v1` finding. That example is a schema illustration. Person 3’s design forbids that rule from appearing in production `findings` until it is enabled and reaches at least 0.80 held-out coach-labeled precision. Do not copy the example into a production assembler.

### 4.3 Normalized video contract

Owned by `packages/video/`, specified in `packages/video/README.md` and the Person 3 design. Not implemented.

- MP4, H.264/AVC, `yuv420p`.
- Constant 60 fps when inspected source rate is at least 50 fps; otherwise constant 30 fps. Do not claim frames the source did not have.
- Display rotation baked into pixels; rotation metadata cleared.
- Audio and non-video streams removed.
- Long edge at most 1920, aspect ratio preserved, even dimensions.
- Presentation timestamps rebased to zero and monotonic.
- Timestamp map: normalization-contract version plus, per output frame, `frame_index`, `normalized_timestamp_ms`, `source_timestamp_ms`.
- Mapping uses decoded source presentation timestamps. Each output timestamp maps to the nearest source PTS. Exact ties choose the earlier source timestamp. Duplicate mappings and gaps are valid. The map does not claim interpolated frames.
- Sub-720p source may continue with warning code `VIDEO_LOW_RESOLUTION`.
- Accepted containers: MP4 and MOV only. Frame rate outside 30–120 fps is ineligible (`VIDEO_FPS_UNSUPPORTED`).
- Other stable codes already named in the plan: `VIDEO_UNSUPPORTED_CONTAINER`, `VIDEO_TOO_LARGE`, `VIDEO_TOO_LONG`, `VIDEO_DECODE_FAILED`.
- Inclusive maxima: 100 MB and 30 seconds.
- FFmpeg and ffprobe are system tools. uv does not install them. Invoke them with argument lists and `shell=False`.

### 4.4 Analysis pipeline that is specified and not built

Stage order:

```text
materialize source
-> inspect and validate
-> normalize and write video.mp4 + timestamps.json
-> pose
-> quality
-> segment one stroke
-> phases
-> coordinate normalization
-> features
-> rules
-> AnalysisFindings
```

Check cancellation before and after each expensive stage. Progress reports use stable message keys and `progress` or null. They must not include filesystem paths or raw exceptions.

First feature, version `1`, unit `deg`:

```text
dominant_elbow_angle_at_max_wrist_height_deg
```

It is the shoulder–elbow–wrist angle at the highest reliable dominant-wrist point inside the stroke window. It does not depend on shuttle contact. If the maximum is missing, low-confidence, or unstable across the configured neighborhood, return `available: false` and no invented number. Reason string planned internally: `unstable_or_unreliable_maximum`.

Handedness and view come from `AnalysisJob`. Person 3 does not infer them. Left-handed clips are mirrored into a canonical dominant-right frame. Coordinates for biomechanics are pelvis-centered and scaled by torso length, with shoulder width as a documented fallback. Relative `z` is stored as non-metric and excluded from this feature and rule.

Candidate rule, not to be enabled:

```text
rule_id: clear.low_arm_extension.v1
status: candidate
enabled: false
calibration_status: not_calibrated
```

Supported views: `side`, `rear_three_quarter`. Minimum feature confidence 0.70. No production threshold. Retrieval tags: `overhead_clear`, `contact_reach`, `arm_extension`.

Development diagnostics may say `would_trigger`, `would_pass`, `not_applicable`, or `inconclusive`. The plan’s plumbing threshold is `development_low_arm_extension_threshold_deg = 140.0`, labeled `provisional_test_only`. An available angle below 140 degrees may yield `would_trigger` in development only. Production serialization has no diagnostics field. A disabled rule must never construct a `Finding`.

Quality gates in the design (body coverage, landmark confidence, blur, camera motion, one stroke candidate, supported view) are versioned engineering defaults, not validated badminton thresholds. The plan names the first config `quality.v1-provisional` and `phases.v1-provisional`.

Provisional ports, to be written in Session 9 and not before, in `services/worker/analysis/ports.py`:

```text
ArtifactReader.materialize(object_key) -> Path
ArtifactWriter.put_file(object_key, local_path, content_type) -> ArtifactMetadata
CancellationPort.raise_if_cancelled(analysis_id)
ProgressPort.report(analysis_id, stage, progress, message_key)
```

Local fakes go in `testing_ports.py`. Person 2 must approve signatures before anyone claims production worker integration.

### 4.5 What the frontend HTTP client assumes, and what the job schema actually is

These are different messages. Do not merge them into one type.

The browser create request, as coded, is metadata: stroke, handedness, view, consent, filename, content type, byte size. The worker job, as schematized, is: `schema_version`, `analysis_id`, `video_object_key`, stroke, handedness, view, `pipeline_version`. Person 2 creates the job after the upload exists. Person 3 consumes the job, not the browser form body.

The frontend’s Bearer header is an interim client choice. No API in git confirms it. When the API appears, match whatever Person 2 actually implemented, then keep the token out of logs.

## 5. Decision log

| Decision | Why | Alternative rejected | Trade-off |
|---|---|---|---|
| Modular monolith, local first | Four people can integrate without operating a cloud | Microservices, or cloud on day one | Cloud migration is deferred until evaluation gates pass. |
| No accounts; capability token hashed at rest | MVP privacy and simpler auth | User accounts | A leaked URL-plus-token exposes one analysis until expiry or deletion. |
| MediaPipe Pose Landmarker only | CPU-friendly local prototype behind a `PoseEstimator` protocol | Running YOLO or MMPose beside it | 2D and relative-3D limits. Fast motion and occlusion can force abstention. |
| Rules own findings; LLM only phrases them | Testable faults, less hallucinated coaching | Letting the model watch video or invent faults | Coaching is only as good as the rules and the corpus. Empty findings stay empty. |
| First feature is elbow angle at max wrist height | Camera-observable reach proxy that does not need racket–shuttle contact | Starting with extension timing relative to contact | Contact-timing rules stay blocked until the contact proxy is evaluated. |
| `clear.low_arm_extension.v1` stays disabled | A plausible threshold is not evidence | Enabling the rule because the example JSON shows it firing | Production findings are empty until a coach-labeled held-out precision of at least 0.80. |
| Diagnostics structurally absent from production JSON | Person 4 must not turn `would_trigger` into a fault | An optional diagnostics field “that Person 4 promises to ignore” | Development mode needs a separate serializer. |
| Internal findings may be `0-draft` until cross-group approval | Unblocks Person 3 without pretending the shared contract is frozen | Waiting to write any models until Milestone A is signed | Two shapes can drift. `main` now has a provisional schema; this branch does not. |
| One OpenCV provider: `opencv-python-headless` | MediaPipe 1.1.1 pulled `opencv-contrib-python`. Both install `cv2/` with different native-module hashes. Imports succeeded while the environment was unsafe. | Keeping both distributions, or switching the direct dependency to contrib | uv exclusion is scoped to MediaPipe `1.1.1` only. A MediaPipe upgrade must revisit it. Real Pose Landmarker inference has not been run. If inference needs a contrib-only API, stop and review; do not install both. |
| uv, one `uv.lock`, Python `>=3.12,<3.13` | Reproducible scientific stack | `requirements.txt` or unconstrained pip | Root config is shared. Later dependency adds still need cross-group review. |
| FFmpeg subprocess argument arrays | Avoid shell injection and a binding dependency | A Python FFmpeg wrapper, or shell strings | Tests must stub a `ProcessRunner`. Developers must install FFmpeg themselves. |
| Timestamp map uses nearest source PTS, earlier PTS on ties | Nominal fps is wrong for variable-frame-rate input | `frame_index / fps` | Duplicated and dropped frames must be tested explicitly. |
| Below 720p warns but stays eligible | Analysis quality gates still run | Hard-rejecting sub-720p | Low resolution can later fail pose quality and become inconclusive rather than `failed`. |
| Handedness and view are job inputs | Inferring them from motion is unreliable for the MVP | Auto view classification | A wrong user hint silently changes mirroring and which rules apply. |
| Severity enum `minor`/`moderate`/`major` | ADR 0001 resolved a doc conflict | Frontend `low`/`medium`/`high` as the contract | UI must map labels. Do not persist the display words as the contract. |
| Quality `overall` is a 0–1 number | ADR 0001 | Frontend enum `acceptable`/`borderline`/`poor` | UI must format the number. Do not store the enum in the contract. |
| Inconclusive results require an `error` object | Implementation plan section 8.5; validator enforces it | Separate `inconclusive_reason` and `retake_guidance` fields | The current React result panel will not render ratified inconclusive payloads without a remap. |
| Object keys use `source/` and `normalized/` | Team decisions section 4.4 and ADR 0001 | Implementation plan section 5.6 flat keys | Any unpublished Person 2 code that used flat keys has to move. |
| `analysis_id` format `uuid`, version not pinned | Current unpublished backend was reported to emit v4; tech design prefers v7 | Schema `pattern` locking v7 now | Time-ordered IDs are a later generator change, not a schema break. |
| Asset files are never committed or auto-downloaded | Consent, licensing, and repo size | Baking a sample video or `.task` model into git | Tests that need them must `pytest.skip` with the missing variable named. |
| Smash and drop were originally out of the MVP | Calibration cost; design section 24 | Building three strokes before one rule is precise | Person 1’s PR #2 reversed the prose and the UI. The JSON Schemas did not follow. See section 6. |

Approaches that already failed:

- Installing both OpenCV distributions. `import cv2` passed, but two distributions owned the same files. Fixed in `6bf18c2` by a version-scoped uv `exclude-dependencies` entry and a metadata test. After the fix, environments created before the exclusion needed `uv sync --locked --all-groups --reinstall-package opencv-python-headless` once.
- Treating verbal “LGTM” as a completed ADR sign-off. PR #4’s body said to fill the reviewer table before merge. The merged ADR still has `_TBD_`. Do not describe the schemas as fully ratified.

## 6. Current project state

### 6.1 Branch map

```text
origin/main                         d8290b7
  PR #5 logo
  PR #4 contracts          (overhead_clear in JSON Schema)
  PR #2 three-stroke UI    (stroke ids clear | smash | drop)
  PR #1 frontend MVP

origin/analysis/mediapipe-adapter   33dbd54   <-- this checkout
  PR #3 Python scaffold
  PR #1 frontend MVP
  does not contain PR #2, #4, or #5

origin/platform/job-lifecycle       47e4b2b   (same as PR #1 merge; no platform code)
origin/analysis/session-1-python-scaffold
  checked out in .worktrees/session-1-python-scaffold at f7cd4f6
```

Neither tip contains the other’s unique work. A merge will conflict in the docs Person 1 edited and in `packages/rules/README.md`. The Python files should merge cleanly because they are new. The contract files should merge cleanly because they are new on `main`. The frontend stroke and logo changes will not be present until `main` is merged in.

### 6.2 Stroke-vocabulary conflict (unresolved)

Three incompatible statements are all “latest” in some branch:

| Source | Stroke value | Scope |
|---|---|---|
| This branch’s UI, Person 3 design, and team docs | `overhead_clear` | One overhead clear. Smash is an explicit non-goal. |
| `origin/main` prose and `apps/web/src/sports/config.ts` after PR #2 | `clear`, `smash`, `drop` | Three strokes. Smash removed from the deferred list. |
| `origin/main` JSON Schemas after PR #4, which is newer than PR #2 | `overhead_clear` only | Job, findings, and result examples all use `overhead_clear`. |

PR #4 did not revert PR #2’s documentation edits. `main` is internally inconsistent. This handoff does not pick a winner. Do not hard-code a new enum until the team chooses one. If you must keep Person 3 moving before that meeting, the safer alignment target is the JSON Schema (`overhead_clear`), because Person 3’s approved design, the job contract, and the findings example all use it, and smash/drop have no rules, features, or corpus. Label that as a recommendation, not a team decision. The frontend IDs `clear` / `smash` / `drop` will not validate against `AnalysisJob.stroke`.

### 6.3 Schema authority conflict (unresolved)

Person 3’s plan says: do not draft the shared findings schema inside Sessions 1–10; use internal Pydantic models tagged `0-draft`.

Person 2 then committed `analysis-findings.schema.json` on `main` and wrote in the file that it is provisional until Group A and Group B review it. The ADR reviewer table is empty. So the file exists, and its own text says it is not yet the authoritative contract.

Use it as the shape to be compatible with. Do not mark outputs `schema_version: "1"` for findings until a real cross-group acceptance is recorded. Job, progress, result, and error schemas are what Person 2 intends the platform to enforce; they also lack the ADR sign-off table.

### 6.4 What was verified, and what this investigation did not re-run

Session 1 handoff, `packages/pose/docs/person3-session-1-handoff.md`, records a Windows CPython 3.12.10 run: `uv lock --check`, locked sync of 39 packages, imports of cv2, mediapipe, numpy, pydantic, and scipy, pytest 2 passed, ruff, and mypy on the five skeletons. This handoff author did not re-run that suite.

This handoff author did not run `npm test`, Playwright, or `validate_examples.py`. The contract validator cannot be run on this branch because the schema files are not checked out here.

No sample video and no Pose Landmarker `.task` file are in git. `.local/README.md` recommends:

```text
FORMCHECK_SAMPLE_VIDEO=.local/samples/overhead_clear.mp4
MEDIAPIPE_POSE_MODEL_PATH=.local/models/pose_landmarker_full.task
```

Neither path was present for Session 1. Do not commit them.

## 7. Known issues and risks

1. **Diverged branches.** Continuing Session 2 only on `analysis/mediapipe-adapter` ignores the contract files and the newer UI. Merging `main` into the analysis branch is the integration step, and it will conflict in docs.
2. **Stroke ID split,** section 6.2. A job created from the `main` UI would not match the job schema.
3. **Frontend result shape does not match `analysis-result.schema.json`.** Severity, evidence, quality, feedback versus recommendations, error field names, `schema_version` `1.0.0` versus `1`, and inconclusive fields. ADR 0001 already assigns the remap to Person 1 after sign-off.
4. **HTTP client never uploads bytes** and collapses every error into a status-code string.
5. **Milestone A sign-off is incomplete.** Schemas are merged; the ADR still says proposed; reviewer rows are blank; GitHub recorded no approving reviews on PR #4.
6. **Findings schema is thinner than the analysis design.** No phases, no feature unavailability reason, no top-level eligibility. The example finding shows a rule that production code must not emit yet.
7. **Feature schema requires `unit` even when `value` is null.** Person 3’s plan says unavailable features have `value is None`. Confirm during Session 2 whether `unit` may be `""` or whether the schema should allow null units. Do not invent values to satisfy the required string.
8. **OpenCV exclusion is unproven for inference.** Session 4 must run Pose Landmarker with headless OpenCV. Imports are not that test.
9. **Unpublished Person 2 stack.** Comments describe behavior you cannot see. Reimplementing it from the comment risks a second, conflicting API.
10. **No coach labels, no consented sample, no model file, no rights-cleared corpus.** End-to-end success and any enabled rule are blocked on those external inputs.
11. **Contact is a body-motion proxy.** Timing rules that depend on it stay suppressed when uncertainty is high. Do not describe contact as observed racket–shuttle impact.
12. **Worktree and local uv.** `.worktrees/` is gitignored. Do not add those environments to a commit.
13. **Design-doc model names.** “GPT-6 Luna” and the October 2026 prices are unverified against a live provider in this repo. The contract example uses a placeholder model string.

## 8. Remaining tasks

Ordered by dependency. Acceptance criteria are the bar for calling the task done, not a claim that it is started.

### P0 — Reconcile the tree

**State.** Not started. Both tips are valid work.

**Do this.** Fetch `origin/main`. Merge or rebase `origin/main` into `analysis/mediapipe-adapter` (or the reverse, if the team wants contracts on `main` to receive the Python project). Resolve doc conflicts by keeping both facts visible until the stroke decision exists: do not silently keep only “three strokes” or only “overhead clear.”

**Done when.** One branch contains the Python scaffold, the six schemas, the ADR, the logo, and a written note of the stroke conflict. `git status` is clean. No media or model files are staged.

### P0 — Stroke decision

**State.** Unresolved. Depends on a human choice. The recommendation in section 6.2 is not that choice.

**Done when.** `sports/config.ts`, `AnalysisJob.stroke`, `strokeInfo.type`, team docs, and Person 3 models use one enum, and smash/drop are either in that enum with an explicit “not analyzed yet” behavior or removed from the upload form.

### P1 — Person 3 Session 2: domain models

**State.** Specified, not started. Depends on P0 so models are not written against a branch that lacks the schema.

**Files the plan names:**

- `packages/pose/formcheck_pose/models.py`
- `packages/biomechanics/formcheck_biomechanics/models.py`
- `packages/rules/formcheck_rules/models.py`
- `services/worker/analysis/formcheck_analysis/models.py`
- tests under each package plus `services/worker/analysis/tests/test_findings_model.py`
- fixture `services/worker/analysis/tests/fixtures/analysis_findings_no_findings.json`

**Produce.** `PoseLandmark`, `PoseFrame`, `PoseSequence`, `QualityReport`, `StrokeWindow`, `PhaseEstimate`, `PhaseSet`, `FeatureValue`, `Evidence`, `Finding`, `CandidateRuleEvaluation`, `AnalysisFindings`, `AnalysisDiagnostics`, `VersionInfo`, `Handedness`, `ViewHint`.

**Acceptance.** Pose frames reject negative index/timestamp and non-monotonic sequences. Unavailable landmarks have no coordinates and a missing reason. `relative_z` is labeled non-metric. Confidence is in `[0,1]`. Unavailable features have `value is None`. `Finding` and `CandidateRuleEvaluation` are different types. `to_production_dict()` uses `schema_version: "0-draft"`, includes quality, stroke, features, findings, and versions, and omits diagnostics. `to_development_dict()` may include diagnostics. Non-finite numbers fail. The no-findings fixture round-trips. Do not add video or MediaPipe code in this session. Do not enable `clear.low_arm_extension.v1`.

**Stop** after tests, lint, mypy, and a review of that session. The original plan says one session per commit and review.

### P1 — Record contract sign-off, or keep the schema provisional

**State.** Files merged, table empty.

**Done when.** Either the ADR reviewer table has real names and dates and the findings schema description is updated, or the team explicitly agrees the schema stays provisional and Person 3 keeps emitting `0-draft`. Do not flip findings to `"1"` by default.

### P2 — Person 3 Sessions 3–8

**State.** Specified in `packages/pose/docs/person3-analysis-pipeline-implementation-plan.md`. Not started. Each session depends on the previous.

| Session | Commit message in the plan | Done when |
|---|---|---|
| 3 Video | `feat: add deterministic video normalization` | Argument-list subprocesses, eligibility codes, nearest-PTS map including ties/duplicates/drops, even-dimension H.264 command, atomic outputs. Sample test skips with `FORMCHECK_SAMPLE_VIDEO is not set or does not point to a file` when the variable is missing. |
| 4 Pose | `feat: add canonical mediapipe pose adapter` | Protocol plus mapper. Unit tests use a fake backend. Headless OpenCV reads frames. No implicit model download. Model test skips with `MEDIAPIPE_POSE_MODEL_PATH is not set or does not point to a file`. When the model exists, inference returns one frame per timestamp and does not require a person to be detected. This session is the OpenCV inference gate. |
| 5 Quality and normalization | `feat: add conservative pose quality and normalization` | Known 90/180 degree angles, translation and scale invariance, left/right mirror, unavailable degenerate geometry, `quality.v1-provisional`. The MVP trusts `view_hint`; it does not classify camera view. |
| 6 Stroke and phases | `feat: add overhead clear segmentation and phase prototypes` | Two comparable peaks return inconclusive with `competing_candidates=2`. Contact is always labeled estimated. Uncertain contact does not invalidate the first feature. |
| 7 Feature | `feat: add versioned arm extension feature` | Known geometry returns degrees. Unreliable maximum returns `available=false` and no nearby substitute. |
| 8 Rules | `feat: isolate candidate rule diagnostics` | Test-only calibrated rule covers the four production outcomes. Catalog entry is disabled and `not_calibrated`. `would_trigger` never appears in production findings or production JSON. |

### P2 — Person 2 platform, only after the unpublished tree is located

**State.** Not in git. Do not start a second API from scratch if Person 2 still has the local stack. Ask them for the branch or patch first.

**Done when.** The five HTTP endpoints exist, tokens are hashed, objects are private, a durable job survives API restart, duplicate requests do not duplicate work, unauthorized callers cannot read or delete, deletion removes related objects, and a fake worker returns payloads that `validate_examples.py` would accept. The public API can later swap the fake worker for Person 3 without frontend business-logic changes.

### P2 — Person 1 remap

**State.** Blocked on the stroke decision and on a stable result schema.

**Done when.** The mock and HTTP client speak the contract: numeric quality, structured evidence, `feedback.tips`, error field names, `schema_version` `"1"`, inconclusive rendered from `error`, and file bytes actually uploaded when a real `upload_url` exists. Keyboard-only path still works. Filename tricks may remain for mocks, but fixture bodies must be schema-valid.

### P3 — Person 3 Session 9 and Person 4 in parallel

Session 9 composes the pipeline behind provisional ports and a development CLI `formcheck-analyze`. It is not production integration. Person 2 reviews the port signatures before any adapter work is called complete. Cancellation after source materialization must skip normalization and must not emit a preprocessing-completed progress event.

Person 4 can draft corpus metadata and a rights register without the pose pipeline, using the findings example as a hard-coded query. Do not ingest unclear copyrighted text. Do not implement generation that invents findings.

### P3 — Person 3 Session 10

Evaluation metrics and an asset-gated end-to-end test. `eligible_for_enablement` is a report flag only, true when held-out precision is at least 0.80 with nonzero support. The metric code must not flip `enabled` by itself. The end-to-end test skips in one message that lists every missing requirement among the two environment variables and FFmpeg/ffprobe. When assets exist, development output is valid `0-draft`, `findings` is empty, and any candidate evaluation is disabled.

### P4 — Integration and calibration

Replace the fake worker only after ports are approved and adapters exist. Enable a rule only after coach labels exist. Ship coaching only when citations validate. Original evaluation targets in the technical design (precision ≥ 0.80 per rule, citation validity 100%, and so on) still apply and have no dataset yet.

## 9. Unified execution plan

Do these in order. Do not parallelize items that touch the same docs or the stroke enum.

1. Read this file, then `packages/pose/docs/person3-analysis-pipeline-design.md` and the implementation plan. Skim ADR 0001 from `origin/main` (`git show origin/main:docs/adr/0001-shared-analysis-contracts.md`).
2. Fetch and merge `origin/main` into the analysis branch. Resolve conflicts without deleting either the contract files or the Python project.
3. Write down the stroke decision. If the team is unavailable, leave the enum as `overhead_clear` in new Python models, keep the `main` UI change intact but incompatible, and put a one-line warning in the upload page’s neighboring docs rather than silently supporting smash.
4. Finish or explicitly postpone ADR sign-off.
5. Implement Session 2 with failing tests first. Stop and review.
6. Sessions 3 through 8, one at a time, each with the verification command in the plan.
7. In parallel with sessions 3–8, only if Person 2’s unpublished tree is obtained: align that API to the schemas and teach the frontend to upload bytes and render the ratified result. If the tree cannot be obtained, implement the platform from `docs/ImplementationPlan.md` section 5 against the schemas, and do not also keep a second private stack.
8. Person 4: source register and a fixture-driven retriever. No provider calls until a findings fixture exists and a model choice is reconfirmed.
9. Session 9 ports, then Person 2 adapters, then Session 10 metrics.
10. Only then connect the real worker and consider enabling a rule.

Overlap to avoid:

- Person 1 must not invent pose logic in the browser.
- Person 2 must not reimplement FFmpeg eligibility inside the API.
- Person 3 must not import storage or queue clients.
- Person 4 must not read landmarks to invent a fault.
- Nobody enables `clear.low_arm_extension.v1` because an example or a 140 degree development threshold exists.

## 10. Environment and testing guide

### 10.1 This checkout

```text
Branch: analysis/mediapipe-adapter
Commit: 33dbd54
Remote: https://github.com/Leohq1/FormCheck
```

Python tooling is documented for Session 1. From the repository root, after installing uv and Python 3.12:

```powershell
uv python install 3.12
uv lock --check
uv sync --locked --all-groups
uv run --locked python -c "import cv2, mediapipe, numpy, pydantic, scipy"
uv run --locked pytest
uv run --locked ruff check packages services/worker/analysis
uv run --locked mypy packages/video/formcheck_video packages/pose/formcheck_pose packages/biomechanics/formcheck_biomechanics packages/rules/formcheck_rules services/worker/analysis/formcheck_analysis
```

Expected at Session 1 scope: pytest `2 passed`. These commands were not re-run while writing this handoff.

If an older virtualenv still has contrib OpenCV files mixed in:

```powershell
uv sync --locked --all-groups --reinstall-package opencv-python-headless
```

FFmpeg and ffprobe are separate installs. They are unnecessary until Session 3.

Frontend, from `apps/web`:

```powershell
npm install
npm run dev
npm test
npm run test:e2e
```

Dev server default is `http://localhost:5173`. First Playwright run may need `npx playwright install chromium`. Mock mode is the default. Point at an API only when one exists:

```powershell
$env:VITE_API_BASE_URL = "http://localhost:8000"
npm run dev
```

That URL comes from Person 2’s comment. Nothing in git listens there.

Contract checks, only after `main` is merged:

```powershell
pip install -r packages/contracts/requirements.txt
python packages/contracts/validate_examples.py
```

PR #4 says this should print 7 example pairs plus 3 semantic guards. Not run from this checkout.

### 10.2 Assets

Never commit videos, frames, pose dumps, model binaries, secrets, or copyrighted corpus files. `.gitignore` already ignores `.env`, `.env.*` except `.env.example`, `.local/*` except `.local/README.md`, `.venv`, media extensions, `models/`, `data/`, `uploads/`, `artifacts/`, and database data directories.

Optional later environment variables:

```powershell
$env:FORMCHECK_SAMPLE_VIDEO = (Resolve-Path '.local/samples/overhead_clear.mp4').Path
$env:MEDIAPIPE_POSE_MODEL_PATH = (Resolve-Path '.local/models/pose_landmarker_full.task').Path
```

Record model URL, version, license, download date, and SHA-256 privately. Record participant consent privately. Tests must skip, not fail, when a variable is missing.

### 10.3 Commands that are not available

There is no Compose file, no migration command, no corpus ingest command, and no `formcheck-analyze` CLI yet. Do not document them as if they work.

## 11. Critical context and lessons learned

- The OpenCV double-install is the concrete failure already paid for. Any lockfile change that lets `opencv-contrib-python` back in fails `test_analysis_environment_has_one_cv2_provider`.
- Successful `import mediapipe` does not mean Pose Landmarker runs on headless OpenCV.
- “Example findings” in schemas and frontend fixtures are demos. Several of them show faults the rule engine is not allowed to emit.
- A missed coaching tip is safer than a confident wrong one. Abstain when confidence or landmarks are insufficient. Do not interpolate across long occlusions.
- Relative `z` stays out of the first feature.
- Development `would_trigger` is not a finding. If a serializer has a diagnostics parameter, production code will eventually pass one. The plan avoids that by giving the production assembler no such parameter.
- The 140 degree threshold is a plumbing fixture. It must not ship in production configuration and must not grow severity bands.
- Person 2’s comment is an integration agreement (package layout, object keys, “build against fakes,” Session 9 gate). It is not a code drop.
- Person 4’s “LGTM!” accepts the Python workspace. It does not accept a findings schema, retrieval tags, or severity semantics in detail. Those still need a Group B pass when the schema is declared final.
- Frontend filename switches (`inconclusive`, `failed`, `expired`) are demo hooks. Do not require real videos to be renamed for the real worker.
- Do not log tokens, signed URLs, raw landmark arrays, video bytes, or full prompts.
- Feedback is technique guidance, not medical advice. The landing page and footer already say this. Keep that sentence when remapping the UI.
- Vendor model names in the October 16 design doc go stale. Pin a real model only after an evaluation run, and record the date.

## 12. First actions for the new agent

1. Confirm the checkout: `git status -sb` should show `analysis/mediapipe-adapter` at `33dbd54`, even with origin. If it is behind, fast-forward. Do not reset or delete the worktree unless the user asks.
2. Read, in this order: this file, `packages/pose/docs/person3-session-1-handoff.md`, `packages/pose/docs/person3-analysis-pipeline-design.md` sections 8–16, and `git show origin/main:docs/adr/0001-shared-analysis-contracts.md`.
3. `git fetch origin` and `git log --oneline HEAD..origin/main` plus `git log --oneline origin/main..HEAD`. You should see PR #2, #4, and #5 on `main`, and the Python scaffold only on this branch.
4. Merge `origin/main` into this branch when the user agrees. Expect conflicts in `README.md`, `docs/ImplementationPlan.md`, `docs/TEAM_DECISIONS_AND_RESPONSIBILITIES.md`, `docs/BADMINTON_MOVEMENT_ASSISTANT_TECHNICAL_DESIGN.md`, and `packages/rules/README.md`.
5. Do not implement Session 2 until that merge is done or the user explicitly says to stay on this branch and ignore `main`.
6. Do not create a FastAPI app until you have asked whether `services/formcheck/` still exists unpublished on Person 2’s machine.
7. Do not add smash/drop rules. Do not set `clear.low_arm_extension.v1` to enabled. Do not commit a video or a `.task` file.
8. When implementation is allowed, start Session 2 from the plan: write the failing model tests first, then the Pydantic models, and stop before video and MediaPipe.
9. After Session 2, run the pytest, ruff, and mypy commands in section 10.1 and include the new test paths.
10. Leave `docs/HANDOFF.md` updated if a stroke decision or a branch merge changes the facts in sections 6 and 8. Do not let this file drift into another undocumented conflict.
