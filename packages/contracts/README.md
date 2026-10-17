# Shared contracts

This directory is the integration boundary between the web, platform, analysis, and RAG modules.

Planned schemas:

```text
analysis-job.schema.json
analysis-progress.schema.json
analysis-findings.schema.json
analysis-result.schema.json
analysis-error.schema.json
```

Every schema needs a version, required and optional fields, enumerated states where applicable, and at least one valid example. Changes require review from both groups.
