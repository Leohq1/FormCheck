# Coaching RAG

Owner: Person 4. This package turns structured technique findings into short coaching feedback that cites approved corpus passages.

The slice that is implemented now runs without Person 1, Person 2, Person 3, Docker, or a hosted model. It loads a rights manifest, chunks text on headings, retrieves approved passages with metadata filters and keyword overlap, and writes a deterministic template response. A citation check rejects tips that invent a finding or cite a chunk that was not retrieved.

The coaching text in `tests/fixtures/` is synthetic. It is not a real coaching authority. Do not commit copyrighted manuals.

## Agreement with Person 3

Person 4 agrees with the pre-calibration boundary.

- Read `schema_version: "0-draft"` for local fixtures only. Do not call that output shared-schema compliant. Person 4 is the Group B reviewer for the future `packages/contracts/analysis-findings.schema.json`.
- Create coaching tips only from `findings`. Ignore `features`, quality scores, phase estimates, and any `diagnostics` or `would_trigger` field.
- The first rule id is `clear.low_arm_extension.v1`, label `Low arm extension at maximum reach`. It stays out of production findings until coach-labeled precision is at least 0.80. Empty `findings` are the expected production payload until then.
- Evidence for that rule uses feature `dominant_elbow_angle_at_max_wrist_height_deg` and unit `deg`.
- Retrieval tags for that rule are `overhead_clear`, `contact_reach`, and `arm_extension`.
- Severity is `low`, `moderate`, or `high`, and is copied as supplied. Confidence is a separate 0.0–1.0 value. Wording uses "suggests", names the severity, and prints the confidence. A finding below 0.70 is still explained, with an uncertainty limitation. RAG does not drop or strengthen it.
- Quality warnings RAG will turn into limitations: `contact_uncertain`, `uncertain_contact`, `unsupported_view`, `low_pose_confidence`, `body_not_fully_visible`, and `inconclusive_pose`.
- Empty findings with no inconclusive warning produce "No supported technique fault was found" and no tips. An unsupported view or inconclusive pose produces no tips and does not describe the clear as clean.

## Verify this slice

From the repository root, with the project virtual environment:

```text
.\.venv\Scripts\python.exe -m pytest packages/rag/tests --rootdir=packages/rag -q
```

Create that environment if it is missing:

```text
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e "packages/rag[dev]"
```

What the tests check:

- A source without a license is rejected.
- Heading sections stay separate, and a long section splits below the word budget.
- Retrieval returns only approved overhead-clear passages and skips a different stroke.
- Template feedback cites a retrieved chunk, keeps the supplied finding, and preserves severity.
- An invented citation or an invented finding fails validation.
- If nothing was retrieved, the result has no practice tip and says that no approved passage was available.

## Still to build

1. Agree the shared `AnalysisFindings` and feedback schemas in `packages/contracts/` with both groups. This package currently uses its own Pydantic models.
2. Replace the synthetic fixture corpus with 5–10 rights-approved sources recorded in `corpus/manifests/`. Keep the source files out of git unless their license allows it.
3. Store embeddings from OpenAI `text-embedding-3-small` in the local pgvector database. The database is started from `infra/local`. The embedding column is `vector(1536)` and is empty until an API key is available.
4. Add vector search on top of the same metadata filters, then combine it with keyword ranking. Keep returning 3–6 chunks.
5. Add the hosted generator adapter for GPT-6 Luna: timeouts, limited retries, structured-output validation, and token-cost logging. Keep this template generator as the fallback when the provider fails.
6. Add an Ollama adapter only after the hosted path and fallback are tested.
7. Connect `retrieval` and `generating` in `services/worker/` once Person 2 has a job to call.
8. Build `evals/retrieval/`, `evals/generation/`, and `evals/system/` with a coach. Targets are Recall@5 at least 0.90, 100 percent valid citations, at least 95 percent finding faithfulness, and no critical unsafe output.

## Local database

From `infra/local`:

```text
docker compose up -d
```

Connection values for this container: host `localhost`, port `5432`, database `formcheck`, user `formcheck`, password `formcheck`. An OpenAI API key is still required before embeddings can be written. Put that key in an untracked `.env` file. Do not commit it.
