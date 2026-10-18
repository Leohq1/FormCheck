# Person 3 Analysis Pipeline Working Design

Status: Draft for approval and cross-group review  
Owner: Person 3  
Scope: Video processing, pose estimation, biomechanics, deterministic rules, and analysis-stage integration

## 1. Intent

Build a conservative Python 3.12 pipeline that converts one privately stored overhead-clear video into structured `AnalysisFindings`. The pipeline measures observable body motion, abstains when evidence is unreliable, and keeps uncalibrated rule behavior out of production findings.

The first useful demonstration is one command or analysis-stage invocation that can process a consented sample when local assets are present. Before coach calibration, it may return measured features and development-only candidate-rule diagnostics, but its production-consumable `findings` array remains empty.

Person 4 must be able to generate coaching from approved findings without receiving the video, frames, pose trajectories, or candidate-rule diagnostics.

## 2. Goals

- Inspect and normalize eligible MP4 or MOV source video with FFmpeg/ffprobe.
- Preserve a normalized-frame-to-source-timestamp map.
- Wrap MediaPipe Pose Landmarker behind a `PoseEstimator` interface.
- Represent pose output in a canonical, versioned `PoseSequence` with explicit missing data.
- Reject or mark inconclusive videos whose observations cannot support analysis.
- Locate one overhead-clear window and estimate preparation, loading, acceleration, contact proxy, and follow-through.
- Normalize coordinates for translation, body scale, handedness, and phase-relative timing.
- Initially compute `dominant_elbow_angle_at_max_wrist_height_deg` without depending on precise contact timing.
- Evaluate `clear.low_arm_extension.v1` as a disabled, uncalibrated candidate.
- Produce an internal `schema_version: "0-draft"` findings document until the shared schema is approved.
- Provide deterministic unit, property, integration, and evaluation tests with explicit asset-dependent skips.

## 3. Non-goals and anti-goals

This work does not implement frontend presentation, coaching prose, RAG, API routes, queue infrastructure, object-store credentials, retention, deletion, or worker retry policy. It does not track a racket or shuttle, infer metric depth from MediaPipe relative z, diagnose injury, compare the player with a professional, analyze a smash, or support multiple players/strokes.

The pipeline must not:

- invent measurements through long occlusions;
- present the estimated contact proxy as observed racket-shuttle contact;
- turn a disabled candidate evaluation into a finding;
- let development diagnostics reach Person 4 or the user-facing result;
- enable a badminton rule based on a plausible-looking threshold;
- commit participant video, extracted pose artifacts, or model binaries;
- claim shared-schema compliance before cross-group approval.

## 4. Authorized paths

Person 3 implementation changes are limited to:

```text
packages/video/
packages/pose/
packages/biomechanics/
packages/rules/
services/worker/analysis/
evals/pose/
evals/rules/
```

Explicitly authorized shared/setup exceptions are:

```text
pyproject.toml
uv.lock
.python-version
.gitignore
.local/README.md
```

Person 3 may draft `packages/contracts/analysis-findings.schema.json`, but it is not authoritative until reviewed by at least one Group A and one Group B member. No other shared contract or cross-module test is changed without separate approval.

## 5. Proposed module boundaries

```text
packages/video/
  inspection, eligibility, normalization, timestamp mapping, FFmpeg adapter

packages/pose/
  pose domain models, PoseEstimator protocol, MediaPipe adapter, landmark mapping

packages/biomechanics/
  quality assessment, coordinate normalization, stroke segmentation,
  phase estimation, confidence propagation, feature registry

packages/rules/
  rule models, rule registry, deterministic evaluation, production projection

services/worker/analysis/
  pipeline composition, storage-port protocol, progress/cancellation ports,
  command-line development entry point

evals/pose/
  pose/phase evaluation code and reports; no participant media

evals/rules/
  coach-label formats, rule metrics, calibration reports; no participant media
```

Dependencies point inward toward domain models and protocols. Package code must not import API routes, queue clients, database models, object-store SDKs, or RAG code.

## 6. Python environment

The root project uses uv with one committed `uv.lock` and `.python-version` set to `3.12`.

`pyproject.toml` defines:

- `requires-python = ">=3.12,<3.13"`;
- base dependencies: NumPy and Pydantic;
- analysis group: MediaPipe, `opencv-python-headless`, and SciPy;
- test group: pytest and Hypothesis;
- development group including analysis and test;
- centralized pytest, formatting, linting, and type-checking settings.

Direct and transitive versions are accepted only after a real Python 3.12 import/test smoke check. The lockfile is never edited manually. Developers use `uv sync --locked` and `uv run --locked pytest`; controlled upgrades use `uv lock --upgrade-package <package>`.

The first setup change will select and record a uv version. CI integration is outside Person 3 ownership, but the documented CI commands are:

```powershell
uv lock --check
uv sync --locked
uv run --locked pytest
```

## 7. Local assets

Local-only assets use:

```text
.local/samples/overhead_clear.mp4
.local/models/pose_landmarker_full.task
```

and environment variables:

```text
FORMCHECK_SAMPLE_VIDEO
MEDIAPIPE_POSE_MODEL_PATH
```

`.gitignore` ignores `.local/*` and re-includes `.local/README.md`. The README explains placement, consent/licensing restrictions, expected model provenance fields, and example environment configuration.

Synthetic tests always run. A sample-video test skips unless `FORMCHECK_SAMPLE_VIDEO` resolves to a file. A MediaPipe integration test skips unless `MEDIAPIPE_POSE_MODEL_PATH` resolves to a file. End-to-end tests require both. Every skip names the missing variable or invalid path.

## 8. Video inspection and normalization

### 8.1 Input and eligibility

The video package receives a local source path materialized through the worker storage port. ffprobe output is parsed into typed metadata containing source hash, duration, byte size, codec, width, height, nominal and average frame rate, rotation, stream count, and decode-validity status.

Analysis-level eligibility enforces the agreed limits: MP4/MOV, at most 100 MB and 30 seconds, supported decodable video, 30--120 fps, and recommended minimum 720p. Container extension and MIME type are never trusted as decode evidence. Stable error/remediation codes distinguish invalid media from an otherwise operational but analytically inconclusive clip.

For the MVP, a source below 720p remains eligible when it otherwise decodes and passes analysis quality gates, but inspection emits a low-resolution warning. MP4 and MOV are the only accepted source containers. Source video codecs are not independently allow-listed: successful resource-limited decoding is authoritative, the observed codec is recorded, and normalization always emits the fixed H.264/AVC output contract. Frame rates outside 30--120 fps are ineligible rather than merely warned.

### 8.2 FFmpeg adapter

FFmpeg and ffprobe are invoked directly with argument arrays, never shell strings. The adapter captures stdout/stderr, applies a configurable timeout, checks the exit status, redacts sensitive paths from safe errors, and exposes the constructed invocation for tests.

Normalization produces:

- MP4 with H.264/AVC and `yuv420p`;
- 60 fps when inspected source rate is at least 50 fps, otherwise 30 fps;
- rotation applied to pixels and rotation metadata removed;
- audio and non-video streams removed;
- long edge at most 1920 pixels, aspect ratio preserved, even dimensions;
- presentation timestamps rebased to zero and monotonic.

### 8.3 Timestamp map

The map contains the normalization-contract version and one entry per output frame:

```json
{
  "frame_index": 0,
  "normalized_timestamp_ms": 0,
  "source_timestamp_ms": 12
}
```

Mapping uses decoded source presentation timestamps rather than assuming that frame index divided by nominal fps accurately describes the source. Each constant-rate output timestamp maps to the nearest decoded source presentation timestamp; ties select the earlier source timestamp. Duplicate mappings are valid when FFmpeg duplicates a source frame, and gaps are valid when source frames are dropped. The map does not claim interpolated frames or exact pixel provenance. Source presentation timestamps are collected before normalization, and tests cover variable-rate input, duplicates, drops, and the deterministic tie rule. The normalization result records logical object keys, hashes, output metadata, FFmpeg version, and contract version.

## 9. Pose estimation

`PoseEstimator` is a protocol with an inference operation over a normalized local video path and returns a `PoseSequence`. The MVP has one implementation: `MediaPipePoseEstimator` using video mode and monotonically increasing millisecond timestamps.

`PoseSequence` records:

- schema/model version and estimator name/version;
- normalized video metadata and frame-time mapping reference;
- frame index and timestamp for every processed frame;
- each canonical landmark name;
- normalized image x/y;
- relative z when reported, explicitly labeled non-metric;
- visibility and presence/confidence;
- explicit `available`/missing state and missing reason.

All expected canonical landmarks remain represented even when unavailable. Raw estimator output is preserved in memory through canonical conversion; any smoothing occurs downstream and never fills a long occlusion.

The adapter validates model-path existence, converts MediaPipe failures into typed internal errors, and never downloads a model implicitly.

Dominant handedness is supplied by the Person 2 `AnalysisJob`; Person 3 does not infer it from motion. A missing or unsupported handedness value is an invalid job-contract input. The supplied value controls dominant-landmark selection and canonical mirroring and is preserved in analysis metadata.

## 10. Quality assessment and abstention

Quality is evaluated before fault production and returns an overall score, eligibility flag, component results, warnings, and remediation codes. Initial checks cover:

- torso, dominant arm, and full-body coverage;
- selected-landmark availability and confidence;
- dominant-arm occlusion duration;
- motion blur around candidate motion;
- camera motion;
- multiple-person interference where observable from estimator output;
- supported side or rear-three-quarter view;
- exactly one plausible stroke candidate;
- sufficient post-candidate frames for follow-through.

Initial numeric gates are versioned engineering defaults, not claims of validated badminton accuracy. They must be easy to replace through reviewed configuration. Required-landmark or phase failures make dependent features unavailable. Global eligibility failures stop rule production and return an inconclusive analysis outcome with actionable remediation.

Confidence is conservative: derived confidence cannot exceed the weakest required observation after accounting for temporal stability and phase uncertainty.

## 11. Coordinate and handedness normalization

Image coordinates remain available for coverage checks. Biomechanical coordinates are translated to the pelvis midpoint and scaled by a robust body reference such as torso length, with shoulder width as a documented fallback. Degenerate or unavailable scale makes dependent measurements unavailable.

Left-handed clips are mirrored into a canonical dominant-right representation by swapping left/right landmark semantics and reflecting the horizontal axis around the body origin. Joint angles use three points and are invariant to translation and uniform scale. Relative z is carried as an observation but excluded from the first feature and rule.

Property tests cover translation invariance, uniform-scale invariance, left/right mirroring, monotonic timestamps, and missing inputs.

## 12. Stroke and phase estimation

The segmenter computes robust, smoothed motion signals from the dominant wrist, elbow, shoulder, and torso. It detects contiguous motion-energy candidates and selects a single overhead-clear window only when one candidate sufficiently dominates. Zero candidates, multiple competing candidates, or insufficient surrounding context yield an inconclusive segmentation result.

Within the window, the phase detector estimates:

- preparation interval;
- loading interval;
- acceleration interval;
- estimated contact proxy interval/time;
- follow-through interval.

The contact proxy uses wrist-speed, reach, and elbow-extension evidence and is always labeled estimated. Every phase has evidence, confidence, and uncertainty. Contact-dependent features and rules are unavailable when contact uncertainty exceeds the configured versioned limit. The first feature does not require contact.

Prototype heuristics are kept behind interfaces so labeled-data calibration can replace thresholds without changing downstream models.

## 13. Feature extraction

Features use a registry containing name, version, units, required landmarks/phases, supported views, handedness policy, computation, availability reason, and confidence method.

The first feature is:

```text
dominant_elbow_angle_at_max_wrist_height_deg
```

Within the eligible stroke window, choose the reliable sample or narrow neighborhood having maximum normalized dominant-wrist height. Compute the shoulder-elbow-wrist angle in image/body-plane coordinates. If required landmarks are missing, confidence is too low, the view is unsupported, or the maximum is unstable across the neighborhood, return `available: false` with no invented numeric value.

The feature output includes name, optional value, unit `deg`, confidence, availability, unavailability reason, and feature version `1`.

## 14. Rule engine and diagnostic separation

Production rule outcomes are `not_applicable`, `pass`, `finding`, and `inconclusive`. A rule definition declares required features, supported stroke/view, confidence minimum, version, calibration status, enabled state, condition, severity bands, and retrieval tags.

`clear.low_arm_extension.v1` begins with:

- `enabled: false`;
- `calibration_status: not_calibrated`;
- no production threshold;
- required feature `dominant_elbow_angle_at_max_wrist_height_deg`;
- supported side and rear-three-quarter views.

Development/evaluation mode may apply a clearly labeled provisional diagnostic threshold to exercise rule plumbing. Its diagnostic outcome may be `would_trigger`, `would_pass`, `not_applicable`, or `inconclusive`. These are not production rule outcomes.

The result assembler uses separate types for `Finding` and `CandidateRuleEvaluation`. Only enabled, calibrated rules can construct a `Finding`. The production projection removes diagnostics entirely. Person 4 receives the complete production `AnalysisFindings` payload (quality, stroke/phases, features, findings, and versions), but its RAG fault input is derived exclusively from `findings`. Candidate diagnostics cannot be passed to the production serializer or the RAG input adapter.

The candidate remains excluded from `findings` until a coach-reviewed definition and threshold achieve at least 0.80 precision on a held-out labeled set, with supported-view and handedness slices reported. Enabling requires a reviewed configuration/version change, not a runtime flag.

## 15. `AnalysisFindings` draft output

Until shared-schema approval, the internal Pydantic model uses `schema_version: "0-draft"`. It contains:

- analysis ID;
- quality report and eligibility;
- stroke window, phase estimates, and uncertainties;
- all measured/unavailable features;
- production findings, initially empty;
- pipeline, pose, feature, and rule versions;
- optional diagnostics only in development/evaluation serialization.

Validation forbids non-finite numbers, confidence outside `[0, 1]`, evidence without units/version, and findings from disabled or uncalibrated rules.

### Integration assumption requiring cross-group review: shared schema

Person 3 may draft `packages/contracts/analysis-findings.schema.json`. Person 2 and Person 4 integrate only after Group A and Group B approval. Diagnostics should remain outside the production shared contract; if the team elects to include them, they must be optional, explicitly development-only, and ignored by Person 4.

## 16. Worker analysis composition

The analysis-stage orchestrator composes pure stages and ports:

```text
materialize source through storage port
-> inspect and validate
-> normalize and persist normalized artifacts
-> estimate pose
-> assess quality
-> segment stroke
-> detect phases
-> normalize coordinates
-> extract features
-> evaluate rules
-> assemble AnalysisFindings
```

Each expensive boundary checks cancellation. Operations are deterministic for a recorded run identity. That identity includes source hash, pipeline version, normalization-contract version, FFmpeg version, pose-estimator/model version and model hash, feature-schema version, rule-set/configuration version, and execution mode. Person 3 does not implement a cache or decide whether artifacts may be reused; Person 2 owns idempotency and storage policy. Any material algorithm or heuristic change requires an appropriate component or pipeline version change. Person 3 code reports progress through a protocol but does not persist it or choose retry policy.

### Integration assumption requiring cross-group review: Person 2 boundary

Person 2 provides source materialization, artifact writing, cancellation, and progress interfaces. Logical object keys are:

```text
analyses/{analysis_id}/source/{filename}
analyses/{analysis_id}/normalized/video.mp4
analyses/{analysis_id}/normalized/timestamps.json
```

Person 3 will define only the pipeline-facing requirements in `services/worker/analysis/ports.py`. These interfaces are explicitly provisional until Person 2 approves their signatures:

```python
class ArtifactReader(Protocol):
    def materialize(self, object_key: str) -> Path: ...


class ArtifactWriter(Protocol):
    def put_file(
        self,
        object_key: str,
        local_path: Path,
        *,
        content_type: str,
    ) -> ArtifactMetadata: ...


class CancellationPort(Protocol):
    def raise_if_cancelled(self, analysis_id: UUID) -> None: ...


class ProgressPort(Protocol):
    def report(
        self,
        analysis_id: UUID,
        stage: AnalysisStage,
        progress: float | None,
        message_key: str,
    ) -> None: ...
```

`ArtifactMetadata` contains only integration-neutral facts needed by analysis, such as logical object key, byte size, content type, and content hash. `AnalysisStage` is an internal typed representation aligned with the shared progress contract; it does not redefine persistence behavior.

Local adapters in `services/worker/analysis/testing_ports.py` use temporary directories, an in-memory progress-event list, and an explicit cancellation flag. They enable deterministic pipeline tests before Redis, MinIO, or the production worker exists.

The provisional ports follow these restrictions:

- no imports of MinIO, Redis, Dramatiq, database models, API code, or Person 2 internals;
- logical object keys only, never signed or storage-specific URLs;
- no decisions about authentication, credentials, retries, retention, or deletion;
- cancellation checks between expensive stages;
- advisory progress reports that cannot control analysis behavior;
- repeat-safe artifact writes for the same run identity, with conflict/replacement policy left to Person 2;
- stable, safe progress message keys with no raw exceptions or local paths.

The integration sequence is: Person 3 defines the provisional ports, Person 2 reviews their signatures, Person 2 supplies production adapters, and Person 3 retains local adapters for tests. Worker composition may be implemented against the provisional ports, but production adapters are outside Person 3's scope and worker integration cannot be declared complete until Person 2 approves the interfaces and adapter contract.

### Integration assumption requiring cross-group review: Person 4 handoff

Person 4 receives the approved production projection containing quality, stroke/phases, features, `findings`, and versions. Its RAG fault input is the `findings` collection; quality and phase limitations may constrain wording, while raw features are evidence already referenced by findings rather than a source of new faults. It never receives raw video/pose data or candidate diagnostics and must not create, reverse, or strengthen findings.

## 17. Errors and safe failure

Typed internal failures distinguish:

- missing local dependency/asset in development;
- malformed or unsupported media;
- technical FFmpeg/MediaPipe failure;
- analytically inconclusive quality;
- unavailable feature/phase;
- invalid internal output.

Expected poor-quality input returns inconclusive data and remediation, not a technical failure. Unexpected tool crashes remain failures for Person 2's retry policy. Safe outward messages never expose stack traces, credentials, signed URLs, or full local paths.

## 18. Testing and evaluation

### Always-running tests

- Typed-model validation and JSON round trips.
- ffprobe parsing and FFmpeg command construction.
- Timestamp-map monotonicity and mapping fixtures.
- Canonical landmark mapping and explicit missing state.
- Quality gate pass/abstain behavior.
- Geometry and joint-angle examples.
- Translation, scale, and handedness properties.
- Stroke/phase behavior on synthetic trajectories.
- Feature availability and confidence propagation.
- Disabled rules never populate findings.
- Production serialization excludes diagnostics.
- Empty findings is schema-valid.

### Asset-dependent tests

- Source-video inspection/normalization: requires `FORMCHECK_SAMPLE_VIDEO` and FFmpeg tools.
- MediaPipe inference: requires `MEDIAPIPE_POSE_MODEL_PATH` and a small generated/readable video input.
- End to end: requires both environment variables and FFmpeg tools.

Missing assets cause explicit pytest skips. Missing required executables may skip marked integration tests but produce clear setup guidance; they do not weaken unit coverage.

### Evaluation

`evals/pose/` reports landmark availability and phase/contact-proxy error when labels exist. `evals/rules/` computes per-rule precision, recall, F1, calibration, counts, and relevant slices. No participant media is committed. A golden result is created only after consent, handedness, view, and expected stroke window are reviewed and label provenance is recorded.

## 19. Implementation sessions

Each session begins by listing exact files, tests, assumptions, and unresolved points. It ends with focused verification and a handoff summary. Later sessions start only after the prior session is reviewed.

1. **Environment and skeleton:** authorized root uv configuration, ignore/setup files, Python package skeletons, import and configuration tests.
2. **Domain models:** internal `0-draft` Pydantic models, pose types, availability/confidence semantics, JSON fixtures.
3. **Video layer:** ffprobe parsing, eligibility, FFmpeg adapter, normalization plan, timestamp-map generation and tests.
4. **Pose adapter:** `PoseEstimator`, MediaPipe mapping, model-path handling, synthetic and skipped integration tests.
5. **Quality and normalization:** coverage/confidence gates, coordinate normalization, mirroring, geometry/property tests.
6. **Stroke and phases:** synthetic motion signals, candidate selection, phase/contact-proxy estimates, abstention tests.
7. **Feature vertical slice:** registry and dominant-elbow-angle feature with unavailable-data behavior.
8. **Rule vertical slice:** generic rule engine, disabled candidate diagnostics, production-projection isolation.
9. **Pipeline composition:** provisional ports and local test adapters, progress/cancellation boundaries, development command, provisional findings fixtures. Stop at a Person 2 review gate before production-adapter integration can be declared complete.
10. **Evaluation and end-to-end readiness:** owned evaluation harnesses, asset skips, setup/run documentation, full verification.

Drafting the shared schema is a separately reviewed integration task and is not silently bundled into these sessions.

## 20. Completion criteria

Before assets and calibration exist, the implementation is ready when all synthetic tests pass, asset-dependent tests skip explicitly, draft outputs validate internally, disabled rules cannot leak into findings, and another developer can install and run the suite from documentation.

With approved local assets, the controlled sample must produce a canonical pose sequence and complete development-mode analysis. With coach labels and cross-group schema approval, production completion additionally requires valid shared-schema output and at least 0.80 held-out precision before any candidate rule is enabled.

## 21. Builder decisions left intentionally open

The implementer may choose internal filenames, class/function names, NumPy array layouts, smoothing implementation details, and exact initial heuristic constants, provided they remain versioned, tested, conservative, and do not change the public or integration behavior above.

Exact production quality, segmentation, phase, feature-confidence, and rule thresholds remain hypotheses until labeled evaluation. The implementation must make that status visible rather than treating defaults as validated facts.
