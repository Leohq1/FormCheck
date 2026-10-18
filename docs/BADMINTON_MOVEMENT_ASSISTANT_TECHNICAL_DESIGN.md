# Badminton Movement Assistant

Technical design for a local first developer prototype

Version 1.0  |  16 October 2026

## Purpose

This document defines an implementable web system that accepts a badminton video, analyzes one selected stroke (clear, smash, or drop), detects a bounded set of technique faults with deterministic rules, and returns source-grounded coaching feedback. It is written for the developers who will build and evaluate the prototype, including the interfaces needed to replace early components later.

## Recommended direction

Build a modular monolith first: a React web client, a Python FastAPI service, a durable background worker, PostgreSQL with pgvector, object storage, and a pose-analysis pipeline based on MediaPipe Pose Landmarker. Keep movement-similarity scoring as a later extension. Use a provider-neutral RAG adapter with OpenAI text-embedding-3-small and GPT-6 Luna as the hosted default, with a local Ollama-compatible alternative when privacy or offline operation matters more than response quality and setup simplicity.

## Decision status

| **Area** | **Decision** |
| --- | --- |
| MVP | Clear, smash, or drop; one player; one uploaded clip; asynchronous result |
| Stroke selection | User selects clear, smash, or drop at upload |
| Analysis | Rule-based technique fault detection |
| RAG | Curated, versioned coaching sources with inline citations |
| Identity | No accounts or longitudinal history |
| Hosting | Local prototype first; cloud deployment later |
| Open decision | Rights-cleared professional reference footage sourcing |

# Contents

1 Executive summary

2 Product scope and requirements

3 System architecture

4 End to end workflow

5 Video intake and preprocessing

6 Pose estimation and quality gating

7 Stroke segmentation and phase detection

8 Feature engineering and normalization

9 Rule based fault detection

10 Reference movement strategy

11 Coaching knowledge and RAG

12 AI model and provider strategy

13 API design

14 Data model and schemas

15 Frontend design

16 Local development and hosting

17 Cloud deployment

18 Observability and operations

19 Security privacy and safety

20 Evaluation and acceptance criteria

21 Testing strategy

22 Delivery roadmap

23 Risks and mitigations

24 Open decisions

25 Appendices

## Reading guide

Sections 3–12 explain the processing pipeline. Sections 13–17 specify implementation contracts and deployment. Sections 18–23 define the operational and quality gates needed before the prototype should be trusted by testers.

# 1 Executive summary

The prototype analyzes technique; it does not diagnose injury, measure shuttle speed, or replace a coach. A user uploads a short side or rear three-quarter video containing one clear, smash, or drop and selects that stroke type at upload. The server validates and normalizes the video, estimates body landmarks per frame, identifies the stroke window and key phases, computes interpretable kinematic features, and evaluates conservative rules. Each triggered rule becomes a structured finding with a confidence score and evidence. A retrieval pipeline then selects relevant passages from a curated coaching corpus and asks a language model to express only those findings as concise, cited feedback.

The architecture deliberately separates measurement, interpretation, and language generation. Pose estimation produces observations. Deterministic code produces fault findings. Retrieval supplies trusted coaching evidence. The language model may rephrase and prioritize but must not invent a biomechanical finding. This separation makes behavior testable, reduces hallucination risk, and lets the team improve pose models or language providers independently.

Success means that qualified clear, smash, and drop clips complete reliably, rejected clips fail with actionable capture guidance, supported faults meet agreed precision on an expert-labeled set, and every coaching claim is traceable to both motion evidence and a curated source passage.

# 2 Product scope and requirements

## 2.1 Primary user journey

1. Open the web application and review capture guidance.

1. Upload a short video, select the stroke type (clear, smash, or drop), and confirm the clip contains that single stroke.

1. Receive an analysis identifier immediately and view queued or processing status.

1. Review video quality checks, phase markers, detected findings, confidence, and cited coaching guidance.

1. Delete the analysis and uploaded media, or let the configured retention policy expire it.

## 2.2 Functional requirements

| **ID** | **Requirement** | **MVP acceptance** |
| --- | --- | --- |
| FR 1 | Accept MP4 or MOV uploads through an asynchronous job API. | Valid upload returns 202 and an analysis ID. |
| FR 2 | Validate duration, size, codec, frame rate, resolution, and visible-player quality. | Invalid media returns a specific remediation code. |
| FR 3 | Analyze a single selected stroke (clear, smash, or drop). | The system produces phase landmarks or an inconclusive result. |
| FR 4 | Apply versioned rule-based fault detectors. | Every finding names the rule, threshold, value, and confidence. |
| FR 5 | Generate grounded feedback from curated sources. | Every recommendation cites at least one approved chunk. |
| FR 6 | Operate without user accounts. | Analysis is accessed by a high-entropy capability token. |
| FR 7 | Allow deletion. | Delete removes job artifacts and schedules object deletion. |

## 2.3 Nonfunctional requirements

- Local developer setup completes from a documented container configuration.

- A typical 10–20 second 1080p clip should finish within 90 seconds on the reference development machine; publish measured percentiles instead of promising a fixed SLA.

- Jobs are idempotent and resumable. A process restart does not lose accepted work.

- Raw video, landmarks, findings, retrieved chunks, prompts, model IDs, and rule versions are traceable for evaluation.

- The UI meets WCAG 2.2 AA fundamentals: keyboard flow, labeled controls, readable contrast, and non-color status cues.

## 2.4 Explicit non goals

- Live on-court feedback, multi-camera 3D reconstruction, racket or shuttle tracking, match analytics, automatic stroke classification across a rally, medical advice, injury prediction, social sharing, accounts, subscriptions, and progress history.

- A single numerical imitation score. Such a score hides meaningful differences and encourages overfitting to one professional body or style.

- Automatically scraping or redistributing broadcast or social-media footage without documented rights.

# 3 System architecture

The MVP is a modular monolith deployed as separate processes from one codebase. This reduces operational overhead while preserving clear internal boundaries.

| **Layer** | **Component** | **Responsibility** |
| --- | --- | --- |
| Client | React and TypeScript web app | Capture guidance, upload, progress polling, result presentation, deletion. |
| API | FastAPI | Validation, signed upload coordination, job creation, status and result endpoints. |
| Queue | Redis plus Dramatiq or Celery | Durable background execution, retries, cancellation, progress events. |
| Worker | Python analysis worker | FFmpeg preprocessing, pose inference, phases, features, rules, retrieval, generation. |
| Data | PostgreSQL and pgvector | Job metadata, findings, corpus metadata, embeddings, audit events. |
| Objects | Local MinIO then cloud object storage | Uploads, normalized media, landmark files, optional annotated preview. |
| AI | Provider adapters | Embedding and grounded response generation; local alternative. |
| Ops | Structured logs and OpenTelemetry | Correlation, latency, failure, quality, cost and model telemetry. |

## Architecture flow

```text
Browser -> API -> object storage
              |
              +-> job queue -> analysis worker
                              |-> FFmpeg preprocessing
                              |-> pose and quality gates
                              |-> phase and feature extraction
                              |-> deterministic rule engine
                              |-> pgvector retrieval
                              +-> grounded LLM generation
Browser <- status and result API <- PostgreSQL
```

## Boundary rule

Only the analysis worker reads video objects. The RAG generator receives structured findings and retrieved text, never raw frames or full pose trajectories. This is both a privacy control and a correctness constraint.

# 4 End to end workflow

| **Stage** | **Input** | **Output** | **Failure behavior** |
| --- | --- | --- | --- |
| 1 Intake | Video plus client metadata | Upload record and object | Reject unsupported size/type. |
| 2 Normalize | Uploaded object | CFR MP4 and frame index | Mark media invalid; retain diagnostic. |
| 3 Pose | Frames | Landmarks and confidence | Quality gate or partial inference. |
| 4 Segment | Landmark sequence | Stroke interval and phases | Return inconclusive if ambiguous. |
| 5 Features | Aligned stroke | Versioned feature vector | Flag unavailable dimensions. |
| 6 Rules | Features plus context | Structured findings | Do not infer when confidence is low. |
| 7 Retrieve | Finding labels | Ranked source chunks | Fall back to finding-only explanation. |
| 8 Generate | Findings plus chunks | Cited coaching response | Schema validation; retry once; deterministic fallback. |
| 9 Publish | All artifacts | Result JSON and UI | Atomic status transition to completed. |

## Job state machine

```text
created -> uploading -> queued -> preprocessing -> pose_estimation
       -> phase_detection -> rule_evaluation -> retrieval -> generating
       -> completed
Any active state -> failed | cancelled | inconclusive
```

State transitions are compare-and-set updates. A worker records stage start and completion, heartbeat time, attempt count, and error code. Retried stages write to deterministic artifact paths and upsert results so that retries do not duplicate findings.

# 5 Video intake and preprocessing

## 5.1 Capture contract

- Target 10–20 seconds and exactly one selected stroke (clear, smash, or drop).

- Prefer 60 fps; accept 30–120 fps. Minimum 720p; 1080p recommended.

- Place the camera 4–8 m away at roughly hip-to-chest height, using side or rear three-quarter view.

- Keep the whole body visible from ready position through follow-through. Use good lighting and a stable camera.

- Avoid other people crossing the subject and avoid cuts, slow motion, zoom changes, or variable-speed editing.

## 5.2 Validation and normalization

Inspect streams with ffprobe. Enforce configurable limits, initially 100 MB and 30 seconds. Decode server-side regardless of extension; never trust MIME type alone. Normalize to H.264, yuv420p, constant 60 fps when source quality allows, rotation applied, audio removed, and a maximum long edge of 1920 pixels. Preserve a frame-time map from normalized frames to source timestamps.

## 5.3 Quality gates

| **Gate** | **Suggested MVP rule** | **User-facing remediation** |
| --- | --- | --- |
| Body coverage | Required torso and dominant arm landmarks present in >= 85% of candidate frames. | Move farther back and keep the whole body in frame. |
| Pose confidence | Median selected-landmark visibility >= 0.65. | Improve lighting and reduce occlusion. |
| Motion blur | Sharpness below calibrated threshold around too many key frames. | Use brighter lighting and higher frame rate. |
| Camera motion | Background motion exceeds calibrated threshold. | Use a tripod or stable support. |
| Stroke count | Exactly one high-confidence candidate. | Upload a clip containing one complete clear. |
| View suitability | Estimated viewpoint within supported band. | Record from side or rear three-quarter view. |

# 6 Pose estimation and quality gating

Use MediaPipe Pose Landmarker as the first implementation because it is easy to run locally, provides 2D and relative 3D landmarks, supports video tracking, and avoids a server GPU for the initial prototype. Wrap it behind PoseEstimator so YOLO pose, MMPose, or a fine-tuned model can be evaluated without changing downstream schemas.

Store, per frame, timestamp; normalized x, y, z; visibility; presence; and an estimator version. Smooth only after preserving raw output. A Savitzky-Golay filter or One Euro filter may be applied to continuous joint trajectories, with parameters fixed in the pipeline version. Never interpolate across long occlusions.

## Coordinate frames

- Image frame: normalized pixel coordinates for crop and coverage checks.

- Body frame: translate to pelvis midpoint and scale by shoulder width or torso length.

- Orientation-normalized frame: estimate the shoulder and hip axes; mirror left-handed clips to a canonical dominant-hand representation.

- Angle representation: compute joint angles from three landmarks; use signed planar angles only when camera view is eligible.

## Confidence propagation

Every derived feature carries availability and confidence. A feature confidence is a conservative aggregation of its contributing landmark visibility, temporal stability, and phase certainty. A rule cannot fire when required feature confidence is below its configured minimum.

# 7 Stroke segmentation and phase detection

The upload contract simplifies segmentation to one stroke, but the worker must still locate it. First compute motion-energy candidates from wrist, elbow, shoulder, and torso velocities. Then identify a contiguous window containing preparation, acceleration, estimated contact, and follow-through. For the MVP strokes, contact is a body-kinematic proxy because the system does not track the shuttle or racket.

| **Phase** | **Operational definition** | **Primary signals** |
| --- | --- | --- |
| Ready and preparation | Stable base followed by dominant elbow rise and shoulder external rotation. | Wrist/elbow velocity, elbow height, shoulder angle. |
| Loading | Torso and shoulder rotation increase before acceleration. | Shoulder-hip separation, trunk lean, elbow flexion. |
| Acceleration | Dominant wrist velocity rises toward its local maximum. | Wrist speed, elbow extension rate. |
| Estimated contact | Calibrated offset near the wrist-speed peak and greatest reach. | Wrist speed peak, arm extension, hand height. |
| Follow-through | Arm decelerates and crosses or descends after contact. | Wrist deceleration, shoulder rotation, hand path. |

Phase detection returns distributions or confidence intervals, not false precision. Manual phase labels from a small training set should calibrate offsets and thresholds. If contact uncertainty exceeds the allowed window, contact-dependent rules are suppressed and the result explains that limitation.

# 8 Feature engineering and normalization

Features must be interpretable, stable across body sizes, and linked to coaching concepts. Keep a feature registry with definition, units, window, required landmarks, supported viewpoints, handedness handling, and version.

| **Feature** | **Definition** | **Use** |
| --- | --- | --- |
| Elbow angle at contact | Angle shoulder-elbow-wrist within contact window. | Arm extension. |
| Elbow extension timing | Time of maximum extension rate relative to estimated contact. | Late or early extension. |
| Hand height | Dominant wrist vertical position relative to body scale. | Contact reach. |
| Shoulder-hip separation | Signed angle between shoulder and hip axes. | Trunk rotation/loading. |
| Trunk lateral lean | Torso axis relative to vertical in supported view. | Balance and contact position. |
| Knee flexion at loading | Hip-knee-ankle angle in preparation window. | Lower-body loading. |
| Follow-through range | Dominant wrist path after contact, body-normalized. | Deceleration and completion. |
| Temporal ratios | Phase durations divided by total stroke duration. | Timing independent of absolute speed. |

Do not treat MediaPipe world z as metric depth without calibration. Features sensitive to depth should be unavailable unless a supported viewpoint and reliability study justify them. Racket-face angle, grip, pronation, and shuttle-contact location are out of scope for body-only pose.

# 9 Rule based fault detection

A rule is a versioned, testable function over features and quality context. It returns not_applicable, pass, finding, or inconclusive. Thresholds begin as expert hypotheses and become production candidates only after calibration on labeled clips.

```text
rule_id: clear.late_elbow_extension.v1
stroke: clear
requires: [elbow_extension_timing, contact_time]
applicable_when:
  view: [side, rear_three_quarter]
  min_feature_confidence: 0.70
condition:
  elbow_extension_peak_ms_after_contact > 45
severity_bands: {minor: 45, moderate: 80, major: 120}
message_key: late_elbow_extension
retrieval_tags: [clear, timing, elbow_extension]
```

## Candidate rules for calibration

| **Finding** | **Candidate evidence** | **Important limitation** |
| --- | --- | --- |
| Low contact reach | Hand height and arm extension below calibrated ranges. | May reflect jump timing or camera pitch. |
| Late elbow extension | Extension-rate peak occurs after contact proxy. | Depends strongly on contact estimate. |
| Insufficient trunk rotation | Low shoulder-hip separation change during loading. | Viewpoint and individual style sensitive. |
| Limited lower-body loading | Knee flexion or vertical drive below calibrated range. | Feet may be cropped or obstructed. |
| Abbreviated follow-through | Short post-contact hand path or abrupt stop. | Clip may end early. |
| Unstable balance | Large torso or pelvis displacement after contact. | Camera motion must be excluded. |

## Rule governance

- Store rule configuration in reviewed YAML or database records, but execute only whitelisted operators.

- Log rule version, thresholds, input values, confidence, and decision.

- Optimize first for precision. A missed tip is safer than confident incorrect coaching.

- Limit the result to the highest-value two or three findings using severity, confidence, and redundancy suppression.

- Never let the language model add, remove, or reverse rule outcomes.

# 10 Reference movement strategy

Approach A for the MVP is technique-fault detection: compare measurements with expert-calibrated acceptable ranges and timing relationships. This is easier to explain and validate than whole-sequence similarity. Professional video still helps experts establish examples and reference distributions, but an individual clip does not need to be matched to a single professional.

Approach B remains a later improvement: movement-similarity analysis using normalized pose sequences and dynamic time warping. It may help visualize timing differences, but it should not produce coaching faults until the link between similarity and expert judgment is validated. Multiple references by viewpoint, handedness, sex, style, and skill level are needed to avoid presenting one athlete’s form as universally correct.

## Professional-video sourcing remains unresolved

| **Option** | **Advantages** | **Risks or work required** |
| --- | --- | --- |
| Directly record coaches or elite players | Clear consent, controlled view, repeatable protocol. | Recruitment, compensation, release forms, smaller initial diversity. |
| License instructional footage | Higher production quality and coaching context. | Negotiation, reuse limits, possible camera mismatch. |
| Use open-license footage | Low acquisition cost. | Scarcity, uncertain suitability, attribution and license verification. |
| Use broadcast or social footage | Large and diverse pool. | Copyright, terms, unstable access, cuts and poor biomechanics view; do not use without permission. |

Decision gate: before incorporating any professional video, record provenance, license terms, permitted derivative processing, retention, redistribution rights, participant consent, and whether extracted landmarks are treated as derivatives. Legal review is required for anything other than directly commissioned or clearly licensed material.

# 11 Coaching knowledge and RAG

## 11.1 Corpus policy

The corpus contains curated coaching manuals, federation resources, peer-reviewed biomechanics papers, and licensed expert-authored material. Each source must have a rights record and an editorial status. General web search is not part of the runtime coaching path.

| **Metadata field** | **Purpose** |
| --- | --- |
| source_id and version | Stable provenance and re-indexing. |
| title, author, publisher, date | Human-readable citation. |
| license and allowed_use | Rights enforcement. |
| stroke and phase tags | Constrain retrieval. |
| fault and body-region tags | Match structured findings. |
| audience and skill level | Avoid inappropriate advice. |
| reviewer and review date | Coaching approval. |
| page or section locator | Precise citation. |
| content hash | Detect source changes. |

## 11.2 Ingestion

1. Acquire and rights-review the document.

1. Extract text with page or section locators; preserve headings and lists.

1. Remove navigation noise and duplicate passages.

1. Chunk semantically at headings, typically 250–500 tokens with modest overlap.

1. Apply controlled tags and coaching review status.

1. Embed approved chunks and store vectors with the embedding model ID and content hash.

1. Run retrieval regression tests before promoting the index version.

## 11.3 Retrieval

Construct the query from structured findings, phase, stroke, severity, and the user’s observable evidence. Apply hard metadata filters for the selected stroke (clear, smash, or drop) and approved status. Combine vector similarity with keyword or BM25 ranking, then optionally rerank the top candidates. Return three to six nonredundant chunks. Retrieval must expose source IDs and locators to the generator and final UI.

## 11.4 Generation contract

- Input only the supported findings, evidence summaries, capture limitations, and retrieved chunks.

- Generate JSON conforming to a strict schema: summary, prioritized tips, drill suggestions, cautions, and citations.

- Require each coaching recommendation to cite source chunk IDs. Reject unsupported citations.

- Use neutral language such as “the clip suggests” and surface uncertainty.

- When retrieval is weak, return a deterministic finding explanation and ask for a better clip rather than improvising.

# 12 AI model and provider strategy

## Recommendation as of 16 October 2026

Use OpenAI text-embedding-3-small for the first index and GPT-6 Luna for coaching-language generation through a thin provider adapter. The current published standard short-context prices are $0.02 per million embedding tokens, and $0.05 input / $0.25 output per million tokens for GPT-6 Luna. This is inexpensive enough that video processing and engineering time, not language generation, will dominate prototype cost. Pin a tested model snapshot or deployment where available, log the model ID, and re-run the evaluation suite before changing it.

## Why this split works

- The task is constrained synthesis, not open-ended expert reasoning; a small model should be sufficient when findings and evidence are explicit.

- Embedding cost is negligible for a small curated corpus. pgvector avoids a separate managed vector service.

- The provider adapter preserves the option to use a larger hosted model only for low-confidence or evaluation cases.

- Raw video stays local to the analysis worker. Only compact de-identified findings and approved excerpts leave the environment.

## Provider alternatives and tradeoffs

| **Option** | **Best fit** | **Cost and quality** | **Privacy and operations** |
| --- | --- | --- | --- |
| OpenAI hosted default | Fastest path to reliable structured generation. | Very low small-model cost; validate coaching quality with evals. | API data is not used for training by default; standard retention may apply; eligible customers can explore ZDR. |
| Google Gemini API | Teams already on Google Cloud or needing multimodal experiments later. | Competitive free/paid tiers; pricing and model lineup change frequently. | Paid-service terms state data is not used for product improvement; verify region and project settings. |
| Anthropic Claude | A second hosted generator for quality comparison. | Historically higher small-model token prices than the recommended default; measure, do not assume. | Review current retention and enterprise controls before sending findings. |
| Local Ollama-compatible model | Offline demos or strict data locality. | No per-token fee, but hardware, latency, setup and weaker structured-output reliability can cost more. | Findings and corpus remain local; model license and artifact security still matter. |

## Cost model

Track cost per completed analysis as embedding amortization plus generation tokens. For example, 4,000 input tokens and 700 output tokens on GPT-6 Luna at the cited rates cost about $0.000375 per analysis, excluding infrastructure and any future reranking model. Treat this as an illustrative calculation, not a budget guarantee; prices and model names change.

## Privacy hierarchy

1. Best: send no user-derived data to an LLM; use template-based guidance from retrieved text.

1. Balanced default: send structured findings without video, images, names, file metadata, or exact timestamps.

1. Avoid for MVP: send raw frames or video to a multimodal hosted model. This expands privacy, consent, cost, and evaluation scope.

# 13 API design

Use /api/v1, JSON, UTC ISO 8601 timestamps, UUIDv7 identifiers, and a capability secret returned once at creation. Hash the secret in the database. Require it for all read and delete operations. Use Idempotency-Key for creation and deletion.

| **Method and path** | **Purpose** | **Key responses** |
| --- | --- | --- |
| POST /analyses | Create upload and job; direct upload locally or signed object URL in cloud. | 201 created or 202 accepted; validation error. |
| POST /analyses/{id}/complete-upload | Finalize signed upload and enqueue. | 202 queued; 409 already finalized. |
| GET /analyses/{id} | Status, stage, progress, expiry, errors. | 200; 404 for invalid ID or token. |
| GET /analyses/{id}/result | Final result document. | 200 completed; 409 not ready; 410 expired. |
| DELETE /analyses/{id} | Cancel and delete artifacts. | 202 deletion scheduled; idempotent. |
| POST /corpus/reindex | Administrative local command or protected endpoint. | 202 index build ID. |

## Create request

```json
{
  "filename": "clear.mp4",
  "content_type": "video/mp4",
  "size_bytes": 18420342,
  "stroke": "clear",
  "handedness": "right",
  "view_hint": "rear_three_quarter",
  "consent_to_process": true
}
```

## Result response excerpt

```json
{
  "analysis_id": "019...",
  "status": "completed",
  "pipeline_version": "2026.10.0",
  "quality": {"overall": 0.84, "warnings": []},
  "stroke": {"type": "clear", "contact_time_ms": 6240, "confidence": 0.78},
  "findings": [{
    "rule_id": "clear.late_elbow_extension.v1",
    "label": "Late elbow extension",
    "severity": "moderate",
    "confidence": 0.81,
    "evidence": [{"feature": "extension_peak_offset_ms", "value": 92, "unit": "ms"}]
  }],
  "feedback": {"summary": "...", "tips": [], "citations": []},
  "expires_at": "2026-10-17T20:00:00Z"
}
```

## Error format

```json
{"error":{"code":"POSE_BODY_CROPPED","message":"The full body was not visible.","retryable":false,"details":{"missing_regions":["ankles"]}}}
```

# 14 Data model and schemas

| **Entity** | **Selected fields** | **Retention** |
| --- | --- | --- |
| analysis | id, token_hash, status, stage, progress, stroke, handedness, view, versions, timestamps, expiry | Metadata to expiry plus short operational grace. |
| media_object | analysis_id, role, object_key, sha256, bytes, codec, dimensions, fps | Raw shortest; normalized through result expiry. |
| pose_artifact | analysis_id, frame map, landmark URI, estimator, smoothing version | Delete with analysis; optionally keep de-identified eval samples by separate consent. |
| feature_set | analysis_id, schema version, values, confidences | Delete with analysis unless explicitly enrolled in evaluation. |
| finding | analysis_id, rule ID/version, outcome, severity, confidence, evidence JSON | Delete with analysis. |
| source | provenance, rights, review state, hash, bibliographic fields | Long-lived controlled corpus. |
| chunk | source version, locator, text, tags, embedding, model ID | Long-lived; rebuildable. |
| generation | analysis_id, provider, model, prompt version, usage, validated output | Delete with analysis; aggregate usage may remain. |
| audit_event | event, correlation ID, timestamp, non-sensitive details | Operational policy; never include raw frames or tokens. |

## Artifact formats

Store dense frame data as compressed Parquet or NPZ, not database rows. Store human-inspectable derived summaries as JSON. Every artifact includes analysis ID, schema version, pipeline version, source object hash, created time, and producing stage. Database rows point to immutable objects; a completed result references a consistent manifest.

## Database constraints

- Status and stage values are enums; terminal states cannot transition back to active.

- One active artifact per analysis, role, and pipeline version.

- Foreign keys cascade for metadata; object deletion is handled by a deletion outbox.

- Embedding dimensions and model ID are validated per index version.

- No plaintext capability token, API secret, or signed object URL is persisted.

# 15 Frontend design

The interface has four states: capture guidance, upload, processing, and result. Keep language direct and avoid presenting uncertain measurements as a verdict.

| **Screen** | **Essential content** |
| --- | --- |
| Capture and upload | Diagram or short instructions, accepted limits, consent statement, file picker, selected stroke and handedness. |
| Processing | Named current stage, honest indeterminate progress where needed, cancel/delete action, explanation that the browser may be closed. |
| Inconclusive | Specific quality failures, a retake checklist, and no fabricated technique feedback. |
| Result | Overall quality, annotated timeline, up to three findings, evidence in plain language, prioritized practice cue, citations and limitations. |
| Deletion | Confirmation and deletion status; explain expiry. |

Do not show raw joint-angle tables by default. Provide a developer/debug panel behind a local feature flag. If an annotated preview is implemented, show phase markers and selected joints but avoid drawing an apparently precise shuttle-contact point.

# 16 Local development and hosting

Use Docker Compose as the reference environment: web, API, worker, Redis, PostgreSQL with pgvector, and MinIO. A seeded corpus and two consented sample videos support smoke tests. Keep model weights in a documented cache or image layer, not in Git.

| **Concern** | **Local choice** | **Reason** |
| --- | --- | --- |
| Web | React, TypeScript, Vite | Fast iteration and typed API client. |
| API and worker | Python 3.12, FastAPI, Pydantic | Pose and scientific ecosystem; typed validation. |
| Video | Bundled FFmpeg/ffprobe | Reliable inspection and normalization. |
| Pose | MediaPipe Tasks | CPU-friendly prototype and tracking. |
| Numerics | NumPy, SciPy, pandas or Polars | Signal processing and feature calculation. |
| Queue | Redis plus Dramatiq | Simple durable jobs and retries; Celery acceptable if team experience favors it. |
| Database | PostgreSQL plus pgvector | One durable store for metadata and retrieval. |
| Objects | MinIO | Cloud-like object API locally. |
| RAG | Custom thin pipeline | Transparent filters, citation checks and provider interchangeability. |

Developer commands should cover environment startup, database migration, corpus ingest, sample analysis, unit tests, integration tests, and evaluation. Secrets belong in a local untracked environment file. Provide deterministic configuration profiles for CPU smoke tests and full analysis.

# 17 Cloud deployment

Move to cloud only after the local evaluation gates pass. Preserve the same container boundaries and object-store API. A pragmatic first cloud target is one managed web/API service plus a separately autoscaled worker service, managed PostgreSQL, managed Redis or queue, and private object storage.

| **Local** | **Cloud equivalent** | **Migration note** |
| --- | --- | --- |
| React dev server | Static hosting plus CDN | Same build artifact; strict CSP and HTTPS. |
| FastAPI container | Managed container service | Stateless; scale by request rate. |
| Worker container | CPU or GPU worker pool | Scale by queue depth; separate resource class. |
| Redis queue | Managed Redis or cloud queue | If changing queue semantics, add visibility-timeout and DLQ tests. |
| PostgreSQL plus pgvector | Managed PostgreSQL plus pgvector | Backups, point-in-time recovery and private networking. |
| MinIO | Encrypted object storage | Signed uploads, lifecycle deletion, block public access. |
| Local model cache | Container registry or artifact registry | Pin hashes and scan images. |

## Network design

Expose only the CDN and API ingress. Keep database, queue, object-store service endpoint, and workers on private networking. Workers use workload identity or scoped service credentials. Apply storage lifecycle rules as a backstop to application deletion. Use separate development, staging, and production projects or accounts.

## Capacity and scaling

Scale API instances on request concurrency and worker instances on queue age and depth. Cap concurrent pose jobs per worker based on measured memory. Generation calls are lightweight and should not determine worker sizing. Define admission limits so an upload spike cannot exhaust disk or create an unbounded queue.

# 18 Observability and operations

| **Signal** | **Examples** | **Alert or use** |
| --- | --- | --- |
| Reliability | Completion, failure and retry rates by stage/error code. | Alert on sustained completion drop. |
| Latency | Queue wait and stage duration p50/p95/p99. | Capacity planning and regression detection. |
| Quality | Gate failures, pose confidence, inconclusive rate, finding distribution. | Detect camera-guide or model drift. |
| RAG | Retrieval hit rate, citation validation failures, fallback rate. | Protect groundedness. |
| Cost | Tokens and hosted-model cost per completed analysis. | Budget and model-change review. |
| Deletion | Objects pending deletion and oldest age. | Privacy operations. |
| Versioning | Pipeline, rule, corpus, embedding and generator versions. | Reproducibility and rollback. |

Use one correlation ID from API through worker and provider calls. Structured logs must exclude video URLs, capability tokens, prompt bodies, retrieved copyrighted passages beyond controlled debug settings, and landmark arrays. Dashboards should segment by pipeline version and test-versus-user traffic.

# 19 Security privacy and safety

## Threat model

| **Threat** | **Control** |
| --- | --- |
| Malicious or malformed media | Decode in an isolated, resource-limited process; validate after decode; patch FFmpeg; limit duration, bytes, resolution and frames. |
| Unauthorized result access | High-entropy capability token, hashed at rest, TLS, uniform not-found responses, rate limits. |
| Object exposure | Private buckets, short-lived signed URLs, least-privilege identities, no public ACLs. |
| Prompt injection in corpus | Only approved sources; treat text as data; fixed system policy; structured output; citation allow-list. |
| Hallucinated coaching | Rules own findings; generator cannot introduce facts; validate every citation; deterministic fallback. |
| Sensitive biometric-like data | Data minimization, short retention, explicit consent, deletion, no identity recognition or cross-session linking. |
| Dependency or model compromise | Lock files, image scanning, artifact hashes, model provenance, controlled updates. |
| Abuse and denial of service | Upload quotas, per-IP rate limits, queue caps, decompression limits, timeouts and cancellation. |

## Privacy defaults

- Default raw-video retention: 24 hours after completion; configurable shorter. Results expire at the same time unless the user downloads them.

- Do not identify faces or infer sensitive attributes. Consider face blurring for retained evaluation clips.

- Evaluation reuse requires separate explicit consent and a separate dataset governance path.

- Send only compact findings and approved source excerpts to a hosted language provider.

- Publish a plain-language notice describing processing, provider use, retention and deletion.

## Safety language

Feedback should be framed as technique guidance, not medical advice. Do not diagnose injury or recommend training through pain. When the user reports pain, the product should advise stopping and consulting a qualified coach or healthcare professional. Avoid guarantees such as “this will prevent injury.”

# 20 Evaluation and acceptance criteria

Build an evaluation dataset under consent with varied skill levels, body shapes, handedness, clothing, lighting, backgrounds, viewpoints and devices. Qualified badminton coaches label stroke boundaries, phase points, supported faults, severity, and whether each rule is observable from the view. Use at least two independent raters for a meaningful subset and adjudicate disagreements.

| **Layer** | **Metric** | **Initial exit target** |
| --- | --- | --- |
| Media and quality | Valid acceptance; invalid rejection; actionable error accuracy. | >= 95% on controlled test matrix. |
| Pose | Required landmark availability; normalized trajectory error on annotated subset. | Report by landmark/view; thresholds set after baseline. |
| Phases | Median absolute timing error and within-tolerance rate. | Contact proxy <= 100 ms median; >= 85% within 150 ms on qualified clips. |
| Rules | Precision, recall, F1 and calibration per fault. | Precision >= 0.80; no rule ships on aggregate score alone. |
| Retrieval | Recall@k and coach relevance. | Recall@5 >= 0.90 for a curated query set. |
| Generation | Citation correctness, faithfulness, usefulness, unsafe-advice rate. | 100% valid citations; >= 95% finding faithfulness; zero critical unsafe outputs in test set. |
| System | Completion and p95 latency. | >= 95% completion; p95 <= 90 s on reference hardware for qualified clips. |
| User | Retake success and feedback comprehension. | Measure in moderated tests; define target after baseline. |

Metrics must include confidence intervals and slices. A global average can hide failure for left-handed players or a camera view. The first go/no-go criterion is safe precision and honest abstention, not broad fault coverage.

# 21 Testing strategy

- Unit tests: coordinate transforms, angles, filters, phase utilities, rule operators, schema validation, citation checker, cost calculation.

- Golden tests: frozen landmark sequences with expected phases, features, findings, and result JSON.

- Property tests: translation/scale invariance, left-right mirroring, monotonic timestamp handling, missing-landmark behavior.

- Integration tests: upload through completion using a tiny consented clip; process restart and retry; deletion outbox; provider timeout and fallback.

- Contract tests: OpenAPI client, provider adapters, object store, and corpus index version.

- Security tests: malformed containers, oversized claims, path traversal names, capability-token guessing, signed URL expiry, prompt-injection corpus sample.

- Evaluation tests: fixed expert-labeled set run on every rule, model, pose, or corpus change. Fail promotion when protected metrics regress beyond tolerance.

- UI tests: keyboard-only flow, screen-reader labels, upload errors, refresh during processing, inconclusive state, and deletion.

Use real video only in a controlled fixture store with documented consent and license. Keep CI fixtures tiny; run the full evaluation suite in a gated environment with access logging.

# 22 Delivery roadmap

| **Phase** | **Deliverable** | **Exit condition** |
| --- | --- | --- |
| 0 Foundations | Repository, Compose stack, schemas, sample data policy, CI, threat model. | One command starts services; sample job lifecycle works. |
| 1 Intake | Upload, validation, normalization, status UI, deletion. | Media test matrix passes; restart-safe jobs. |
| 2 Pose and phases | Pose artifacts, quality gates, phase visualization. | Phase baseline measured on labeled clears. |
| 3 Rules | Feature registry and first 2–3 calibrated clear rules. | Precision gate met for each enabled rule. |
| 4 RAG | Curated corpus, hybrid retrieval, structured generation, citations and fallback. | Retrieval and faithfulness gates pass. |
| 5 Pilot | Polished result UI, observability, privacy notice, limited testers. | End-to-end targets and deletion audit pass. |
| 6 Cloud | Staging deployment and load/security tests. | Operational runbook and rollback tested. |
| Later | Smash support, similarity visualization, more views or multi-camera. | Separate labeled data and acceptance criteria per expansion. |

## Suggested team sequence

One developer can prototype the pipeline, but rule calibration requires a qualified badminton coach, and video rights require a responsible owner. Security and privacy review should occur before external testing, not after cloud deployment.

# 23 Risks and mitigations

| **Risk** | **Impact** | **Mitigation** |
| --- | --- | --- |
| 2D depth ambiguity | Incorrect conclusions about rotation or contact. | Restrict viewpoints and features; abstain; later evaluate multi-view or 3D. |
| Fast motion and occlusion | Missing wrist/elbow landmarks. | Capture guide, confidence propagation, temporal tracking, better pose models later. |
| Contact is only a proxy | Timing rules may be wrong. | State limitation; calibrate against manually labeled frames; add racket/shuttle model later. |
| Expert disagreement | Unstable ground truth. | Multiple raters, observability labels, adjudication and documented definitions. |
| One reference becomes a universal ideal | Biased or misleading coaching. | Use ranges and diverse references; avoid imitation score. |
| RAG sounds authoritative | Users over-trust fluent output. | Citations, uncertainty, bounded claims, no new findings from LLM. |
| Video rights unclear | Legal or deployment blocker. | Rights register and decision gate; commission controlled footage. |
| Model/provider drift | Regression or cost surprise. | Pinned versions, adapters, regression suite, budgets and change review. |
| No login but sensitive URL | Link leakage exposes result. | Capability secret, short expiry, no indexing, referrer policy, easy delete. |

# 24 Open decisions

| **Decision** | **Needed by** | **Decision evidence** |
| --- | --- | --- |
| Professional reference video source and license model | Before reference-derived thresholds or similarity work. | Rights, camera protocol, diversity, cost, consent. |
| Exact supported camera view band | Before phase/rule calibration. | Error sliced by view on labeled clips. |
| Initial enabled fault rules and thresholds | Before pilot. | Coach definitions plus precision and calibration results. |
| Default retention period | Before external users. | Privacy policy, user need and operating cost. |
| Hosted AI provider approval and region | Before external users if hosted generation is enabled. | Privacy/legal review, residency, retention and evaluation. |
| Whether to render annotated video | Before result UI freeze. | User-study benefit versus processing and privacy cost. |
| Per-stroke rule depth for smash and drop | After shared stroke contract is stable. | Clear, smash, and drop are selectable at upload; deepen stroke-specific rules and evals as labeled data allows. |

# 25 Appendices

## 25.1 Suggested repository layout

```text
apps/web                 React client
services/api             FastAPI routes and orchestration
services/worker          background stage runners
packages/contracts       shared schemas and generated clients
packages/video           ffprobe and FFmpeg normalization
packages/pose            estimator interface and MediaPipe adapter
packages/biomechanics    phases, features and confidence
packages/rules           rule engine and reviewed configurations
packages/rag             ingestion, retrieval, provider adapters
corpus/manifests         source metadata, not copyrighted source files
evals                    labels, metrics and regression harness
infra/local              Compose and local configuration
infra/cloud              infrastructure as code
docs                     decisions, runbooks and data governance
```

## 25.2 Core internal interfaces

```text
PoseEstimator.infer(video) -> PoseSequence
QualityAssessor.evaluate(video, pose) -> QualityReport
StrokeSegmenter.segment(pose) -> StrokeWindow[]
PhaseDetector.detect(window) -> PhaseSet
FeatureExtractor.compute(window, phases) -> FeatureSet
RuleEngine.evaluate(features, context) -> Finding[]
Retriever.search(findings, filters) -> EvidenceChunk[]
FeedbackGenerator.generate(findings, evidence) -> Feedback
ResultAssembler.build(...) -> AnalysisResult
```

## 25.3 Definition of done for an enabled rule

- A coach-reviewed definition and observable limitation exist.

- Required features and supported views are explicit.

- Thresholds are calibrated on training data and frozen before test evaluation.

- Per-slice precision, recall and confidence calibration are reported.

- Low-confidence and missing-data paths abstain.

- A relevant, rights-approved corpus passage is retrievable.

- UI wording and source citations pass coach review.

- Pipeline, rule, corpus and model versions reproduce the result.

## 25.4 Source and vendor references

| **Reference** | **Location** |
| --- | --- |
| Project context | Local project reference, Badminton Movement Assistant Project Context. |
| OpenAI API pricing | https://developers.openai.com/api/docs/pricing (accessed 16 October 2026). |
| OpenAI text embedding 3 small | https://developers.openai.com/api/docs/models/text-embedding-3-small (accessed 16 October 2026). |
| OpenAI business data privacy | https://openai.com/business-data/ (accessed 16 October 2026). |
| Google Gemini API pricing | https://ai.google.dev/gemini-api/docs/pricing (accessed 16 October 2026). |
| Google Gemini embeddings | https://ai.google.dev/gemini-api/docs/embeddings (accessed 16 October 2026). |
| Anthropic pricing | https://docs.anthropic.com/en/docs/about-claude/pricing (accessed 16 October 2026). |

Vendor features, names, prices, retention, and regional controls change. Reconfirm them during implementation and record the verified date in an architecture decision record.

## 25.5 Glossary

| **Term** | **Meaning** |
| --- | --- |
| Capability token | A high-entropy secret that grants access to one analysis without an account. |
| Contact proxy | A body-kinematic estimate of likely shuttle contact time; not direct contact observation. |
| DTW | Dynamic time warping, an algorithm for aligning sequences with different timing. |
| Finding | A versioned, rule-produced technique observation with evidence and confidence. |
| Grounded feedback | Language limited to supplied findings and retrieved approved passages. |
| Inconclusive | A safe terminal result when quality or certainty is insufficient. |
| RAG | Retrieval-augmented generation: retrieve relevant source passages, then generate from them. |
| Rule precision | Among clips where a rule fires, the proportion that experts label as having that fault. |
