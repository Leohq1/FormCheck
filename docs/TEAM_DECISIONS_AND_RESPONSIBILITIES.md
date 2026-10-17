# Team Decisions and Responsibilities

This document is the implementation agreement for the four-person FormCheck team. It records the MVP decisions that affect more than one module, assigns ownership, and defines the integration points between contributors.

## 1 MVP scope

The first release will:

- Support a web application.
- Accept an asynchronously processed video upload.
- Analyze one player performing one overhead clear.
- Use MediaPipe as the only MVP pose-estimation implementation.
- Use deterministic, rule-based technique fault detection.
- Use a curated coaching corpus for retrieval-augmented feedback.
- Operate without user accounts or saved progress.
- Run locally first and move to cloud hosting only after evaluation targets pass.
- Keep overhead smash, professional-movement similarity, multi-camera analysis, and live feedback outside the MVP.

The first complete analysis target is one controlled overhead-clear video, one trustworthy feature, one rule-produced finding, one retrieved coaching passage, and one result displayed in the web application.

## 2 Team organization

### Group A — Web application and platform

- Person 1 owns the frontend application.
- Person 2 owns the API, persistence, storage, queue, and local infrastructure.

### Group B — Analysis and coaching

- Person 3 owns video processing, pose estimation, biomechanics, and fault rules.
- Person 4 owns coaching-corpus ingestion, retrieval, feedback generation, and evaluation coordination.

Each person may depend on another person's documented output, but not on that person's internal implementation.

## 3 Repository ownership

| Person | Owned paths |
|---|---|
| Person 1 | `apps/web/` |
| Person 2 | `services/api/`, the worker framework and orchestration in `services/worker/`, database migrations, `infra/local/` |
| Person 3 | `packages/video/`, `packages/pose/`, `packages/biomechanics/`, `packages/rules/`, `evals/pose/`, `evals/rules/`, and analysis-stage logic in `services/worker/analysis/` |
| Person 4 | `packages/rag/`, `corpus/manifests/`, `evals/retrieval/`, `evals/generation/`, `evals/system/`, overall evaluation coordination, and coaching-stage logic in `services/worker/coaching/` |
| Shared | `packages/contracts/`, root configuration, cross-module tests, architecture decisions |

Changes to `packages/contracts/` require review by at least one person from Group A and one person from Group B.

## 4 Shared technical decisions

### 4.1 Technology stack

| Area | Decision |
|---|---|
| Frontend | React, TypeScript, and Vite |
| API | Python 3.12, FastAPI, and Pydantic |
| Worker | Python 3.12 |
| Pose estimation | MediaPipe Pose Landmarker for the MVP |
| Video processing | FFmpeg and ffprobe |
| Database | PostgreSQL with pgvector |
| Job queue | Redis with Dramatiq |
| Object storage | MinIO locally; cloud object storage later |
| Local environment | Docker Compose |
| Frontend tests | Vitest, React Testing Library, and Playwright |
| Python tests | Pytest |

YOLO Pose and MMPose are possible future adapters. They will not run alongside MediaPipe in the MVP.

### 4.2 Shared format conventions

- API and job messages use JSON.
- Field names use `snake_case`.
- All timestamps use UTC ISO 8601 strings.
- Identifiers use UUIDs.
- Confidence values range from `0.0` to `1.0`.
- Every inter-module message includes `schema_version`.
- Final results record pipeline, pose, feature, rule, corpus, embedding, and generation versions.
- Missing or unreliable measurements are marked unavailable; they are never invented.

### 4.3 Analysis status values

```text
created
uploading
queued
preprocessing
pose_estimation
phase_detection
rule_evaluation
retrieval
generating
completed
inconclusive
failed
cancelled
expired
```

`inconclusive` means the system operated correctly but could not produce reliable technique findings from the submitted video. `failed` means a technical problem prevented completion.

### 4.4 Video requirements

- Accepted containers: MP4 and MOV.
- Maximum file size: 100 MB.
- Maximum duration: 30 seconds.
- Minimum recommended resolution: 720p; 1080p preferred.
- Accepted frame rate: 30–120 fps; 60 fps preferred.
- The clip must contain exactly one overhead clear.
- The entire player must remain visible.
- The camera should use a side or rear three-quarter view.
- The camera should remain stable with adequate lighting.
- Edited, variable-speed, or slow-motion footage is not supported initially.

Server-side validation is authoritative. Frontend checks exist only to provide faster feedback.

#### Video-processing ownership and handoff

- Person 2 accepts the upload, performs security and request-level validation, stores the original object privately, creates the job, and supplies storage, retry, cancellation, and progress-reporting facilities.
- Person 3 owns `packages/video/`, including ffprobe inspection, analysis-level eligibility checks, FFmpeg normalization, and generation of the frame-to-source timestamp map.
- Person 3's analysis stage reads the original object through Person 2's storage abstraction and writes normalized artifacts through the same abstraction. It must not implement object-store credentials or lifecycle policy.
- Person 2 must not duplicate FFmpeg or analysis-specific validation inside the API or orchestration layer.

The normalized-video contract is:

- MP4 container with H.264/AVC video and `yuv420p` pixel format.
- Constant frame rate: 60 fps when the inspected source rate is at least 50 fps; otherwise 30 fps. Normalization never claims to create motion detail absent from the source.
- Display rotation applied to pixels and rotation metadata cleared.
- Audio and non-video streams removed.
- Long edge no greater than 1920 pixels, aspect ratio preserved, and output dimensions made even.
- Presentation timestamps begin at zero and are monotonic.
- A JSON timestamp map records each normalized frame index and timestamp together with its nearest source timestamp.
- The inspection result records source hash, duration, codec, dimensions, nominal and average frame rate, rotation, and decode validity.
- The normalization result records the normalized-object key, timestamp-map object key, output hash, output metadata, FFmpeg version, and normalization-contract version.

The canonical object names are `analyses/{analysis_id}/source/{filename}`, `analyses/{analysis_id}/normalized/video.mp4`, and `analyses/{analysis_id}/normalized/timestamps.json`. Person 2 may change the physical storage backend without changing these logical keys.

### 4.5 Access, privacy, and retention

- The MVP has no accounts.
- Each analysis is accessed through an analysis ID and a high-entropy capability token.
- The API stores only a hash of the capability token.
- Raw videos and results expire 24 hours after completion by default.
- Users may delete an analysis before expiration.
- Deletion covers raw and normalized video, landmarks, features, findings, feedback, and related metadata.
- Reuse for evaluation requires separate explicit consent.
- Raw video, frames, capability tokens, and signed storage URLs must not be sent to a language model.
- Videos, model weights, secrets, and copyrighted source documents must not be committed to Git.

### 4.6 AI and RAG boundary

- Person 3's rule engine is the only component allowed to create technique findings.
- The language model may explain and prioritize supplied findings but may not add, remove, reverse, or strengthen them.
- Every coaching recommendation must cite an approved retrieved passage.
- Invalid model output or provider failure must produce a deterministic fallback rather than fail the complete analysis.
- Runtime web search is not part of the coaching path.

## 5 Required shared contracts

The team must implement and approve these files before connecting modules:

```text
packages/contracts/analysis-job.schema.json
packages/contracts/analysis-progress.schema.json
packages/contracts/analysis-findings.schema.json
packages/contracts/analysis-result.schema.json
packages/contracts/analysis-error.schema.json
```

Each schema must include a version, required and optional fields, enumerated values, and at least one valid example.

Person 3 drafts `analysis-findings.schema.json`, but it becomes authoritative only after review by at least one Group A member and one Group B member. Before approval, Person 3 may use a provisional internal model and fixtures marked `schema_version: "0-draft"`; those outputs must not be described as compliant with the shared contract. Person 2 and Person 4 must integrate only against the approved schema version.

### 5.1 Analysis job

Produced by Person 2 and consumed by Person 3.

Required information:

- `schema_version`
- `analysis_id`
- `video_object_key`
- `stroke`
- `handedness`
- `view_hint`
- `pipeline_version`

### 5.2 Analysis progress

Produced by the worker and consumed by Person 2.

Required information:

- `schema_version`
- `analysis_id`
- `stage`
- `progress`, or `null` when exact progress is unavailable
- `message_key`
- `updated_at`

### 5.3 Analysis findings

Produced by Person 3 and consumed by Person 4.

Required information:

- Video-quality report
- Stroke interval and phase estimates
- Feature names, values, units, availability, and confidence
- Rule IDs, labels, severity, confidence, and evidence
- Retrieval tags
- Pose, feature, and rule versions

### 5.4 Analysis result

Produced by Group B, persisted by Person 2, and displayed by Person 1.

Required information:

- Analysis status
- Quality report
- Stroke and phase information
- Findings and evidence
- Coaching summary and prioritized tips
- Source citations
- Limitations
- All relevant versions
- Completion and expiration timestamps

### 5.5 Analysis error

Required information:

- Stable error code
- Safe user-facing message
- Whether retrying may work
- Specific recording remediation when applicable
- Correlation ID for technical support

Internal exception text and stack traces must not be returned to the frontend.

## 6 Person 1 — Frontend instructions

### Objective

Build the browser interface using only the public API and shared contracts.

### First tasks

1. Initialize React, TypeScript, and Vite in `apps/web/`.
2. Generate or write TypeScript types from the shared schemas.
3. Build mock responses for every status and terminal outcome.
4. Implement capture guidance and upload screens.
5. Implement the processing-status screen.
6. Implement completed, inconclusive, failed, expired, and deleted result states.
7. Add frontend unit and browser-flow tests.

### Required screens

- Capture guidance
- Upload form
- Processing status
- Completed result
- Inconclusive result with retake guidance
- Failed analysis
- Expired analysis
- Deletion confirmation and state

### Restrictions

- Do not connect directly to PostgreSQL, Redis, MinIO, the worker, or an AI provider.
- Do not implement pose or fault-detection logic in the browser.
- Do not display internal errors or stack traces.
- Do not store capability tokens in analytics or logging systems.
- Do not present confidence as certainty.

### Person 1 completion criteria

- Every screen works against schema-valid mock responses.
- Keyboard-only navigation works.
- All terminal states render correctly.
- Refreshing during processing restores the analysis when credentials remain available.
- The real API can replace the mock API without changing frontend business logic.

## 7 Person 2 — Platform instructions

### Objective

Build the API and infrastructure that accept videos, create durable jobs, persist results, control access, and delete data.

### First tasks

1. Initialize FastAPI in `services/api/`.
2. Add PostgreSQL, Redis, and MinIO to `infra/local/` with Docker Compose.
3. Create the initial database migration.
4. Implement capability-token generation, hashing, and validation.
5. Implement analysis creation, upload completion, status, result, and deletion endpoints.
6. Implement the job state machine and fake worker.
7. Provide Person 1 with a stable local API.
8. Add lifecycle, authorization, retry, and deletion tests.

### Required endpoints

```http
POST   /api/v1/analyses
POST   /api/v1/analyses/{id}/complete-upload
GET    /api/v1/analyses/{id}
GET    /api/v1/analyses/{id}/result
DELETE /api/v1/analyses/{id}
```

### Fake worker behavior

The fake worker must accept a real `AnalysisJob`, report realistic stages, and return schema-valid examples for completed, inconclusive, and failed outcomes.

### Restrictions

- Do not implement pose, biomechanics, rule, retrieval, or coaching logic inside API routes.
- Do not store videos directly in PostgreSQL.
- Do not persist plaintext capability tokens or signed URLs.
- Do not log user videos, raw landmarks, secrets, or complete model prompts.

### Person 2 completion criteria

- A video can be uploaded and stored privately.
- A durable job survives an API restart.
- Duplicate requests do not create duplicate work.
- Unauthorized callers cannot read or delete an analysis.
- The fake worker completes the end-to-end frontend flow.
- Deletion removes every related object and record.
- The real worker can replace the fake worker without changing the public API.

## 8 Person 3 — Analysis instructions

### Objective

Convert a privately stored source video into a normalized analysis artifact and then into conservative, explainable, rule-produced technique findings.

### First tasks

1. Define the `PoseEstimator` interface and canonical `PoseSequence`.
2. Implement `MediaPipePoseEstimator`.
3. Process one consented team-supplied overhead-clear video when `FORMCHECK_SAMPLE_VIDEO` is available; otherwise keep the asset-dependent test explicitly skipped.
4. Save timestamps, canonical landmarks, coordinates, confidence, and missing-landmark state.
5. Implement initial pose-quality checks.
6. Implement stroke-window and phase prototypes.
7. Implement `dominant_elbow_angle_at_max_wrist_height_deg` and a disabled `clear.low_arm_extension.v1` candidate rule.
8. Produce an `AnalysisFindings` fixture marked `schema_version: "0-draft"` until the shared schema receives cross-group approval.
9. Add unit, property, and evaluation tests.

### Required processing stages

```text
video validation
-> normalization
-> pose estimation
-> quality assessment
-> stroke segmentation
-> phase detection
-> feature extraction
-> rule evaluation
-> AnalysisFindings
```

### Initial feature recommendation

Begin with dominant-elbow angle at maximum dominant-wrist height as a camera-observable arm-extension proxy. Do not begin with precise extension timing until the estimated-contact method has been evaluated.

### Restrictions

- Use MediaPipe only for the MVP.
- Do not treat relative pose depth as metric depth.
- Do not infer a value across long occlusions.
- Do not fire a rule when required feature confidence is too low.
- Do not rely on a language model to decide whether a fault exists.
- Do not enable a rule until it reaches at least 0.80 precision on a held-out coach-labeled set.

### Person 3 completion criteria

- A controlled sample video produces a canonical `PoseSequence`.
- Missing and unreliable landmarks remain explicitly unavailable.
- Handedness, translation, and scale normalization are tested.
- Every finding identifies its rule, evidence, confidence, and version.
- Ineligible videos produce an inconclusive result rather than fabricated findings.
- Person 4 can generate coaching feedback without accessing raw video or pose files.

## 9 Person 4 — RAG and evaluation instructions

### Objective

Turn structured findings into concise, cited coaching guidance and maintain the evaluation framework used to decide what can ship.

### First tasks

1. Select 5–10 trusted, rights-approved coaching sources.
2. Define the source-manifest format in `corpus/manifests/`.
3. Extract, clean, chunk, and tag the approved material.
4. Create embeddings and store them using PostgreSQL and pgvector.
5. Test retrieval using a hard-coded overhead-clear finding.
6. Implement the feedback-generator interface and strict result schema.
7. Add citation validation and deterministic fallback behavior.
8. Coordinate retrieval, generation, and system evaluation sets.

### Source metadata requirements

- Source ID and version
- Title, author, and publisher
- Publication date
- License and allowed use
- Stroke, phase, and fault tags
- Review status and reviewer
- Page or section locator
- Content hash

### Restrictions

- Do not use unapproved or rights-unclear material.
- Do not send raw video, frames, pose trajectories, capability tokens, or object URLs to an AI provider.
- Do not let the language model create or alter a technique finding.
- Do not return a coaching recommendation without a valid retrieved citation.
- Do not fail the entire analysis when the model provider is unavailable.

### Person 4 completion criteria

- Only approved chunks are retrievable.
- A hard-coded finding retrieves relevant passages with locators.
- Every generated recommendation has a valid citation.
- Unsupported model output is rejected.
- Provider failure returns a deterministic fallback.
- Evaluation reports cover retrieval relevance, citation validity, finding faithfulness, unsafe claims, latency, and cost.

## 10 Initial branch plan

```text
frontend/upload-flow
platform/job-lifecycle
analysis/mediapipe-adapter
rag/corpus-retrieval
```

Do not commit feature work directly to `main`. Keep pull requests limited to one owned module or one jointly reviewed contract change.

## 11 First integration milestones

### Milestone A — Contracts

All five shared schemas exist, validate, and contain examples approved by both groups.

### Milestone B — Platform vertical slice

```text
real frontend
-> real API
-> stored upload
-> fake worker
-> sample result
-> real result screen
```

### Milestone C — Analysis prototypes

```text
sample video -> MediaPipe -> PoseSequence
```

and:

```text
hard-coded finding -> approved corpus retrieval -> cited passages
```

### Milestone D — Group B integration

```text
PoseSequence
-> quality and phases
-> features
-> rules
-> AnalysisFindings
-> retrieval
-> feedback
-> AnalysisResult
```

### Milestone E — Full integration

Replace the fake worker with the real analysis pipeline without changing the public API or frontend business logic.

## 12 Decisions intentionally deferred

Do not block the MVP on:

- Cloud-provider selection
- YOLO Pose or MMPose
- GPU hosting
- Overhead smash
- Professional-player similarity scoring
- Professional-video sourcing
- Multi-camera analysis
- User accounts
- Saved progress
- Mobile applications
- A separate managed vector database

Each deferred item requires its own evidence and acceptance criteria before entering the MVP.

## 13 Definition of done for every contribution

A task is complete only when:

- Its public input and output follow the shared schemas.
- Tests cover expected behavior and important failures.
- Another developer can run it from repository documentation.
- Configuration values and environment variables are documented.
- Errors use stable codes and safe messages.
- No secret, participant video, model weight, generated artifact, or unauthorized source material is committed.
- Relevant schema, model, rule, and corpus versions are recorded.
- The owning developer has provided fixtures for downstream consumers.
