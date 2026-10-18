# Person 3 Session 1 Handoff

## Purpose

This document lets another agent or developer resume Person 3's analysis-pipeline work without reconstructing the decisions from chat history. Session 1 established the Python workspace only. It did not implement video processing, pose models, biomechanics, rules, or production worker adapters.

## Repository and branch state

- Parent feature branch: `analysis/mediapipe-adapter`
- Session branch: `analysis/session-1-python-scaffold`
- Isolated worktree: `.worktrees/session-1-python-scaffold/`
- Session branch base: `0f77ba3` (`chore: ignore local worktrees`)
- Implementation commits:
  - `4241373` — `build: initialize person 3 python workspace`
  - `6bf18c2` — `fix: keep a single headless OpenCV provider`
- The worktree must remain available until the review is resolved.
- Do not merge directly into `main`. The Session 1 PR targets `analysis/mediapipe-adapter`.

## Authoritative documents

- Working design: `packages/pose/docs/person3-analysis-pipeline-design.md`
- Test-first implementation plan: `packages/pose/docs/person3-analysis-pipeline-implementation-plan.md`
- This handoff: `packages/pose/docs/person3-session-1-handoff.md`

The implementation plan contains ten sessions. Only Task/Session 1 is complete. Continue with Session 2 only after the root configuration receives the required cross-group review.

## Ownership and authorized changes

Person 3 owns:

```text
packages/video/
packages/pose/
packages/biomechanics/
packages/rules/
services/worker/analysis/
evals/pose/
evals/rules/
```

The team explicitly authorized these shared/setup files for Person 3's initial Python scaffold:

```text
pyproject.toml
uv.lock
.python-version
.gitignore
.local/README.md
```

Root configuration changes require review by at least one Group A member and one Group B member.

## What Session 1 implemented

- Root project `formcheck-analysis`, version `0.1.0`.
- Python requirement `>=3.12,<3.13` and `.python-version` set to `3.12`.
- One committed cross-platform `uv.lock`; no `requirements.txt` and no direct-pip workflow.
- Base dependencies: NumPy and Pydantic.
- `analysis` dependency group: MediaPipe, `opencv-python-headless`, and SciPy.
- `test` group: pytest and Hypothesis.
- Default `dev` group: includes `analysis` and `test`, plus Ruff and mypy.
- Central pytest markers and test paths, Ruff Python 3.12 settings, and strict mypy settings.
- Importable versioned packages:
  - `formcheck_video`
  - `formcheck_pose`
  - `formcheck_biomechanics`
  - `formcheck_rules`
  - `formcheck_analysis`
- A smoke test that verifies all five packages import and report version `0.1.0`.
- A regression test that verifies exactly one installed distribution owns `cv2/` files.
- Local asset/setup documentation and ignore rules.

## Important dependency decision: one OpenCV provider

The first review found that MediaPipe 1.1.1 transitively selected `opencv-contrib-python` while the approved direct dependency selected `opencv-python-headless`. Both distributions install the same `cv2` paths and had different hashes for the native module, so the environment was unsafe even though `import cv2` passed.

Resolution:

- Keep `opencv-python-headless` as the single explicit provider.
- Use uv's version-scoped dependency exclusion for MediaPipe 1.1.1's `opencv-contrib-python` dependency.
- Lock 39 packages with no contrib OpenCV distribution.
- Test the installed metadata to ensure exactly one provider owns `cv2/`.
- Reinstall the headless distribution once during repair so files previously overwritten by contrib were restored.

This is intentionally a version-scoped exception. A MediaPipe upgrade must revisit the exclusion and rerun the sole-provider test. Session 4 must validate real Pose Landmarker inference with the headless provider; successful imports do not prove inference compatibility. If MediaPipe requires a contrib-only API, stop and bring the dependency choice back for cross-group review rather than silently reinstalling both packages.

## Local tools and assets

uv 0.13.1 was installed only inside the ignored worktree path `.local/tooling/uv` for this session. It is not committed and does not modify a user shell profile. Other developers should install the reviewed uv version using the official installer.

Future optional assets:

```text
FORMCHECK_SAMPLE_VIDEO=.local/samples/overhead_clear.mp4
MEDIAPIPE_POSE_MODEL_PATH=.local/models/pose_landmarker_full.task
```

Neither asset is currently present or required for Session 1. Never commit them. Tests added in later sessions must skip explicitly when their required variables are missing or invalid.

## Verification evidence

Final verification used Windows CPython 3.12.10 and the committed lockfile:

```powershell
uv lock --check
uv sync --locked --all-groups
uv run --locked python -c "import cv2, mediapipe, numpy, pydantic, scipy"
uv run --locked pytest -v
uv run --locked ruff check packages services/worker/analysis
uv run --locked mypy packages/video/formcheck_video packages/pose/formcheck_pose packages/biomechanics/formcheck_biomechanics packages/rules/formcheck_rules services/worker/analysis/formcheck_analysis
git diff --check
```

Observed result at handoff:

- Lock and sync: passed, 39 packages.
- Dependency imports: passed.
- Pytest: 2 passed, 0 failed.
- Ruff: passed.
- mypy: passed for all five package skeletons.
- Worktree: clean before adding this handoff document.

## Decisions governing later sessions

- Missing/unreliable measurements remain unavailable; never invent them.
- Relative MediaPipe z is non-metric and is excluded from the first feature/rule.
- Handedness and view hint come from Person 2's `AnalysisJob`; Person 3 does not infer them in the MVP.
- Sub-720p source video may continue with a warning; MP4/MOV and 30–120 fps remain the accepted input boundary.
- Normalization emits H.264/AVC `yuv420p`, 60 fps for source rates at least 50 fps and otherwise 30 fps, with even dimensions, rotation applied, audio removed, and timestamps rebased.
- Each normalized output frame maps to the nearest decoded source PTS; ties choose the earlier timestamp.
- The first feature is `dominant_elbow_angle_at_max_wrist_height_deg`.
- `clear.low_arm_extension.v1` remains disabled and `not_calibrated`.
- Development diagnostics may say `would_trigger`; production `findings` remains empty until a rule reaches at least 0.80 held-out coach-labeled precision.
- Production serialization excludes candidate diagnostics structurally.
- Until cross-group schema approval, internal output uses `schema_version: "0-draft"`.

## Person 2 integration boundary

Person 3 will propose provisional protocols in `services/worker/analysis/ports.py` for:

```text
ArtifactReader
ArtifactWriter
CancellationPort
ProgressPort
```

Person 2 must approve their signatures and provide production adapters. Person 3 must not import MinIO, Redis, Dramatiq, database models, API code, credentials, retry policy, retention policy, or deletion policy.

Logical object keys are:

```text
analyses/{analysis_id}/source/{filename}
analyses/{analysis_id}/normalized/video.mp4
analyses/{analysis_id}/normalized/timestamps.json
```

Production worker integration is not complete until Person 2 approves the ports.

## Person 4 integration boundary

Person 4 receives production `AnalysisFindings` containing quality, stroke/phases, features, findings, and versions. Person 4's RAG pipeline derives faults only from `findings`; it may use quality/phase limitations to qualify wording but may not infer faults from features.

Candidate diagnostics are never sent to Person 4. Empty findings is a valid result and must not cause invented coaching advice. Person 4 should review finding IDs/labels, evidence units, retrieval tags, severity/confidence semantics, limitation fields, empty-findings behavior, and the future shared schema as the Group B reviewer.

## Review gates still open

1. Group A review of the root Python/uv configuration.
2. Group B review of the root Python/uv configuration.
3. Task 4 validation that MediaPipe inference works with the sole headless OpenCV provider.
4. Person 2 approval of provisional worker ports before production adapters.
5. Group A and Group B approval of the future `analysis-findings.schema.json`.
6. Coach-labeled evaluation before enabling any production rule.

## Next step

After the Session 1 PR is approved and incorporated into `analysis/mediapipe-adapter`, start Session 2 from the implementation plan: canonical domain models and the internal `0-draft` findings contract.

Session 2 must use the subagent-driven workflow, begin with failing model/serialization tests, and stop after its own independent task review. It must not draft the shared JSON schema or begin video/MediaPipe implementation.

