# Shared contracts

Integration boundary between web, platform, analysis, and RAG.

## Schemas

| File | Producer | Consumer | Draft owner |
|---|---|---|---|
| `common.schema.json` | Shared `$defs` | findings + result | Shared (amend with both groups) |
| `analysis-job.schema.json` | Person 2 | Person 3 | Person 2 |
| `analysis-progress.schema.json` | Worker | Person 2 | Person 2 |
| `analysis-findings.schema.json` | Person 3 | Person 4 | **Person 3** (scaffold until review) |
| `analysis-result.schema.json` | Group B | Person 2 → Person 1 | Person 2 |
| `analysis-error.schema.json` | Platform / worker | Person 1 | Person 2 |

Valid examples live in `examples/`.

## Status

**Proposed — not yet authoritative.** See [docs/adr/0001-shared-analysis-contracts.md](../../docs/adr/0001-shared-analysis-contracts.md).

Until that ADR is signed off by ≥1 Group A and ≥1 Group B reviewer:

- Do not treat these schemas as frozen integration law.
- Person 3 may continue with `schema_version: "0-draft"` provisional findings.
- The Milestone B frontend/API private mapping (`apps/web` types ↔ `services/formcheck/schemas.py`) remains interim and will be realigned **after** sign-off.

## Resolutions pinned in the ADR

- Severity: `minor` | `moderate` | `major`
- Quality: numeric `overall` + `warnings[]`
- Job `video_object_key`: `analyses/{id}/source/{filename}`
- Error: `safe_message`, `retryable`, `remediation[]`, `correlation_id`
- Feedback: Person 4 `feedback` object (§7.7)
- Evidence: structured `[{feature, value, unit}]`
- `pose_estimator`: single name+version string
- Shared defs via `common.schema.json` (no duplicated finding shape)

## Validate examples (required gate)

Schema `$id`s are **relative filenames**. Validate through the registry harness (not a single-file IDE check that only opens `analysis-result.schema.json`):

```bash
pip install -r packages/contracts/requirements.txt
python packages/contracts/validate_examples.py
```

Dependencies are declared in `packages/contracts/requirements.txt` (`jsonschema`, `referencing`) so CI/Docker can install them independently of the API image.

## Sign-off process

1. Open a PR that includes these schemas + the ADR.
2. Request one reviewer from Group A and one from Group B.
3. Record names/dates in the ADR reviewer table.
4. Only after merge: Person 2 aligns API/worker; Person 1 remaps the UI.

## Notes for Person 3

`analysis-findings.schema.json` is a **scaffold from §6.12**. Amend it freely under your ownership, but prefer changing shared shapes in `common.schema.json` (with Group A visibility) so `analysis-result` stays aligned.
