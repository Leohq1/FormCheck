# Local infrastructure

Owner: Person 2 for the API, Redis, and object-storage stack. Person 4's coaching tables are created from `init/` the first time the Postgres volume is empty.

The database image is `pgvector/pgvector:pg16`, which is the official Postgres image with the pgvector extension. The local username, password, and database name are all `formcheck`. This password is for the local container only.

Open a terminal in `infra/local` and use these commands.

Start the database and wait until it is ready:

```text
docker compose up -d
docker compose ps
```

Check that vector search is available and the coaching tables exist:

```text
docker compose exec postgres psql -U formcheck -d formcheck -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';"
docker compose exec postgres psql -U formcheck -d formcheck -c "\dt"
```

Stop the database. The saved data remains:

```text
docker compose stop
```

Start it again later:

```text
docker compose start
```

Stop it and delete the saved data:

```text
docker compose down -v
```

The coaching tables are created only the first time the data volume is empty. After `docker compose down -v`, the next `docker compose up -d` creates them again.

`docker compose up --build` also starts Redis, the S3-compatible store, the API on port 8000, and the worker. The existing volume name is `formcheck-pgvector`, so a database created by the earlier Postgres-only file is reused. Init scripts do not rerun on a volume that already has data.
