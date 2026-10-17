# Contributing

## Working agreements

1. Keep each pull request focused on one module or integration contract.
2. Do not commit videos, model weights, extracted pose files, secrets, or copyrighted corpus documents.
3. Add automated tests for behavior changes.
4. Record public input and output changes in `packages/contracts`.
5. Require cross-group review for shared-contract changes.
6. Include model, rule, corpus, and schema versions in generated results.

## Branch naming

```text
frontend/upload-flow
platform/job-lifecycle
analysis/mediapipe-adapter
rag/corpus-ingestion
```

## Pull request checklist

- [ ] The change stays within the documented ownership boundary.
- [ ] Tests cover expected behavior and important failures.
- [ ] Shared schemas and examples remain valid.
- [ ] No secrets or large media artifacts are included.
- [ ] Setup or operational changes are documented.
