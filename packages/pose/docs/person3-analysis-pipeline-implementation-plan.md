# Person 3 Analysis Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a conservative Python 3.12 analysis pipeline that converts one overhead-clear source video into internally validated `0-draft` `AnalysisFindings`, with explicit abstention and development-only diagnostics for an uncalibrated candidate rule.

**Architecture:** Person 3-owned Python packages separately implement video normalization, canonical pose estimation, biomechanics, and deterministic rules. A thin analysis worker composes them through provisional infrastructure-neutral ports, while production serialization structurally excludes candidate diagnostics.

**Tech Stack:** Python 3.12, uv, Pydantic, NumPy, SciPy, MediaPipe Tasks, OpenCV headless, FFmpeg/ffprobe subprocesses, pytest, Hypothesis, Ruff, and mypy.

**Spec:** `packages/pose/docs/person3-analysis-pipeline-design.md`

## Global Constraints

- Modify only Person 3-owned paths plus the explicitly authorized root files: `pyproject.toml`, `uv.lock`, `.python-version`, `.gitignore`, and `.local/README.md`.
- Python must satisfy `>=3.12,<3.13`; use uv and one committed root `uv.lock`; do not add `requirements.txt` or direct-pip instructions.
- Do not commit participant media, pose artifacts, model binaries, secrets, or generated analysis artifacts.
- `FORMCHECK_SAMPLE_VIDEO` and `MEDIAPIPE_POSE_MODEL_PATH` are optional; asset-dependent tests skip with the missing variable/path in the reason.
- Invoke FFmpeg/ffprobe using argument arrays without a shell; do not add a Python FFmpeg binding.
- Do not import MinIO, Redis, Dramatiq, API code, database models, or Person 2 internals.
- Relative pose z is non-metric and is not used by the first feature or rule.
- Missing or unreliable measurements remain unavailable; never interpolate across long occlusions or invent values.
- Production `findings` may contain only enabled, calibrated rules. The current milestone has none. Diagnostics are development-only and must be absent from the public result.
- `clear.low_arm_extension.v1` stays `enabled: false` and `calibration_status: not_calibrated` for this milestone. Coach-labeled calibration and the `0.80` held-out precision gate are future validation work. Do not enable the rule to make a demo produce a finding.
- Public `findings` stay `[]`. The UI says “No supported fault detected.” RAG and Gemini must not convert `would_trigger` into coaching advice. Descriptive or educational wording about a measured angle or general overhead-clear mechanics is allowed; “you have low arm extension” is not.
- Shared `analysis-findings.schema.json` drafting is not part of this plan; it requires separate cross-group review.
- Provisional worker ports require Person 2 approval before production adapters or complete worker integration may be claimed.
- Begin each task/session by restating its exact files, tests, assumptions, and unresolved points; stop after its commit and review.

## Review Focus

- Variable-frame-rate input with duplicate/dropped normalized frames must yield a monotonic map to the nearest source PTS with earlier-timestamp tie breaking; Task 3 pins this.
- A dominant-arm landmark that disappears around maximum wrist height must make the feature unavailable instead of selecting a nearby untrustworthy value; Task 7 pins this.
- Multiple comparable motion peaks must make segmentation inconclusive instead of arbitrarily selecting one stroke; Task 6 pins this.
- A disabled diagnostic that says `would_trigger` must never appear in production `findings` or production JSON; Task 8 pins this.
- Cancellation after an artifact is materialized but before the next expensive stage must stop the pipeline without a success/progress event for that stage; Task 9 pins this.

---

### Task 1: Python Environment and Importable Package Skeletons

**Files:**
- Create: `pyproject.toml`
- Create: `uv.lock`
- Create: `.python-version`
- Modify: `.gitignore`
- Create: `.local/README.md`
- Create: `packages/video/formcheck_video/__init__.py`
- Create: `packages/pose/formcheck_pose/__init__.py`
- Create: `packages/biomechanics/formcheck_biomechanics/__init__.py`
- Create: `packages/rules/formcheck_rules/__init__.py`
- Create: `services/worker/analysis/formcheck_analysis/__init__.py`
- Create: `services/worker/analysis/tests/test_imports.py`

**Interfaces:**
- Consumes: Approved dependency and asset policy from the design.
- Produces: Importable packages `formcheck_video`, `formcheck_pose`, `formcheck_biomechanics`, `formcheck_rules`, and `formcheck_analysis`; one locked development environment.

- [ ] **Step 1: Record the intended package imports in a failing smoke test**

```python
def test_person3_packages_are_importable() -> None:
    import formcheck_analysis
    import formcheck_biomechanics
    import formcheck_pose
    import formcheck_rules
    import formcheck_video

    assert all(
        package.__version__ == "0.1.0"
        for package in (
            formcheck_analysis,
            formcheck_biomechanics,
            formcheck_pose,
            formcheck_rules,
            formcheck_video,
        )
    )
```

- [ ] **Step 2: Run the smoke test before configuration exists**

Run: `uv run pytest services/worker/analysis/tests/test_imports.py -v`  
Expected: FAIL because the root project/packages are not configured.

- [ ] **Step 3: Create the root project configuration**

Define project `formcheck-analysis`, version `0.1.0`, Python `>=3.12,<3.13`, base dependencies NumPy and Pydantic, `analysis`, `test`, and composed `dev` dependency groups. Add Ruff and mypy to `dev`. Configure setuptools discovery across the five owned package roots, pytest markers `integration` and `assets`, Ruff for Python 3.12, and strict-enough mypy settings for typed package code.

Use uv to resolve a concrete Python 3.12-compatible set, then put bounded direct version ranges in `pyproject.toml`, regenerate `uv.lock`, and verify imports for NumPy, Pydantic, SciPy, OpenCV, and MediaPipe. Do not claim a combination is compatible until that smoke check passes.

- [ ] **Step 4: Add package versions and local-asset policy**

Set `__version__ = "0.1.0"` in each package. Set `.python-version` to `3.12`. Add `.local/*` and `!.local/README.md` to `.gitignore`; document the two environment variables, recommended paths, consent/licensing rules, and the fact that assets are never downloaded implicitly.

- [ ] **Step 5: Lock and verify the environment**

Run:

```powershell
uv lock --check
uv sync --locked --all-groups
uv run --locked python -c "import cv2, mediapipe, numpy, pydantic, scipy"
uv run --locked pytest services/worker/analysis/tests/test_imports.py -v
uv run --locked ruff check packages services/worker/analysis
uv run --locked mypy packages/video/formcheck_video packages/pose/formcheck_pose packages/biomechanics/formcheck_biomechanics packages/rules/formcheck_rules services/worker/analysis/formcheck_analysis
```

Expected: all commands exit `0`; pytest reports `1 passed`.

- [ ] **Step 6: Commit the environment session**

```powershell
git add pyproject.toml uv.lock .python-version .gitignore .local/README.md packages/video/formcheck_video packages/pose/formcheck_pose packages/biomechanics/formcheck_biomechanics packages/rules/formcheck_rules services/worker/analysis
git commit -m "build: initialize person 3 python workspace"
```

Include both approved planning documents under `packages/pose/docs/` in this first commit.

Review gate: cross-group review is required for the root configuration before merge.

---

### Task 2: Canonical Domain Models and Draft Findings Contract

**Files:**
- Create: `packages/pose/formcheck_pose/models.py`
- Create: `packages/biomechanics/formcheck_biomechanics/models.py`
- Create: `packages/rules/formcheck_rules/models.py`
- Create: `services/worker/analysis/formcheck_analysis/models.py`
- Create: `packages/pose/tests/test_models.py`
- Create: `packages/biomechanics/tests/test_models.py`
- Create: `packages/rules/tests/test_models.py`
- Create: `services/worker/analysis/tests/test_findings_model.py`
- Create: `services/worker/analysis/tests/fixtures/analysis_findings_no_findings.json`

**Interfaces:**
- Consumes: Package imports from Task 1.
- Produces: `PoseLandmark`, `PoseFrame`, `PoseSequence`; `QualityReport`, `StrokeWindow`, `PhaseEstimate`, `PhaseSet`, `FeatureValue`; `Evidence`, `Finding`, `CandidateRuleEvaluation`; `AnalysisFindings`, `AnalysisDiagnostics`, and `VersionInfo`.

- [ ] **Step 1: Write failing pose-model tests**

Test that `PoseFrame` requires a non-negative index and timestamp, records `detected_pose_count`, that all canonical entries can carry `available=False` with a missing reason and no coordinates, and that `PoseSequence` rejects non-monotonic timestamps.

- [ ] **Step 2: Implement canonical pose models**

Define `LandmarkName` for the MediaPipe Pose landmark set and immutable Pydantic models with finite coordinate/confidence validation. Mark z as `relative_z` and never metric.

- [ ] **Step 3: Run pose-model tests**

Run: `uv run --locked pytest packages/pose/tests/test_models.py -v`  
Expected: PASS.

- [ ] **Step 4: Write failing biomechanics/rule-model tests**

Assert confidence is constrained to `[0, 1]`, unavailable features have `value is None`, available features require value/unit/version, and a candidate diagnostic cannot validate as `Finding`.

- [ ] **Step 5: Implement biomechanics and rule models**

Use explicit enums for quality disposition, phase name, severity, production rule outcome, diagnostic outcome, and calibration status. Keep `Finding` and `CandidateRuleEvaluation` unrelated Pydantic types.

- [ ] **Step 6: Run biomechanics/rule-model tests**

Run: `uv run --locked pytest packages/biomechanics/tests/test_models.py packages/rules/tests/test_models.py -v`  
Expected: PASS.

- [ ] **Step 7: Write failing `AnalysisFindings` serialization tests**

```python
def test_production_dump_omits_diagnostics(draft_findings: AnalysisFindings) -> None:
    dumped = draft_findings.to_production_dict()
    assert dumped["schema_version"] == "0-draft"
    assert dumped["findings"] == []
    assert "diagnostics" not in dumped
```

Also assert development serialization may include diagnostics, non-finite values fail validation, and the no-findings fixture round-trips.

- [ ] **Step 8: Implement draft findings models and fixture**

Define `AnalysisFindings.to_production_dict() -> dict[str, object]` and `to_development_dict() -> dict[str, object]`. Production output includes quality, stroke/phases, features, findings, and versions but never diagnostics.

Also define `Handedness` (`left`, `right`), `ViewHint` (`side`, `rear_three_quarter`), and optional stroke/phase fields so an ineligible analysis validates without fabricated phase data.

- [ ] **Step 9: Run all model tests and static checks**

Run: `uv run --locked pytest packages/pose/tests packages/biomechanics/tests packages/rules/tests services/worker/analysis/tests/test_findings_model.py -v`  
Expected: PASS.

- [ ] **Step 10: Commit the domain-model session**

```powershell
git add packages/pose packages/biomechanics packages/rules services/worker/analysis
git commit -m "feat: define person 3 analysis domain models"
```

---

### Task 3: Video Inspection, Eligibility, Normalization, and Timestamp Mapping

**Files:**
- Create: `packages/video/formcheck_video/models.py`
- Create: `packages/video/formcheck_video/errors.py`
- Create: `packages/video/formcheck_video/process.py`
- Create: `packages/video/formcheck_video/inspection.py`
- Create: `packages/video/formcheck_video/eligibility.py`
- Create: `packages/video/formcheck_video/timestamps.py`
- Create: `packages/video/formcheck_video/frame_quality.py`
- Create: `packages/video/formcheck_video/normalization.py`
- Create: `packages/video/tests/test_inspection.py`
- Create: `packages/video/tests/test_eligibility.py`
- Create: `packages/video/tests/test_timestamps.py`
- Create: `packages/video/tests/test_frame_quality.py`
- Create: `packages/video/tests/test_normalization.py`
- Create: `packages/video/tests/test_video_assets.py`
- Modify: `packages/video/README.md`

**Interfaces:**
- Consumes: Draft model conventions from Task 2.
- Produces: `inspect_video(path: Path) -> VideoInspection`, `assess_eligibility(inspection: VideoInspection) -> VideoEligibility`, `measure_frame_quality(path: Path, config: FrameQualityConfig) -> VideoQualitySignals`, and `normalize_video(source: Path, video_output: Path, timestamp_output: Path, *, runner: ProcessRunner) -> NormalizationResult`.

- [ ] **Step 1: Write failing process/inspection tests**

Test that subprocess calls use argument lists with `shell=False`, timeouts are enforced, ffprobe JSON fractions parse exactly, rotation and PTS values are captured, malformed output raises a typed technical error, and safe errors omit source paths.

- [ ] **Step 2: Implement the subprocess and inspection adapters**

Define a `ProcessRunner` protocol and `SubprocessRunner`. Invoke ffprobe once for stream/format metadata and once for decoded video-frame presentation timestamps. Hash the source with SHA-256 using bounded reads.

- [ ] **Step 3: Run inspection tests**

Run: `uv run --locked pytest packages/video/tests/test_inspection.py -v`  
Expected: PASS.

- [ ] **Step 4: Write failing eligibility boundary tests**

Pin: only MP4/MOV containers; `100 MB` and `30 s` inclusive maxima; fps in `[30, 120]`; below 720p yields warning but remains eligible; decode failure and out-of-range fps are ineligible with stable codes.

- [ ] **Step 5: Implement eligibility assessment**

Return typed warnings/remediation without raising for expected ineligible input. Keep security/request validation outside this package.

Use stable initial codes: `VIDEO_UNSUPPORTED_CONTAINER`, `VIDEO_TOO_LARGE`, `VIDEO_TOO_LONG`, `VIDEO_FPS_UNSUPPORTED`, and `VIDEO_DECODE_FAILED`; use `VIDEO_LOW_RESOLUTION` as the non-terminal warning.

- [ ] **Step 6: Write failing timestamp-map property and edge tests**

Test monotonic output timestamps, nearest-source-PTS mapping, duplicate source mappings, dropped source PTS gaps, and earlier-PTS selection for exact ties. Use Hypothesis over sorted unique source timestamps and constant-rate output timestamps.

- [ ] **Step 7: Implement timestamp mapping**

Define `map_output_to_source(output_timestamps_ms: Sequence[int], source_pts_ms: Sequence[int]) -> tuple[TimestampMapEntry, ...]` using binary search and the exact tie rule.

- [ ] **Step 8: Write failing normalization-command tests**

Assert 60 fps for source fps `>=50`, otherwise 30 fps; H.264/AVC, `yuv420p`, no audio/non-video streams, rotation application, cleared rotation metadata, rebased timestamps, aspect-preserving scale capped at 1920, and even dimensions. Assert no shell string is constructed.

- [ ] **Step 9: Write failing sampled-frame quality tests**

Use generated NumPy frames to assert a sharp checkerboard scores sharper than its blurred version, coherent full-frame translation raises the camera-motion signal, static frames do not, and unreadable/insufficient frames produce unavailable signals rather than invented zeroes.

- [ ] **Step 10: Implement provisional frame-quality signals**

Sample frames at deterministic timestamps. Use variance of Laplacian for relative sharpness and robust global feature displacement for camera motion. Return measurements plus availability; keep provisional thresholds/config versioned for Task 5 rather than classifying user eligibility here.

- [ ] **Step 11: Implement normalization and atomic outputs**

Write to sibling temporary files, validate produced media, write timestamp JSON with contract version, then atomically replace final local outputs. Remove partial temporary files on failure without deleting pre-existing caller-owned outputs.

- [ ] **Step 12: Add the explicitly skipped sample-video integration test**

Resolve `FORMCHECK_SAMPLE_VIDEO`; call `pytest.skip("FORMCHECK_SAMPLE_VIDEO is not set or does not point to a file")` when absent. When present, assert inspection and normalization artifacts meet the fixed contract.

- [ ] **Step 13: Verify the video session**

Run: `uv run --locked pytest packages/video/tests -v -ra`  
Expected without assets: unit/property tests PASS and the sample test SKIPS with the exact reason.

- [ ] **Step 14: Commit the video session**

```powershell
git add packages/video
git commit -m "feat: add deterministic video normalization"
```

---

### Task 4: PoseEstimator Protocol and MediaPipe Adapter

**Files:**
- Create: `packages/pose/formcheck_pose/estimator.py`
- Create: `packages/pose/formcheck_pose/landmarks.py`
- Create: `packages/pose/formcheck_pose/mediapipe_estimator.py`
- Create: `packages/pose/formcheck_pose/assets.py`
- Create: `packages/pose/tests/test_landmarks.py`
- Create: `packages/pose/tests/test_mediapipe_estimator.py`
- Create: `packages/pose/tests/test_pose_assets.py`
- Modify: `packages/pose/README.md`

**Interfaces:**
- Consumes: `PoseSequence` from Task 2 and normalized video/timestamps from Task 3.
- Produces: `PoseEstimator.infer(video_path: Path, timestamps_ms: Sequence[int]) -> PoseSequence` and `MediaPipePoseEstimator(model_path: Path)`.

- [ ] **Step 1: Write failing protocol and canonical-mapping tests**

Use a fake estimator result to assert all canonical landmarks are emitted in canonical order, missing MediaPipe results become unavailable entries with reasons, visibility/presence are preserved, and timestamps remain unchanged.

- [ ] **Step 2: Implement the estimator protocol and landmark mapper**

Use `typing.Protocol`; isolate MediaPipe names and indices in `landmarks.py`. The domain models must not import MediaPipe.

- [ ] **Step 3: Write failing MediaPipe adapter tests with a fake backend**

Assert video mode, configuration for up to two poses, strictly increasing integer millisecond timestamps, explicit no-pose frames, `detected_pose_count`, deterministic primary-pose selection for canonical landmarks, estimator/model version metadata, model-path validation, and typed backend failures.

- [ ] **Step 4: Implement the MediaPipe adapter**

Inject a small backend/factory seam so unit tests do not load the model. Read frames with headless OpenCV, convert BGR to SRGB, and never download a model.

- [ ] **Step 5: Add the explicitly skipped model integration test**

Resolve `MEDIAPIPE_POSE_MODEL_PATH`; skip with `MEDIAPIPE_POSE_MODEL_PATH is not set or does not point to a file` when absent. If present, create/read a tiny synthetic video and assert inference returns one pose frame per requested timestamp without asserting a person was detected.

- [ ] **Step 6: Verify the pose session**

Run: `uv run --locked pytest packages/pose/tests -v -ra`  
Expected without model: model-free tests PASS and the model integration test SKIPS explicitly.

- [ ] **Step 7: Commit the pose-adapter session**

```powershell
git add packages/pose
git commit -m "feat: add canonical mediapipe pose adapter"
```

---

### Task 5: Coordinate Normalization and Quality Gates

**Files:**
- Create: `packages/biomechanics/formcheck_biomechanics/geometry.py`
- Create: `packages/biomechanics/formcheck_biomechanics/normalization.py`
- Create: `packages/biomechanics/formcheck_biomechanics/quality.py`
- Create: `packages/biomechanics/formcheck_biomechanics/config.py`
- Create: `packages/biomechanics/tests/test_geometry.py`
- Create: `packages/biomechanics/tests/test_normalization.py`
- Create: `packages/biomechanics/tests/test_quality.py`
- Modify: `packages/biomechanics/README.md`

**Interfaces:**
- Consumes: Canonical pose models from Task 2 and handedness supplied by `AnalysisJob` metadata.
- Produces: `joint_angle_deg(a, vertex, c) -> float | None`, `normalize_pose(sequence: PoseSequence, handedness: Handedness, config: NormalizationConfig) -> NormalizedPoseSequence`, and `assess_pose_quality(sequence: PoseSequence, context: QualityContext, config: QualityConfig) -> QualityReport`, where `QualityContext` includes the supplied view hint and Task 3 frame-quality signals.

- [ ] **Step 1: Write failing geometry example/property tests**

Assert known 90/180-degree angles, degenerate vectors return unavailable, finite-only behavior, translation invariance, and positive uniform-scale invariance using Hypothesis.

- [ ] **Step 2: Implement finite conservative geometry helpers**

Clamp cosine input only for floating-point roundoff; never coerce missing/degenerate points into numeric measurements.

- [ ] **Step 3: Write failing normalization tests**

Assert pelvis-centering, torso-length scale with shoulder-width fallback, unavailable scale behavior, right-handed identity, left-handed semantic swap/reflection, and mirror equivalence properties.

- [ ] **Step 4: Implement pose normalization**

Preserve raw availability/confidence and timestamps. Exclude relative z from first-slice geometry.

- [ ] **Step 5: Write failing quality-gate tests**

Cover adequate input, cropped full body, unreliable dominant arm, long occlusion, low resolution warning, unsupported supplied view, `detected_pose_count > 1` interference, camera-motion/blur signals supplied by context, and clip ending before follow-through. Assert global failure produces `eligible=False` with remediation and no fabricated scores. The MVP trusts `AnalysisJob.view_hint`; it does not implement automatic camera-view classification.

- [ ] **Step 6: Implement versioned quality configuration and assessment**

Keep initial engineering defaults in one immutable configuration with version `quality.v1-provisional`; document that thresholds are unvalidated. Aggregate confidence conservatively and never above the weakest required component.

- [ ] **Step 7: Verify the quality/normalization session**

Run: `uv run --locked pytest packages/biomechanics/tests/test_geometry.py packages/biomechanics/tests/test_normalization.py packages/biomechanics/tests/test_quality.py -v`  
Expected: PASS.

- [ ] **Step 8: Commit the quality session**

```powershell
git add packages/biomechanics
git commit -m "feat: add conservative pose quality and normalization"
```

---

### Task 6: Stroke Segmentation and Phase Prototypes

**Files:**
- Create: `packages/biomechanics/formcheck_biomechanics/signals.py`
- Create: `packages/biomechanics/formcheck_biomechanics/segmentation.py`
- Create: `packages/biomechanics/formcheck_biomechanics/phases.py`
- Create: `packages/biomechanics/tests/synthetic_motion.py`
- Create: `packages/biomechanics/tests/test_signals.py`
- Create: `packages/biomechanics/tests/test_segmentation.py`
- Create: `packages/biomechanics/tests/test_phases.py`

**Interfaces:**
- Consumes: `NormalizedPoseSequence`, quality eligibility, and biomechanics models from earlier tasks.
- Produces: `compute_motion_signals(sequence, config) -> MotionSignals`, `segment_overhead_clear(signals, config) -> SegmentationResult`, and `detect_phases(sequence, window, signals, config) -> PhaseDetectionResult`.

- [ ] **Step 1: Write failing signal tests on synthetic trajectories**

Assert timestamp-aware velocity (not frame-index velocity), missing samples remain gaps, smoothing does not cross configured long occlusions, and constant pose yields near-zero energy.

- [ ] **Step 2: Implement signal extraction**

Use SciPy only behind focused helpers; record smoothing/config version and reject non-monotonic timestamps.

- [ ] **Step 3: Write failing segmentation tests**

Cover one dominant overhead-like peak, no candidate, one candidate lacking context, and two comparable peaks. The comparable-peaks review-focus test must return inconclusive with `competing_candidates=2` rather than choose one.

- [ ] **Step 4: Implement conservative candidate segmentation**

Return typed confidence/evidence and preserve all candidate summaries for diagnostics; only one sufficiently dominant candidate yields a `StrokeWindow`.

- [ ] **Step 5: Write failing phase tests**

Assert ordered preparation/loading/acceleration/contact-proxy/follow-through estimates, confidence/uncertainty on every phase, insufficient follow-through abstention, and uncertain contact suppresses contact-dependent availability without invalidating the first feature.

- [ ] **Step 6: Implement versioned prototype phase heuristics**

Keep heuristic constants in `PhaseConfig(version="phases.v1-provisional")`; label contact as a body-motion proxy everywhere.

- [ ] **Step 7: Verify the stroke/phase session**

Run: `uv run --locked pytest packages/biomechanics/tests/test_signals.py packages/biomechanics/tests/test_segmentation.py packages/biomechanics/tests/test_phases.py -v`  
Expected: PASS.

- [ ] **Step 8: Commit the stroke/phase session**

```powershell
git add packages/biomechanics
git commit -m "feat: add overhead clear segmentation and phase prototypes"
```

---

### Task 7: Versioned Feature Registry and First Arm-Extension Feature

**Files:**
- Create: `packages/biomechanics/formcheck_biomechanics/features/base.py`
- Create: `packages/biomechanics/formcheck_biomechanics/features/registry.py`
- Create: `packages/biomechanics/formcheck_biomechanics/features/arm_extension.py`
- Create: `packages/biomechanics/formcheck_biomechanics/features/__init__.py`
- Create: `packages/biomechanics/tests/features/test_registry.py`
- Create: `packages/biomechanics/tests/features/test_arm_extension.py`

**Interfaces:**
- Consumes: Normalized pose, eligible stroke window, view, and feature/geometry models.
- Produces: `FeatureExtractor.compute(context: FeatureContext) -> FeatureValue`, `FeatureRegistry.extract_all(context) -> tuple[FeatureValue, ...]`, and registered feature `dominant_elbow_angle_at_max_wrist_height_deg` version `1`.

- [ ] **Step 1: Write failing registry tests**

Assert unique `(name, version)` registration, deterministic order, explicit requirements metadata, and no implicit discovery/import side effects.

- [ ] **Step 2: Implement feature protocol and registry**

Expose required landmarks, supported views, handedness policy, units, and confidence strategy as metadata.

- [ ] **Step 3: Write failing arm-extension feature tests**

Assert a known shoulder-elbow-wrist geometry at maximum wrist height returns the expected degrees and unit; left/right canonical equivalents match; unsupported view, missing scale, or missing required landmark returns unavailable with no value.

Add the review-focus case: when the wrist/elbow/shoulder becomes missing or falls below confidence around the apparent maximum, do not select an adjacent low-confidence maximum; return `available=False` with reason `unstable_or_unreliable_maximum`.

- [ ] **Step 4: Implement the first feature**

Select the reliable maximum/narrow neighborhood inside the stroke window, require a stable maximum across configured neighboring samples, calculate the planar joint angle, and aggregate confidence conservatively. Use version `1` and unit `deg`.

- [ ] **Step 5: Verify the feature session**

Run: `uv run --locked pytest packages/biomechanics/tests/features -v`  
Expected: PASS.

- [ ] **Step 6: Commit the feature session**

```powershell
git add packages/biomechanics
git commit -m "feat: add versioned arm extension feature"
```

---

### Task 8: Deterministic Rule Engine and Diagnostic Isolation

**Files:**
- Create: `packages/rules/formcheck_rules/definitions.py`
- Create: `packages/rules/formcheck_rules/engine.py`
- Create: `packages/rules/formcheck_rules/projection.py`
- Create: `packages/rules/formcheck_rules/catalog.py`
- Create: `packages/rules/tests/test_engine.py`
- Create: `packages/rules/tests/test_projection.py`
- Create: `packages/rules/tests/test_catalog.py`
- Create: `packages/rules/tests/fixtures/candidate_low_arm_extension.json`
- Modify: `packages/rules/README.md`

**Interfaces:**
- Consumes: `FeatureValue` and rule models from Tasks 2 and 7.
- Produces: `RuleEngine.evaluate(features, context, *, diagnostics_enabled: bool) -> RuleEvaluationResult`, disabled catalog entry `clear.low_arm_extension.v1`, and `production_findings(result) -> tuple[Finding, ...]`.

- [ ] **Step 1: Write failing generic engine tests**

Use a clearly named test-only calibrated rule to pin `not_applicable`, `pass`, `finding`, `inconclusive`, minimum-confidence gating, evidence/version inclusion, and deterministic ordering.

- [ ] **Step 2: Implement whitelisted deterministic rule evaluation**

Do not evaluate arbitrary Python or untrusted expressions. Model supported comparison operators explicitly and require enabled plus calibrated status before constructing `Finding`.

- [ ] **Step 3: Write failing candidate-catalog tests**

Assert `clear.low_arm_extension.v1` is disabled, `not_calibrated`, has no production threshold/severity bands, requires the named feature, and declares the agreed tags/views.

- [ ] **Step 4: Implement the candidate catalog and development threshold injection**

Keep the provisional diagnostic threshold in development/evaluation configuration, not the production catalog. For the first plumbing demonstration only, set `development_low_arm_extension_threshold_deg = 140.0`; an available feature below `140.0 deg` may yield `would_trigger`. Label the value `provisional_test_only`, and do not define production severity bands. Diagnostic evaluation yields only `would_trigger`, `would_pass`, `not_applicable`, or `inconclusive`.

- [ ] **Step 5: Write failing isolation tests**

```python
def test_disabled_would_trigger_never_becomes_finding() -> None:
    result = evaluate_disabled_candidate_with_triggering_feature()
    assert result.diagnostics[0].evaluation == DiagnosticOutcome.WOULD_TRIGGER
    assert production_findings(result) == ()
    assert "diagnostics" not in assemble_production_json(result)
```

Also assert diagnostics are absent when `diagnostics_enabled=False` and cannot be parsed as `Finding`.

- [ ] **Step 6: Implement production projection isolation**

Use type-separated inputs: the production findings projector accepts only production evaluations and the production JSON assembler has no diagnostic parameter.

- [ ] **Step 7: Verify the rule session**

Run: `uv run --locked pytest packages/rules/tests -v`  
Expected: PASS.

- [ ] **Step 8: Commit the rule session**

```powershell
git add packages/rules
git commit -m "feat: isolate candidate rule diagnostics"
```

---

### Task 9: Provisional Worker Ports and Pipeline Composition

**Files:**
- Create: `services/worker/analysis/formcheck_analysis/ports.py`
- Create: `services/worker/analysis/formcheck_analysis/testing_ports.py`
- Create: `services/worker/analysis/formcheck_analysis/pipeline.py`
- Create: `services/worker/analysis/formcheck_analysis/cli.py`
- Create: `services/worker/analysis/tests/test_ports.py`
- Create: `services/worker/analysis/tests/test_pipeline.py`
- Create: `services/worker/analysis/tests/test_cli.py`
- Modify: `services/worker/README.md`

**Interfaces:**
- Consumes: All Person 3 package interfaces from Tasks 2--8.
- Produces: Provisional `ArtifactReader`, `ArtifactWriter`, `CancellationPort`, and `ProgressPort`; local test adapters; `AnalysisJobDraft(schema_version, analysis_id, video_object_key, stroke, handedness, view_hint, pipeline_version)`; `AnalysisPipeline.run(job: AnalysisJobDraft, *, development_diagnostics: bool = False) -> AnalysisFindings`; one development CLI.

- [ ] **Step 1: Write failing provisional-port contract tests**

Pin the approved signatures and neutral `ArtifactMetadata`. Assert local reader/writer use logical keys and temporary directories, repeated identical writes return identical metadata/content hash, in-memory progress preserves order, and explicit cancellation raises a typed cancellation exception.

- [ ] **Step 2: Implement provisional protocols and local adapters**

Mark module/class docstrings `PROVISIONAL: requires Person 2 approval`. Do not import infrastructure libraries or choose retry/authentication/retention behavior.

- [ ] **Step 3: Write failing pipeline orchestration tests with fakes**

Assert stage order: materialize, inspect, normalize/write, pose, quality, segmentation, phases, features, rules, assemble. Assert ineligible quality stops downstream faults and returns empty findings; normal development mode includes diagnostics; production mode omits them.

Add the review-focus cancellation test: cancel after materialization, assert normalization is not called and no `preprocessing_completed` event is emitted.

- [ ] **Step 4: Implement pipeline composition and safe progress**

Check cancellation before and after each expensive stage. Report only stable message keys and bounded progress/`None`; never include paths or raw exceptions. Keep pipeline dependencies injectable for unit tests.

- [ ] **Step 5: Write failing CLI tests**

Pin `uv run formcheck-analyze --analysis-id <uuid> --source <path> --handedness right --view rear_three_quarter [--development-diagnostics]`. Assert production JSON omits diagnostics and missing assets/tools return safe actionable stderr and nonzero exit codes.

- [ ] **Step 6: Implement the development CLI**

Use local filesystem adapters only. This is a development command, not Person 2's worker adapter.

- [ ] **Step 7: Verify the worker-composition session**

Run: `uv run --locked pytest services/worker/analysis/tests -v`  
Expected: PASS.

- [ ] **Step 8: Commit the worker-composition session**

```powershell
git add services/worker/analysis services/worker/README.md pyproject.toml uv.lock
git commit -m "feat: compose provisional analysis worker pipeline"
```

Review gate: Person 2 must approve port signatures before production adapters are implemented or integration is called complete.

---

### Task 10: Asset-Gated End-to-End Demonstration and Run Documentation

Coach-labeled pose and rule evaluation harnesses are future validation work. This task does not build them and does not enable a rule. The current demonstration asserts `findings == []` and keeps any `would_trigger` result in development diagnostics only.

**Files:**
- Create: `services/worker/analysis/tests/test_end_to_end_assets.py`
- Create: `services/worker/analysis/README.md`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**
- Consumes: Completed local pipeline and domain outputs.
- Produces: Documented local execution and an asset-gated end-to-end test whose public findings are empty.

- [ ] **Step 1: Write the asset-gated end-to-end test**

Require both environment variables plus FFmpeg/ffprobe. Skip once with a message listing every missing requirement. When available, run local development mode and assert: valid `0-draft` output, canonical pose metadata, quality/stroke/features present when eligible, `findings == []`, and any candidate evaluation is disabled/non-calibrated and exists only in development output.

- [ ] **Step 2: Document setup and commands**

Document uv setup, FFmpeg requirement, environment variables, test markers, expected skips, CLI examples, output separation, current uncalibrated limitations, and the Person 2 review gate. Do not claim end-to-end success without actual assets.

- [ ] **Step 3: Run complete verification**

Run:

```powershell
uv lock --check
uv sync --locked --all-groups
uv run --locked ruff check packages services/worker/analysis
uv run --locked mypy packages/video/formcheck_video packages/pose/formcheck_pose packages/biomechanics/formcheck_biomechanics packages/rules/formcheck_rules services/worker/analysis/formcheck_analysis
uv run --locked pytest packages/video/tests packages/pose/tests packages/biomechanics/tests packages/rules/tests services/worker/analysis/tests -v -ra
git diff --check
```

Expected without assets: lint/type checks PASS; all synthetic tests PASS; asset tests SKIP with explicit reasons; no failures.

- [ ] **Step 4: Inspect scope and tracked artifacts**

Run: `git status --short` and `git diff --name-only HEAD~10..HEAD` (or the actual task commit range).  
Expected: only authorized paths/files; no video, model, pose, `.local` asset, or generated analysis artifact is tracked.

- [ ] **Step 5: Commit the demonstration session**

```powershell
git add services/worker/analysis pyproject.toml uv.lock
git commit -m "test: add uncalibrated analysis demonstration"
```

Final review gates:

- Cross-group review of root Python configuration.
- Person 2 approval of provisional worker ports before production adapters.
- Group A plus Group B approval of the future shared findings schema.
- Asset-backed end-to-end evidence before claiming the sample-video flow works.
- Technique rules remain explicitly uncalibrated. Enabling a rule is future validation work.

