# Local infrastructure

Owner: Person 2.

Docker Compose runs PostgreSQL (pgvector), Redis, MinIO, the FastAPI service, and the Dramatiq worker.

## Quick start

```bash
cd infra/local
cp .env.example .env
docker compose up --build
```

API: `http://localhost:8000`  
OpenAPI docs: `http://localhost:8000/docs`  
Object storage console: `http://localhost:9001` (formcheck / formchecksecret)

> Note: Compose uses `pgsty/silo` + `pgsty/mc` because official `minio/minio` / `minio/mc` images were removed from Docker Hub in 2026.

Point the web app at the API:

```bash
cd ../../apps/web
VITE_API_BASE_URL=http://localhost:8000 npm run dev
```

## Services

| Service | Port | Role |
|---|---|---|
| postgres | 5432 | Job metadata, results JSON, audit, deletion outbox |
| redis | 6379 | Dramatiq broker |
| minio | 9000 / 9001 | Private object storage |
| api | 8000 | Public HTTP API |
| worker | — | Fake analysis pipeline (replaceable by Group B) |

## Notes

- Presigned upload URLs use `MINIO_PUBLIC_ENDPOINT` (`http://localhost:9000`) so the browser can PUT directly.
- Object keys follow `analyses/{id}/source/{filename}` (see team decisions).
- Fake worker outcomes can be forced by putting `inconclusive`, `failed`, or `expired` in the filename (same convention as the frontend mock).
