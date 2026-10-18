# Local infrastructure

Owner: Person 2 for the API, Redis, and object-storage stack. Person 4's coaching tables are created from `init/` the first time the Postgres volume is empty.

This Compose file starts the local FormCheck stack:

- PostgreSQL 16 with pgvector (`formcheck` / `formcheck` / database `formcheck`)
- Redis
- S3-compatible object storage (`pgsty/silo`, API port 9000, console port 9001)
- the API on port 8000
- the Dramatiq worker

The first time the Postgres volume is empty, `init/001-coaching.sql` creates the `vector` extension and the coaching tables. Copy `.env.example` to `.env` when you need to override the local defaults. `GET /result` always returns the ratified contract. The retired `FORMCHECK_INTERIM_RESULT_SHIM` variable has no effect.

This Compose file is configured and has not been started on the machine that last edited it. Docker was not available there, so the stack is runtime-unverified until someone with Docker runs `docker compose up`.

Open a terminal in `infra/local`.

Start the stack and wait until it is ready:

```text
docker compose up -d
docker compose ps
```

Check that vector search is available and the coaching tables exist:

```text
docker compose exec postgres psql -U formcheck -d formcheck -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
docker compose exec postgres psql -U formcheck -d formcheck -c "\dt"
```

API docs: `http://localhost:8000/docs`

Stop the stack. Saved data remains:

```text
docker compose stop
```

Stop it and delete saved data:

```text
docker compose down -v
```

The coaching tables are created only the first time the data volume is empty. After `docker compose down -v`, the next `docker compose up -d` creates them again.

`docker compose up --build` also starts Redis, the S3-compatible store, the API on port 8000, and the worker. The existing volume name is `formcheck-pgvector`, so a database created by the earlier Postgres-only file is reused. Init scripts do not rerun on a volume that already has data.
