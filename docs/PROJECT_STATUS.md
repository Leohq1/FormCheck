# Project status

Date: 2026-10-17. This describes the tree after the coaching merge and the provisional analysis pipeline. The four handoffs below are earlier snapshots and disagree with this file.

## Current contract

- `POST /api/v1/analyses` accepts `overhead_clear` only. `clear`, `smash`, and `drop` return HTTP 400 with `Unsupported stroke type`.
- `GET /result` returns the ratified result (`schema_version` `"1"`). `FORMCHECK_INTERIM_RESULT_SHIM` has no effect.
- The upload form and result screen use that same result shape. Empty findings display “No supported fault detected.”
- `clear.low_arm_extension.v1` stays disabled and uncalibrated. A triggering measurement can appear only in development diagnostics, never as a public finding or coaching fault.
- The fake worker still returns the schema-valid sample finding used by the HTTP demo. The real `formcheck-analyze` pipeline is provisional and is not wired into Dramatiq. A real pre-calibration run returns `findings: []`.

## Still outside this tree

- Consented overhead-clear video (`FORMCHECK_SAMPLE_VIDEO`)
- MediaPipe Pose Landmarker (`MEDIAPIPE_POSE_MODEL_PATH`)
- `GEMINI_API_KEY` and `GEMINI_MODEL` for live generation
- Rights-cleared sources before user-facing citations
- Coach-labeled calibration and the 0.80 held-out precision gate
- A Docker run of the Compose stack on this machine

Missing assets or keys skip the asset tests. They do not fail the ordinary unit suite.

## Handoffs

| File | Use it for |
| --- | --- |
| `docs/HANDOFF_1.md` | Person 1's frontend history and the interim UI shape. Ignore its claim that analysis and the API are missing from `main`. |
| `docs/HANDOFF_PERSON2.md` | Platform routes, Compose services, and the contract file list. |
| `docs/HANDOFF_3.md` | Person 3 session plan, the disabled clear rule, and the normalized-video keys. Ignore the branch-divergence warning. |
| `docs/HANDOFF_PERSON_4.md` | RAG boundaries and the severity/stroke mismatch. Ignore the checkout description. The corpus has since moved past the synthetic fixtures. |
