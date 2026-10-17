# Four Person Implementation Plan

## 1 Purpose

This plan divides the Badminton Movement Assistant MVP among four developers while keeping the components independently testable and straightforward to integrate.

The team is divided into two groups:

- Group A builds the web application and processing platform.
- Group B builds the video-analysis and coaching engine.

Each person owns a clearly defined module. Communication between modules must use the shared contracts defined in this document.

## 2 Team structure

| Person | Primary responsibility | Group |
|---|---|---|
| Person 1 | Frontend application | Group A |
| Person 2 | Backend API and platform | Group A |
| Person 3 | Pose analysis and fault detection | Group B |
| Person 4 | Coaching RAG and system evaluation | Group B |

The main integration boundary is:

```text
Frontend
   ↓ HTTP
Backend API
   ↓ AnalysisJob
Video analysis
   ↓ AnalysisFindings
RAG feedback
   ↓ AnalysisResult
Backend API
   ↓ HTTP
Frontend
```

## 3 Shared rules for all developers

### 3.1 One repository

Use one repository with the following initial structure:

```text
badminton-movement-assistant/
├── apps/
│   └── web/
├── services/
│   ├── api/
│   └── worker/
├── packages/
│   ├── contracts/
│   ├── video/
│   ├── pose/
│   ├── biomechanics/
│   ├── rules/
│   └── rag/
├── corpus/
│   └── manifests/
├── evals/
├── tests/
├── infra/
│   └── local/
└── docs/
```

### 3.2 Shared contracts

The team must agree on the following schemas before implementing major features:

```text
packages/contracts/
├── analysis-job.schema.json
├── analysis-progress.schema.json
├── analysis-findings.schema.json
├── analysis-result.schema.json
└── analysis-error.schema.json
```

A developer must not change a shared contract without informing every developer whose component consumes it.

Contract changes should be reviewed by at least one member from Group A and one member from Group B.

### 3.3 Versioning

Every completed analysis must record:

- Pipeline version
- Pose-estimator name and version
- Feature-schema version
- Rule-set version
- Corpus version
- Embedding-model version
- Generation-model version
- Result-schema version

This information makes results reproducible and helps identify which change caused a regression.

### 3.4 Definition of done

A task is complete only when:

- The implementation is committed to the shared repository.
- Automated tests cover expected and failure behavior.
- Public inputs and outputs follow the shared schemas.
- Configuration values are documented.
- Errors use agreed error codes.
- No secrets or large media files are committed.
- Another developer can run the component from its documentation.
- Mock data or fixtures are provided for downstream developers.

---

# 4 Person 1 Requirements

## Frontend application owner

### 4.1 Mission

Build the web interface through which users upload an overhead-clear video, monitor processing, view results, understand inconclusive analyses, and delete their data.

The frontend must depend only on the backend API. It must not call the analysis worker, PostgreSQL, Redis, object storage, or the language-model provider directly.

### 4.2 Owned directories

```text
apps/web/
packages/contracts/generated/typescript/
```

Person 1 may contribute to shared contracts but does not own backend implementations.

### 4.3 Required technology

Recommended stack:

- React
- TypeScript
- Vite
- React Router
- TanStack Query or an equivalent request-state library
- A lightweight component and styling approach agreed upon by the team
- Vitest
- React Testing Library
- Playwright for critical end-to-end flows

### 4.4 Required screens

#### Screen 1 — Capture guidance

Explain how to record an eligible video:

- Record one overhead clear.
- Keep the whole body visible.
- Use a side or rear three-quarter view.
- Prefer 60 frames per second.
- Use adequate lighting.
- Keep the camera stable.
- Avoid slow-motion or edited footage.
- Keep the clip between the configured minimum and maximum duration.

The screen must make clear that the system provides technique guidance and not medical advice.

#### Screen 2 — Upload

The upload form must collect:

- Video file
- Stroke type, fixed to overhead clear for the MVP
- Dominant hand
- Camera-view hint
- Consent to process the video

Perform basic client-side checks:

- File extension
- File size
- Required fields
- Consent selection

Client-side validation improves the experience but must not replace server-side validation.

#### Screen 3 — Processing

Show:

- Analysis identifier
- Current processing stage
- Progress when reliable progress exists
- An indeterminate indicator when exact progress is unavailable
- A short explanation of the current stage
- Cancel or delete action
- A message explaining that processing continues if the page is closed

Poll the backend status endpoint using bounded backoff. Stop polling when the analysis reaches a terminal state.

Terminal states are:

```text
completed
failed
cancelled
inconclusive
expired
```

#### Screen 4 — Results

Display:

- Video-quality assessment
- Stroke and phase confidence
- Up to three prioritized findings
- Severity and confidence for each finding
- Plain-language evidence
- Coaching recommendations
- Source citations
- Analysis limitations
- Delete action

Do not present confidence as certainty. Prefer wording such as:

```text
The clip suggests that elbow extension occurred late.
```

Avoid wording such as:

```text
You definitely extend your elbow incorrectly.
```

#### Screen 5 — Inconclusive result

If the system cannot safely analyze the video, show:

- Why the analysis was inconclusive
- Which quality checks failed
- Specific instructions for recording a better video
- A clear option to start again

Do not show technique findings when the analysis is inconclusive.

#### Screen 6 — Failed analysis

Show:

- A user-friendly error message
- Whether retrying with the same video may work
- Whether a new recording is required
- A correlation or support identifier
- Delete action

Do not display stack traces, provider errors, object keys, or internal exception text.

### 4.5 API integration

Person 1 must integrate these endpoints:

```http
POST   /api/v1/analyses
POST   /api/v1/analyses/{id}/complete-upload
GET    /api/v1/analyses/{id}
GET    /api/v1/analyses/{id}/result
DELETE /api/v1/analyses/{id}
```

The frontend must store the returned capability token only for the lifetime of the analysis. The token must never appear in analytics, error-reporting payloads, or application logs.

### 4.6 Development without the real backend

Person 1 must create a mock API layer with fixtures for:

- Successful upload
- Queued analysis
- Each processing stage
- Completed result
- Inconclusive result
- Invalid video
- Expired analysis
- Failed analysis
- Deleted analysis

The mocks must use the real shared schemas. This allows frontend work to continue before the backend and analysis pipeline are complete.

### 4.7 Accessibility requirements

The interface must support:

- Keyboard-only navigation
- Visible focus indicators
- Proper input labels
- Screen-reader status announcements
- Sufficient color contrast
- Status indicators that do not rely only on color
- Accessible error messages
- Reduced-motion preferences where applicable

### 4.8 Person 1 deliverables

- Responsive web application
- Capture-guidance screen
- Upload form
- Processing screen
- Results screen
- Inconclusive and failure screens
- Delete workflow
- Typed API client
- Mock API and result fixtures
- Component tests
- Critical browser-flow tests
- Frontend setup and usage documentation

### 4.9 Acceptance criteria

Person 1’s work is complete when:

- The frontend can run entirely against mock responses.
- A user can complete every main flow without a mouse.
- Refreshing the page during processing restores the analysis when its credentials are still available.
- All terminal states render correctly.
- No internal error details are exposed.
- The frontend works with Person 2’s API without changing its page structure or business logic.

---

# 5 Person 2 Requirements

## Backend API and platform owner

### 5.1 Mission

Build the service that accepts analysis requests, stores videos, manages background jobs, tracks status, saves results, controls access, and deletes expired or user-deleted data.

The API coordinates work. It must not contain pose-analysis or coaching-generation algorithms.

### 5.2 Owned directories

```text
services/api/
services/worker/orchestration/
infra/local/
packages/contracts/generated/python/
database/
```

### 5.3 Required technology

Recommended stack:

- Python 3.12
- FastAPI
- Pydantic
- PostgreSQL
- Alembic
- Redis
- Dramatiq or Celery
- MinIO for local object storage
- Docker Compose
- Structured JSON logging

### 5.4 API responsibilities

#### Create analysis

```http
POST /api/v1/analyses
```

Responsibilities:

- Validate request metadata.
- Validate supported stroke type.
- Require processing consent.
- Generate an analysis ID.
- Generate a high-entropy capability token.
- Store only a hash of the capability token.
- Create the initial database record.
- Return upload instructions.

Example response:

```json
{
  "analysis_id": "019...",
  "capability_token": "secret-returned-once",
  "upload": {
    "method": "PUT",
    "url": "short-lived-signed-url"
  },
  "expires_at": "..."
}
```

For the local prototype, direct API upload is acceptable. The external API response should still be designed so signed uploads can be introduced later.

#### Complete upload

```http
POST /api/v1/analyses/{id}/complete-upload
```

Responsibilities:

- Verify the capability token.
- Confirm the object exists.
- Validate file size and checksum where available.
- Mark the upload as complete.
- Enqueue an analysis job.
- Return `202 Accepted`.

The operation must be idempotent.

#### Analysis status

```http
GET /api/v1/analyses/{id}
```

Return:

- Current status
- Current processing stage
- Safe progress information
- Creation and expiration timestamps
- Quality warnings available so far
- Safe error information when terminal

#### Analysis result

```http
GET /api/v1/analyses/{id}/result
```

Return the completed `AnalysisResult`.

If processing is incomplete, return a defined `409` error. If the result expired, return `410 Gone`.

#### Delete analysis

```http
DELETE /api/v1/analyses/{id}
```

Responsibilities:

- Verify the capability token.
- Mark the analysis for deletion.
- Cancel queued work when possible.
- Prevent new work from starting.
- Create deletion tasks for all stored objects.
- Delete related database records according to the retention policy.
- Return `202 Accepted`.

Repeated deletion requests must be safe.

### 5.5 Database responsibilities

Create migrations and data-access code for:

- Analysis records
- Media-object metadata
- Processing-stage records
- Findings
- Feedback results
- Model and pipeline versions
- Generation usage
- Deletion outbox
- Privacy-safe audit events
- Coaching-source and chunk tables needed by Person 4

Do not store original video data directly in PostgreSQL.

### 5.6 Object-storage responsibilities

Store objects using deterministic keys:

```text
analyses/{analysis_id}/original
analyses/{analysis_id}/normalized.mp4
analyses/{analysis_id}/landmarks.parquet
analyses/{analysis_id}/features.json
analyses/{analysis_id}/result.json
```

Required controls:

- Private storage
- No public bucket access
- Short-lived signed URLs
- File-size limits
- Content-type verification
- Object checksums
- Lifecycle deletion
- Separate local-development bucket

### 5.7 Queue and worker orchestration

Implement the processing state machine:

```text
created
  → uploading
  → queued
  → preprocessing
  → pose_estimation
  → phase_detection
  → rule_evaluation
  → retrieval
  → generating
  → completed
```

Possible terminal alternatives:

```text
failed
cancelled
inconclusive
expired
```

Every background stage must be:

- Idempotent
- Retry-safe
- Time-limited
- Observable
- Associated with the analysis ID
- Prevented from running after deletion or cancellation

### 5.8 Security responsibilities

Implement:

- Capability-token validation
- Token hashing
- Uniform not-found responses
- Request-size limits
- Upload limits
- Rate limits
- Restricted CORS
- Secret management
- Private object storage
- Log filtering
- Input validation
- Media-processing timeouts
- Retention enforcement

Never log:

- Capability tokens
- Signed URLs
- Raw landmark arrays
- Uploaded video contents
- Full generation prompts containing user-derived information

### 5.9 Development without the real analysis pipeline

Person 2 must implement a fake worker that:

- Accepts a real `AnalysisJob`
- Reports realistic progress stages
- Returns sample findings
- Produces a valid `AnalysisResult`
- Simulates failures and inconclusive outcomes

This allows integration with Person 1 before Group B is ready.

### 5.10 Person 2 deliverables

- FastAPI application
- OpenAPI specification
- PostgreSQL schema and migrations
- MinIO integration
- Redis queue integration
- Job-state machine
- Capability-token access
- Upload workflow
- Status and result endpoints
- Deletion workflow
- Retention cleanup
- Fake worker
- Docker Compose environment
- API integration tests
- Platform setup and operations documentation

### 5.11 Acceptance criteria

Person 2’s work is complete when:

- A video can be uploaded and stored.
- A durable job is created.
- Restarting the API does not lose the job.
- The fake worker can complete the full lifecycle.
- Person 1 can use every API endpoint.
- Duplicate requests do not create duplicate work.
- Unauthorized requests cannot access or delete analyses.
- Deletion removes all related objects and records.
- The real worker can replace the fake worker without changing the public API.

---

# 6 Person 3 Requirements

## Pose analysis and fault-detection owner

### 6.1 Mission

Convert a normalized badminton video into reliable, structured technique findings.

Person 3 owns measurement and fault detection. The language model must not be responsible for determining whether a technique fault exists.

### 6.2 Owned directories

```text
packages/video/
packages/pose/
packages/biomechanics/
packages/rules/
services/worker/analysis/
evals/pose/
evals/rules/
```

Person 3 owns pose and rule evaluation code and reports in `evals/pose/` and `evals/rules/`. Person 4 owns `evals/retrieval/`, `evals/generation/`, and `evals/system/` and coordinates the combined product evaluation with Person 3 and the badminton coach.

### 6.3 Pipeline responsibilities

Implement:

```text
Video
  → video validation
  → frame extraction
  → pose estimation
  → pose-quality assessment
  → stroke segmentation
  → phase detection
  → normalization
  → feature extraction
  → rule evaluation
  → AnalysisFindings
```

### 6.4 Video preprocessing

Person 3 owns the inspection and normalization library in `packages/video/`. Person 2 owns upload acceptance, private storage, the worker framework, retries, cancellation, progress, retention, and cleanup. Person 3's analysis stage reads and writes video artifacts through Person 2's storage abstraction; it does not own object-store credentials or lifecycle policy.

The analysis job points to the privately stored source upload. Person 3's first worker stage inspects that object, rejects ineligible media with a stable remediation code, and produces the normalized video and timestamp map.

Target normalized output:

- MP4 container
- H.264/AVC video with `yuv420p` pixel format
- Constant 60 fps when the inspected source rate is at least 50 fps; otherwise constant 30 fps
- Rotation applied
- Audio removed
- Maximum long edge of 1920 pixels
- Aspect ratio preserved and dimensions made even
- Presentation timestamps rebased to zero and monotonic
- Frame-to-source timestamp map preserved

Inspect media before processing:

- Duration
- File size
- Codec
- Resolution
- Frame rate
- Rotation
- Decode validity

The timestamp-map JSON must contain the normalization-contract version and, for each output frame, `frame_index`, `normalized_timestamp_ms`, and `source_timestamp_ms`. The normalization result must record the logical object keys, source and output hashes, output media metadata, FFmpeg version, and normalization-contract version.

Use these logical object names:

```text
analyses/{analysis_id}/source/{filename}
analyses/{analysis_id}/normalized/video.mp4
analyses/{analysis_id}/normalized/timestamps.json
```

Person 2 may replace the physical storage backend without changing these keys.

### 6.5 PoseEstimator interface

Define a common interface:

```python
class PoseEstimator:
    def infer(self, video_path: str) -> PoseSequence:
        ...
```

Implement only:

```python
class MediaPipePoseEstimator(PoseEstimator):
    ...
```

for the MVP.

Do not run MediaPipe and YOLO together. YOLO Pose and MMPose are future alternatives.

The standard `PoseSequence` must include:

- Frame index
- Timestamp
- Canonical landmark name
- Normalized x coordinate
- Normalized y coordinate
- Relative z coordinate when available
- Visibility or confidence
- Missing-landmark status
- Pose-estimator name
- Pose-estimator version

### 6.6 Quality assessment

Produce a `QualityReport` before generating faults.

Evaluate:

- Full-body visibility
- Dominant-arm visibility
- Landmark confidence
- Motion blur
- Camera motion
- Multiple-person interference
- Supported camera view
- Number of stroke candidates
- Whether the clip ends too early

If quality is insufficient, return an inconclusive result with specific remediation codes.

Do not continue into fault detection when required landmarks or phases are unreliable.

### 6.7 Stroke segmentation

The MVP assumes one overhead clear, but the system must locate the stroke window.

Use signals such as:

- Dominant wrist velocity
- Dominant elbow velocity
- Hand height
- Elbow height
- Shoulder motion
- Torso rotation

Return:

- Start timestamp
- End timestamp
- Segmentation confidence
- Number of competing candidates

### 6.8 Phase detection

Estimate:

- Ready and preparation
- Loading
- Acceleration
- Estimated contact
- Follow-through

The estimated contact point is a body-motion proxy. It is not direct observation of racket–shuttle contact.

Each phase must include:

- Estimated timestamp or interval
- Confidence
- Required evidence
- Uncertainty where applicable

Suppress contact-dependent rules when contact uncertainty is too high.

### 6.9 Normalization

Normalize pose measurements so they are less affected by:

- Player height
- Limb length
- Image position
- Image scale
- Left- versus right-handed play
- Small timing differences

Implement:

- Pelvis-centered body coordinates
- Body-scale normalization
- Canonical dominant-hand mirroring
- Joint-angle calculations
- Time-relative phase measurements

Do not treat MediaPipe’s relative z coordinate as accurate metric depth.

### 6.10 Feature extraction

Implement a versioned feature registry.

Initial candidate features:

- Dominant-elbow angle at maximum dominant-wrist height
- Elbow-extension timing
- Hand height
- Shoulder–hip separation
- Trunk lateral lean
- Knee flexion during loading
- Follow-through range
- Phase-duration ratios

Every feature must provide:

```json
{
  "name": "dominant_elbow_angle_at_max_wrist_height_deg",
  "value": 128,
  "unit": "deg",
  "confidence": 0.81,
  "available": true,
  "feature_version": "1"
}
```

### 6.11 Rule engine

A rule must return one of:

```text
not_applicable
pass
finding
inconclusive
```

The first vertical-slice feature is `dominant_elbow_angle_at_max_wrist_height_deg`. It uses maximum wrist height as a camera-observable reach proxy and therefore does not require precise shuttle-contact detection. Contact-dependent timing remains a later feature.

First candidate rule definition:

```yaml
rule_id: clear.low_arm_extension.v1
stroke: overhead_clear
status: candidate
enabled: false

requires:
  - dominant_elbow_angle_at_max_wrist_height_deg

applicable_when:
  supported_view:
    - side
    - rear_three_quarter
  minimum_feature_confidence: 0.70

condition: unset_until_coach_calibration

retrieval_tags:
  - overhead_clear
  - contact_reach
  - arm_extension
```

The production engine must skip a disabled rule. Unit tests may use a clearly named test-only rule with a synthetic threshold to verify engine behavior; that threshold must never appear in production configuration.

Initial rule candidates:

- Low contact reach
- Late elbow extension
- Insufficient trunk rotation
- Limited lower-body loading
- Abbreviated follow-through
- Unstable balance

A candidate rule must not be enabled merely because it sounds biomechanically reasonable. It must pass evaluation against coach-labeled videos.

### 6.12 Output contract

Return `AnalysisFindings`:

Person 3 drafts `packages/contracts/analysis-findings.schema.json`, but the schema becomes authoritative only after review by at least one Group A member and one Group B member. Until that review is complete, Person 3 must use a provisional internal Pydantic model and fixtures with `"schema_version": "0-draft"`. Provisional output must not be described as shared-schema compliant, and downstream integration must target the approved version.

```json
{
  "schema_version": "0-draft",
  "analysis_id": "abc123",
  "quality": {
    "overall": 0.84,
    "warnings": []
  },
  "stroke": {
    "type": "overhead_clear",
    "start_time_ms": 4200,
    "end_time_ms": 7100,
    "contact_time_ms": 6240,
    "confidence": 0.78
  },
  "findings": [
    {
      "rule_id": "clear.low_arm_extension.v1",
      "label": "Low arm extension at maximum reach",
      "severity": "moderate",
      "confidence": 0.81,
      "evidence": [
        {
          "feature": "dominant_elbow_angle_at_max_wrist_height_deg",
          "value": 128,
          "unit": "deg"
        }
      ],
      "retrieval_tags": [
        "overhead_clear",
        "contact_reach",
        "arm_extension"
      ]
    }
  ],
  "versions": {
    "pose_estimator": "mediapipe",
    "feature_schema": "1",
    "rule_set": "1"
  }
}
```

### 6.13 Development without the RAG pipeline

Person 3 must create fixtures containing:

- No findings
- One high-confidence finding
- Multiple findings
- Low-confidence features
- Inconclusive pose quality
- Uncertain contact
- Unsupported camera view

Person 4 will use these fixtures to develop the RAG system before the real pose pipeline is ready.

### 6.14 Person 3 deliverables

- Video-normalization specification
- MediaPipe pose adapter
- Canonical pose schema
- Quality-assessment module
- Stroke segmentation
- Phase detection
- Normalization functions
- Feature registry
- Rule engine
- Initial candidate rules
- Structured findings output
- Unit and property tests
- Pose and rule evaluation scripts
- Analysis-pipeline documentation

### 6.15 External prerequisites and asset policy

Implementation may begin without evaluation media, but end-to-end and rule-enablement claims require external inputs that are not currently in the repository.

- The team supplies at least one consented overhead-clear sample video through a local path named by `FORMCHECK_SAMPLE_VIDEO`. Participant videos must not be committed.
- The MediaPipe model is obtained through a documented setup script or manual download and referenced by `MEDIAPIPE_POSE_MODEL_PATH`. Model binaries must not be committed unless licensing and repository policy are explicitly approved. Record the expected model filename, upstream URL, license, version, and SHA-256 checksum in setup documentation.
- When either asset is absent, asset-dependent tests must skip with a clear reason. Unit tests using synthetic landmarks and metadata must still run.
- A coach-labeled dataset is required before enabling any production fault rule. Until it exists and the rule reaches at least 0.80 precision on the held-out labeled set, the rule remains `candidate` with `enabled: false`.
- A golden expected result is created only after the sample video's consent, view, handedness, and expected stroke window have been reviewed. It must record who labeled it and which pipeline version produced it.

### 6.16 Acceptance criteria

Person 3’s work is complete when:

- The pipeline processes a valid sample video.
- Every provisional output validates against the internal `0-draft` model; integration output validates against the cross-group-approved `AnalysisFindings` schema.
- Missing or unreliable data causes abstention.
- Left- and right-handed normalization is tested.
- Scale and translation invariance are tested.
- Every finding identifies its rule, evidence, confidence, and version.
- Rules meet the agreed precision threshold before being enabled.
- Person 4 can generate feedback without reading raw pose files.

---

# 7 Person 4 Requirements

## Coaching RAG and evaluation owner

### 7.1 Mission

Convert structured technique findings into concise, source-grounded coaching feedback and maintain the evaluation system used to validate the overall product.

Person 4 must not use the language model to discover technique faults from the video. Fault detection belongs to Person 3.

### 7.2 Owned directories

```text
packages/rag/
corpus/manifests/
evals/retrieval/
evals/generation/
evals/system/
services/worker/coaching/
```

### 7.3 Corpus responsibilities

Create a controlled source register for:

- Coaching manuals
- Federation materials
- Licensed coaching articles
- Peer-reviewed biomechanics papers
- Trusted expert-authored resources

Every source must record:

```json
{
  "source_id": "source-001",
  "title": "...",
  "author": "...",
  "publisher": "...",
  "publication_date": "...",
  "license": "...",
  "allowed_use": "...",
  "stroke_tags": ["overhead_clear"],
  "fault_tags": ["elbow_extension"],
  "review_status": "approved",
  "reviewer": "...",
  "review_date": "...",
  "content_hash": "..."
}
```

Do not add scraped or copied material without confirming that the project may store and use it.

### 7.4 Corpus ingestion

Implement:

- Text extraction
- Heading preservation
- Page or section locators
- Noise removal
- Duplicate detection
- Semantic chunking
- Controlled metadata tagging
- Embedding generation
- Index-version tracking

Target chunk size:

- Approximately 250–500 tokens
- Moderate overlap only when context would otherwise be lost
- No mixing of unrelated sections

### 7.5 Retrieval

Use PostgreSQL with pgvector.

Initial retrieval approach:

1. Build a query from Person 3’s findings.
2. Filter by approved review status.
3. Filter by stroke type.
4. Filter using fault and phase tags.
5. Run vector retrieval.
6. Combine with keyword ranking where useful.
7. Remove duplicate passages.
8. Return three to six chunks.

Example query input:

```json
{
  "stroke": "overhead_clear",
  "finding": "late_elbow_extension",
  "phase": "estimated_contact",
  "severity": "moderate",
  "evidence_summary": "Elbow extension peaked 92 ms after the contact proxy."
}
```

Each retrieved chunk must contain:

- Chunk ID
- Source ID
- Text
- Page or section locator
- Relevance score
- Metadata
- Corpus version

### 7.6 Language-model integration

Implement a provider interface:

```python
class FeedbackGenerator:
    def generate(
        self,
        findings: AnalysisFindings,
        evidence: list[EvidenceChunk]
    ) -> Feedback:
        ...
```

Implement:

- Hosted provider adapter selected by the project
- Local Ollama-compatible adapter if time permits
- Strict structured-output validation
- Provider timeouts
- Limited retries
- Usage and cost logging
- Deterministic fallback

The model receives only:

- Structured findings
- Safe evidence summaries
- Quality limitations
- Retrieved coaching chunks

The model must not receive:

- Raw video
- Video frames
- Full pose trajectories
- Capability tokens
- Object-storage URLs
- User identity information

### 7.7 Feedback schema

Return:

```json
{
  "summary": "The clip suggests that elbow extension occurred later than the configured reference range.",
  "tips": [
    {
      "finding_id": "clear.low_arm_extension.v1",
      "title": "Prepare the hitting arm earlier",
      "explanation": "...",
      "practice_cue": "...",
      "citations": [
        {
          "source_id": "source-001",
          "chunk_id": "chunk-014",
          "locator": "Section 4.2"
        }
      ]
    }
  ],
  "limitations": [
    "Contact time was estimated from body motion because the racket and shuttle were not tracked."
  ],
  "model": "...",
  "prompt_version": "1"
}
```

### 7.8 Generation restrictions

The generator must:

- Discuss only findings supplied by Person 3.
- Preserve the finding’s severity and uncertainty.
- Cite every coaching recommendation.
- Use only retrieved source identifiers.
- Avoid medical diagnosis.
- Avoid injury-prevention guarantees.
- Avoid claiming direct observation of racket or shuttle contact.
- Produce no more than three prioritized recommendations.
- Prefer understandable coaching language over raw biomechanical terminology.

The generator must not:

- Invent a new finding.
- Contradict the rule engine.
- Hide an inconclusive result.
- Invent a citation.
- Cite a source that was not retrieved.
- State uncertain measurements as facts.

### 7.9 Deterministic fallback

If the hosted model fails or produces invalid output, return a template-based response using the structured finding and approved retrieved text.

Example:

```text
The analysis detected possible late elbow extension with moderate
confidence. Focus on preparing the hitting arm earlier before the
estimated contact point.

Source: [approved source and locator]
```

A failed language-model call must not cause the entire video analysis to fail.

### 7.10 Evaluation responsibilities

Person 4 coordinates evaluation with Person 3 and the badminton coach.

Create evaluation sets for:

- Video eligibility
- Phase timing
- Fault labels
- Retrieval queries
- Citation correctness
- Feedback faithfulness
- Feedback usefulness
- Unsafe or unsupported coaching

Track:

- Rule precision and recall
- Phase timing error
- Retrieval Recall@5
- Citation validity
- Finding faithfulness
- Unsupported-claim rate
- Inconclusive rate
- End-to-end completion rate
- Processing latency
- AI cost per analysis

Evaluation results must be reported by relevant slices:

- Camera view
- Handedness
- Recording device
- Lighting
- Skill level
- Body visibility
- Rule type

### 7.11 Person 4 deliverables

- Source and rights register
- Corpus-ingestion pipeline
- Chunking and tagging logic
- Embedding pipeline
- pgvector retrieval
- Optional keyword retrieval
- Feedback-generator interface
- Hosted model adapter
- Citation validator
- Deterministic fallback
- RAG and generation tests
- End-to-end evaluation harness
- Evaluation reports
- Corpus and RAG documentation

### 7.12 Acceptance criteria

Person 4’s work is complete when:

- Only approved corpus material is searchable.
- Every recommendation contains a valid citation.
- The generator introduces no new technique findings.
- Invalid model output is rejected.
- Provider failure produces a useful fallback response.
- Retrieval meets the agreed relevance target.
- Finding faithfulness meets the agreed target.
- Person 2 can invoke the coaching pipeline through the shared worker contract.

---

# 8 Shared integration contracts

## 8.1 Analysis job

Produced by Person 2 and consumed by Person 3:

```json
{
  "schema_version": "1",
  "analysis_id": "abc123",
  "video_object_key": "analyses/abc123/normalized.mp4",
  "stroke": "overhead_clear",
  "handedness": "right",
  "view_hint": "rear_three_quarter",
  "pipeline_version": "2026.10.0"
}
```

## 8.2 Analysis findings

Produced by Person 3 and consumed by Person 4:

```json
{
  "schema_version": "1",
  "analysis_id": "abc123",
  "quality": {},
  "stroke": {},
  "features": [],
  "findings": [],
  "versions": {}
}
```

## 8.3 Analysis result

Produced by Group B and consumed by Person 2:

```json
{
  "schema_version": "1",
  "analysis_id": "abc123",
  "status": "completed",
  "quality": {},
  "stroke": {},
  "findings": [],
  "feedback": {},
  "versions": {},
  "completed_at": "..."
}
```

## 8.4 Progress event

Produced by Group B and consumed by Person 2:

```json
{
  "schema_version": "1",
  "analysis_id": "abc123",
  "stage": "pose_estimation",
  "progress": 0.42,
  "message_key": "estimating_pose",
  "updated_at": "..."
}
```

Do not provide numeric progress when the stage cannot measure it reliably. Use `null` for indeterminate progress.

## 8.5 Error result

```json
{
  "schema_version": "1",
  "analysis_id": "abc123",
  "status": "inconclusive",
  "error": {
    "code": "POSE_BODY_CROPPED",
    "safe_message": "The full body was not visible throughout the stroke.",
    "retryable": false,
    "remediation": [
      "Move the camera farther away.",
      "Keep both feet and the hitting arm in the frame."
    ]
  }
}
```

---

# 9 Integration schedule

## Week 1 — Contracts and foundations

All four people:

- Confirm repository structure.
- Agree on shared schemas.
- Agree on status and error codes.
- Add sample request and response fixtures.
- Establish formatting, testing, and review rules.

Person 1:

- Create the web application.
- Implement screens with mock data.

Person 2:

- Create the API and database.
- Start Docker Compose environment.

Person 3:

- Define `PoseSequence`.
- Build a MediaPipe proof of concept.

Person 4:

- Define corpus metadata.
- Build a small approved test corpus.

## Week 2 — Independent vertical slices

Person 1:

- Complete upload, processing, and result views against mocks.

Person 2:

- Complete upload storage, job creation, status, and fake worker.

Person 3:

- Complete preprocessing, pose extraction, and initial quality checks.

Person 4:

- Complete ingestion, embeddings, and basic retrieval.

Integration target:

```text
Real frontend → real API → fake worker → real result UI
```

## Week 3 — Analysis pipeline

Person 1:

- Improve error, accessibility, and inconclusive flows.

Person 2:

- Add retry, cancellation, deletion, and retention behavior.

Person 3:

- Add phases, features, and candidate rules.

Person 4:

- Add generation, citation validation, and fallback.

Integration target:

```text
Sample video → Person 3 findings → Person 4 feedback
```

## Week 4 — Full integration

Connect:

```text
Frontend
→ API
→ object storage
→ queue
→ real analysis worker
→ RAG
→ result database
→ frontend
```

Test:

- Valid video
- Invalid format
- Cropped player
- No clear stroke
- Low-confidence pose
- Worker restart
- Provider timeout
- Deletion during processing
- Expired analysis

## Week 5 — Evaluation and stabilization

- Run the labeled evaluation set.
- Disable rules that do not meet precision requirements.
- Review feedback with a badminton coach.
- Fix integration defects.
- Measure latency and resource use.
- Audit deletion.
- Complete project documentation.

---

# 10 Required collaboration points

## Person 1 and Person 2

Meet to finalize:

- HTTP request and response shapes
- Capability-token handling
- Polling behavior
- Error codes
- Upload method
- Deletion behavior

## Person 2 and Person 3

The boundary is resolved as follows:

- Person 2 owns upload handling, private object storage, job creation, worker orchestration, progress persistence, retries, cancellation, retention, and artifact deletion.
- Person 3 owns ffprobe inspection, analysis eligibility, FFmpeg normalization, timestamp mapping, and all later analysis stages.
- Person 3 reads and writes artifacts only through Person 2's storage abstraction.
- Logical video object names and normalization output are fixed by section 6.4.
- Person 2 produces the analysis-job message. Person 3 reports stage progress through the shared progress contract and checks cancellation between expensive stages.
- Retry policy belongs to Person 2; analysis operations owned by Person 3 must be deterministic and safe to rerun for the same analysis and pipeline version.

## Person 3 and Person 4

Meet to finalize:

- Finding labels
- Retrieval tags
- Evidence summaries
- Severity definitions
- Confidence interpretation
- Rule and source relationships

## Person 4 and Person 1

Meet to finalize:

- Feedback display schema
- Citation format
- User-facing limitations
- Inconclusive messages
- Coaching language

---

# 11 Ownership boundaries

To prevent duplicated or conflicting work:

- Person 1 owns presentation, not analysis logic.
- Person 2 owns orchestration and persistence, not pose or coaching decisions.
- Person 3 owns technique findings, not natural-language coaching generation.
- Person 4 owns retrieval and feedback wording, not whether a fault exists.
- Only Person 3’s rule engine can create technique findings.
- Only Person 2’s API can expose results to the frontend.
- Only Person 2’s platform layer can grant access to stored user data.
- Person 4’s generator can explain findings but cannot modify them.

The cleanest integration rule is:

```text
Each person may depend on another person’s documented output,
but not on that person’s internal implementation.
```
