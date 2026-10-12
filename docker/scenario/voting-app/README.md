# Voting app: source-based Compose lab

A local Docker Compose exercise based on [Docker's example-voting-app](https://github.com/dockersamples/example-voting-app). The complete exported source lives in [`upstream/`](upstream/), with revision, license, and modifications in [`UPSTREAM.md`](UPSTREAM.md). Use **this directory's `compose.yaml`**, not `upstream/docker-compose.yml` (a development/debug configuration).

## Architecture

```text
browser :8093 -> vote (Python/Flask + Gunicorn) -> Redis `votes` list
                                                   |
                                              worker (.NET 10)
                                                   |
                                             PostgreSQL 15 `votes` table
                                                   |
browser :8094 <- result (Node.js 24 + Socket.IO) <-+
```

The vote app enqueues JSON containing the `voter_id` cookie and chosen `vote`. The worker consumes Redis and inserts or updates one row per voter ID. The result app polls Postgres and broadcasts counts to browsers. Redis and Postgres are reachable on the internal Compose network only; `vote` and `result` each join front and back networks. A named `db-data` volume persists Postgres data between ordinary restarts. Redis pending votes are deliberately ephemeral.

## Prerequisites and setup

- Docker Engine/Desktop with the **Docker Compose v2 plugin** (`docker compose`) and permission to build and run containers. Allow outbound image pulls and source dependency downloads for the first build. No Docker is installed in the authoring environment, so the image build and end-to-end behavior are **not verified here**.
- Host ports 8093 and 8094 free on loopback. Run commands from this directory:

```bash
cd /root/mygit/Devops-Certification/docker/scenario/voting-app
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --follow vote worker result
```

Open <http://localhost:8093> to vote and <http://localhost:8094> to see results. A first build may take time while Python, npm and NuGet dependencies download. `depends_on: condition: service_healthy` waits for Redis and Postgres before starting their consumers; `vote` and `result` also have HTTP health checks. A healthy result HTTP endpoint alone does not prove DB queries work; check `worker` and `result` logs for data-path errors. Initial results might briefly show zero until the worker creates the table and the result app retries its query.

## Configuration and security boundary

Change the sample choices in `compose.yaml` via `OPTION_A` and `OPTION_B` on the vote service; the upstream Python source reads these variables. Keep them mapped to the two choices `a` and `b` in the UI. The container images are built from `upstream/vote` (final stage), `upstream/result`, and `upstream/worker`; there are no development source bind mounts or exposed Node inspector. `redis:8.2-alpine` and `postgres:15-alpine` are major/minor family tags, not immutable digests. Python 3.11 slim, Node 24 slim, and .NET 10 SDK/runtime come from Dockerfile family tags; dependency manifests originate upstream (Python requirements are unpinned), with targeted worker package patches and a compatible Node lock refresh documented in `UPSTREAM.md`. Review/update image patches and dependencies when reusing this lab. See [VALIDATION.md](VALIDATION.md) for daemon-free checks performed and remaining Docker-host tests.

**Local demo only.** Both upstream clients hardcode the public `postgres/postgres` database login in `upstream/worker/Program.cs` and `upstream/result/server.js`. Compose sets the matching `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB`; changing a Compose variable or adding `.env` alone will **break connectivity**. The credentials are not secrets and cannot be secured by Compose interpolation without source changes to both clients. For anything beyond an isolated lab, refactor both applications to consume a protected secret, rotate database credentials with a deliberate migration, add authentication/TLS and robust health checks, audit dependencies, and back up Postgres. Loopback publishing is not authentication; local processes can access both web endpoints. Cookies are not secure voting identity. Redis is not persisted, so queued votes can be lost on restart; the worker uses a basic pop-then-write flow without delivery guarantees. This app is for Compose learning, not elections or production traffic.

## Test and inspect

```bash
curl -fsS http://127.0.0.1:8093/ > /dev/null
curl -fsS http://127.0.0.1:8094/ > /dev/null
# In a browser, choose Cats or Dogs at :8093; refresh/watch :8094.
docker compose logs --tail=60 worker result
docker compose exec db psql -U postgres -d postgres -c 'SELECT vote, COUNT(*) FROM votes GROUP BY vote;'
```

Expected: the selected option's count becomes visible on the result page and the SQL query shows a matching row. Browser cookies identify repeat votes: submitting again from the same browser **changes** its selection, rather than adding a second row. To test a new voter, use a fresh private browser profile. The sample has no separate automated end-to-end test for this stack.

## Stop and clean up

```bash
docker compose stop          # keeps containers and db-data
docker compose start         # resume
docker compose down          # removes containers/network, keeps db-data
```

Never use `docker compose down -v` as routine cleanup: it **deletes the named Postgres volume and its vote data**. Make an independently verified database backup before intentionally removing data. When an existing Postgres volume is initialized, changing `POSTGRES_PASSWORD` in Compose does not rotate that database password.
