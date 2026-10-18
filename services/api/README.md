# API service

Owner: Person 2.

Implementation lives in the shared package `services/formcheck/` (FastAPI app: `formcheck.api.main:app`).

## Endpoints (frontend contract)

```http
POST   /api/v1/analyses
POST   /api/v1/analyses/{id}/complete-upload
POST   /api/v1/analyses/{id}/cancel
GET    /api/v1/analyses/{id}
GET    /api/v1/analyses/{id}/result
DELETE /api/v1/analyses/{id}
GET    /api/v1/health
```

Optional `Idempotency-Key` header on `POST /analyses` and `DELETE /analyses/{id}` (same key + different body → 409).

Schema migrations: from `services/`, `alembic upgrade head` (API startup also runs migrations, with `create_all` fallback).

Create/upload request aliases still match the frontend (`consent`, `byte_size`, flat `upload_url`).

Persisted **results** and worker **jobs/progress** follow ratified `packages/contracts` (`schema_version: "1"`, `feedback`, numeric quality, structured evidence, `safe_message`/`retryable`/`remediation`).

`GET /result` returns the ratified contract. The legacy result projection has been removed, and `FORMCHECK_INTERIM_RESULT_SHIM` cannot change the response.

Auth after create: `Authorization: Bearer <capability_token>` (token returned once; only a hash is stored).

## Local run (without Compose for the API process)

Start Postgres, Redis, and MinIO via Compose, then:

```bash
cd services
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
set PYTHONPATH=.
set DATABASE_URL=postgresql+psycopg://formcheck:formcheck@localhost:5432/formcheck
set REDIS_URL=redis://localhost:6379/0
set MINIO_ENDPOINT=http://localhost:9000
set MINIO_PUBLIC_ENDPOINT=http://localhost:9000
uvicorn formcheck.api.main:app --reload --port 8000
```

## Tests

```bash
cd services
pip install -r requirements.txt
set PYTHONPATH=.
pytest tests -q
```
