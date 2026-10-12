# Todo app: source-based Compose lab

Build Docker's React/Node todo application from its checked-in source and run it with a private MySQL database. Open **http://127.0.0.1:8092**. This is a local learning lab, not a public deployment.

## Architecture

```text
browser -> 127.0.0.1:8092 -> app (Node/Express :3000, built React assets + /api)
                                  | private database network
                                  v
                              db (MySQL 8.4.8, named volume todo-db-data)
```

The root [`Dockerfile`](Dockerfile) preserves upstream's multi-stage `final` target: it lints/tests/builds the client, runs backend tests via the `test` stage, installs production dependencies with `npm ci --omit=dev`, and serves both static files and API from one Node image. It pins Node 24 LTS; The superseded upstream Dockerfile has been removed. [`compose.yaml`](compose.yaml) builds the locally maintained source in `./upstream` and selects the root Dockerfile. Import provenance, local modifications and selection rationale are in [`UPSTREAM.md`](UPSTREAM.md).

## Setup and configuration

Prerequisites: Docker Engine/Desktop with the Compose v2 plugin, enough disk space for a first multi-stage build, and `openssl` for credential generation. From **this directory** (not `upstream/`):

```sh
sh scripts/init-env.sh
# Inspect the resolved lab definition before starting:
docker compose -f compose.yaml config --quiet
docker compose -f compose.yaml up -d --build
docker compose -f compose.yaml ps
```

`init-env.sh` creates an ignored mode-0600 `.env` containing distinct random `MYSQL_PASSWORD` and `MYSQL_ROOT_PASSWORD`, and will not overwrite one. Keep that file while retaining the database volume: MySQL's initialized credentials do not automatically change when `.env` changes. If `.env` is lost, restore it from backup rather than generate a different password for the same volume. `MYSQL_DB=todos`, `MYSQL_USER=todo`, and `MYSQL_HOST=db` are set by Compose; change these only with a deliberate database migration. The first image build and database initialization may take several minutes. The database health probe tests the app account and database before Node starts, and the app health probe fetches `/api/items`.

## Test and operate

```sh
curl -fsS http://127.0.0.1:8092/api/items  # initially []
# Create a disposable item; write requests change the persistent database:
curl -fsS -H 'Content-Type: application/json' -d '{"name":"Compose practice"}' http://127.0.0.1:8092/api/items
curl -fsS http://127.0.0.1:8092/api/items
# See service status or diagnose failed startup:
docker compose -f compose.yaml ps
docker compose -f compose.yaml logs --tail=100 app db
```

Visit the browser URL to exercise the UI. To stop and retain data, run `docker compose -f compose.yaml stop`; resume with `docker compose -f compose.yaml start`. To remove containers/networks while retaining the named volume, use `docker compose -f compose.yaml down`. Do **not** use `down -v` as a routine stop: it deletes the database volume. Back up `.env` and database data before intentional migrations or cleanup. `docker compose -f compose.yaml build --no-cache app` rebuilds after a source edit; follow with `docker compose -f compose.yaml up -d --no-deps app` only if the DB is already running and healthy. Superseded upstream development configurations are no longer included.

## Source checks without Docker

Use Node **24.18.0** (24 LTS), npm, and an internet connection. Native SQLite source compilation additionally needs Python, `make`, and a C++ compiler. These commands use the current maintained source. `node_modules` and build output are ignored. Backend SQLite tests use `:memory:`; the HTTP smoke test briefly binds loopback port 3000 and terminates its server. No lab DB or `.env` is read.

```sh
(cd upstream/backend && npm ci --include=dev && npm test)
(cd upstream/client && npm ci --include=dev && npm run lint && npm test && npm run build)
(cd upstream/backend && npm audit)  # exits nonzero for known development advisories
(cd upstream/backend && npm audit --omit=dev)  # separate production-dependency check
(cd upstream/client && npm audit)
```

The Docker context's `.npmrc` deliberately disables dependency install scripts; the root Dockerfile explicitly compiles SQLite and copies that artifact into later stages. Direct host installs above use npm's normal lifecycle handling. If scripts are disabled by your npm policy, run SQLite's trusted install step explicitly or compile it with the required toolchain; do not enable arbitrary dependency scripts globally.

[`VALIDATION.md`](VALIDATION.md) records exact checks, audit totals and remaining third-party deprecations. React hooks and CommonJS are supported APIs, not deprecated merely because newer examples look different. React 19 ignores function-component `propTypes`; those ineffective checks were removed rather than represented as runtime validation. UI request failures now retain data and show an error. This lab still has no authentication or API input-validation layer.

## Scope and security

Only the application is published, on IPv4 loopback port 8092; MySQL has no published port. No Docker socket, reverse proxy, phpMyAdmin, or public management UI is included. The database is on an internal Compose network; the app is also on a normal network so its frontend can be accessed. The app runs as `node` with a read-only root filesystem, `/tmp` tmpfs, dropped capabilities, and no-new-privileges; MySQL needs a writable named volume. Credentials are supplied to containers through environment variables (readable to Docker administrators and by `docker inspect`), not Docker secrets. This does not provide HTTPS, authentication, rate limiting, backups, or production-grade secret management; do not expose it on an untrusted network. Pinning image digests and using npm locks improve repeatability, not security guarantees. The refreshed client and backend production dependency audits were clean; backend development tooling still has advisories and two transitive deprecated packages. Review [`VALIDATION.md`](VALIDATION.md) and rerun audits before deployment.

## Provenance and verification boundary

The upstream baseline revision and subsequent local refactor are documented in [`UPSTREAM.md`](UPSTREAM.md). Host-side backend/client tests and the client build were exercised; details are in [`VALIDATION.md`](VALIDATION.md). This host had no Docker daemon or CLI, so container build/start, health behavior, and persistence across restarts were **not** exercised here. Compose syntax/rendered paths and published port can be checked without a daemon using Compose's `config` command; the commands above are the runtime checklist for a Docker-equipped machine.
