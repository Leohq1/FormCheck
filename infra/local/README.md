# Local infrastructure

Owner: Person 2 for the API, Redis, and MinIO stack. The file here now starts only the PostgreSQL database Person 4 needs for coaching retrieval.

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

Redis, MinIO, the API, and the worker are not in this file yet. Person 2 still owns those services.
