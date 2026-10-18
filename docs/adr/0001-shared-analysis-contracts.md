# ADR 0001 — Shared analysis contracts (Milestone A)

- **Status:** Accepted (merged PR #4, 2026-10-18)
- **Date:** 2026-10-17
- **Owners:** Person 2 (job, progress, result, error); Person 3 (findings)
- **Requires review:** ≥1 Group A and ≥1 Group B before schemas are authoritative

## Context

Milestone B wired Person 1’s frontend to Person 2’s API using a private TypeScript/Pydantic shape. That unblocked UI integration but bypassed Milestone A (`packages/contracts/*.schema.json`) and diverged from Group B’s documented findings/feedback contracts. The design docs also disagree with each other on several fields.

## Decision

1. The **shared integration contract is the design-doc shape**, ratified as JSON Schema under `packages/contracts/`.
2. Person 1’s current `low`/`medium`/`high` severity labels and string `evidence` are **presentation mappings**, not the shared contract. The frontend will remap after sign-off.
3. Person 2 drafts `analysis-job`, `analysis-progress`, `analysis-result`, and `analysis-error`.
4. Person 3 drafts `analysis-findings` (authoritative only after Group A + Group B review). Until then, Person 3 may emit `schema_version: "0-draft"` provisionally; Persons 2 and 4 integrate only against the approved version.
5. Cross-group sign-off is recorded by **merging a PR** that adds these schemas **and** accepting this ADR (reviewers listed below). Verbal-only approval is insufficient.

## Resolutions for internal doc inconsistencies

| Topic | Conflict | Resolution (contract) |
|---|---|---|
| Severity | §9 `minor`/`moderate`/`major` vs examples that only show `moderate` | Enum: `minor` \| `moderate` \| `major`. UI may map to low/medium/high for display. |
| Quality | Numeric `overall` + `warnings[]` (§13 / §6.12) vs frontend enum report | Object: `overall` number in `[0, 1]`, `warnings` string array. |
| Object key | TEAM_DECISIONS §4.4 source path vs ImplementationPlan §5.6 flat `original`/`normalized.mp4` | `AnalysisJob.video_object_key` = `analyses/{analysis_id}/source/{filename}`. Person 3 writes `normalized/video.mp4` and `normalized/timestamps.json`. |
| Error | Tech design `message`/`retryable`/`details` vs TEAM_DECISIONS safe message + remediation | Contract error object: `code`, `safe_message`, `retryable`, `remediation` (string array), `correlation_id`. Optional `details` for non-sensitive structured context only. |

## Additional pins

- Ratified messages use `schema_version: "1"`. Person 3 provisional findings use `"0-draft"` only.
- `AnalysisJob` carries a full job payload (not a bare analysis id). The fake and real workers must accept that message.
- Result coaching body uses Person 4’s `feedback` object (`summary`, `tips`, `limitations`, `model`, `prompt_version`) per ImplementationPlan §7.7 — not the Milestone B frontend `recommendations` flat list.
- Finding `evidence` is a structured array of `{feature, value, unit}` so Person 4 can ground citations.
- **Pose estimator versioning:** §3.3 asks for name and version separately; §6.12 examples use one `pose_estimator` string. **Decision:** keep a single `pose_estimator` string that embeds both (e.g. `mediapipe-0.10`). Split fields later only if evaluation needs them.
- Shared finding/quality/stroke defs live in `packages/contracts/common.schema.json` and are `$ref`’d by both findings and result so Person 3 amendments do not silently diverge from the result contract.
- `analysis_id` uses JSON Schema `format: uuid` (any version). Tech design §13 prefers UUIDv7; the current backend still emits `uuid.uuid4()`. Schemas do not pin version — align generator → v7 in the post-sign-off backend pass if the team wants time-ordered ids.
- Result `findings` and feedback `tips` both enforce `maxItems: 3`.
- When `status` is `completed`, `error` must be `null`. When `status` is `inconclusive`, `failed`, `expired`, or `cancelled`, `error` is required (non-null). Inconclusive uses the error object for remediation / retake guidance (ImplementationPlan §8.5 / §6.6) — there is no separate `inconclusive_reason` / `retake_guidance` field on the ratified result.


## Consequences

- Person 1: small client remap after sign-off (severity labels, evidence rendering, feedback vs recommendations, quality display, error field names).
- Person 2: after sign-off, enqueue real `AnalysisJob`, validate persisted results/errors against schemas, then Alembic / idempotency / retention (downstream).
- Person 3 / 4: continue building to §6.12 / §7.7; findings schema owned by Person 3.
- Current `apps/web/src/api/types.ts` and `services/formcheck/schemas.py` remain interim until the post-sign-off alignment pass.

## Reviewers (sign-off)

| Reviewer | Group | Decision | Date |
|---|---|---|---|
| Leohq1 / junyu101 | A | Approved (team confirmation; PR #4 requested reviewers) | 2026-10-18 |
| mzliu05 | B | Approved (merged PR #4) | 2026-10-18 |

## References

- [TEAM_DECISIONS_AND_RESPONSIBILITIES.md](../TEAM_DECISIONS_AND_RESPONSIBILITIES.md) §4.4, §5
- [ImplementationPlan.md](../ImplementationPlan.md) §3.2, §6.12, §7.7, §8
- [BADMINTON_MOVEMENT_ASSISTANT_TECHNICAL_DESIGN.md](../BADMINTON_MOVEMENT_ASSISTANT_TECHNICAL_DESIGN.md) §9, §13
- Schemas: `packages/contracts/`
