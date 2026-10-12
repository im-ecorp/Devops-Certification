# Upstream provenance

- Repository: https://github.com/dockersamples/example-voting-app
- Revision: [`63e9150ca17af4ed05880d4245e486481f73fcb4`](https://github.com/dockersamples/example-voting-app/commit/63e9150ca17af4ed05880d4245e486481f73fcb4) (`main` HEAD when retrieved; commit date 2024-10-10).
- Initial export: all 51 files tracked at that revision copied into [`upstream/`](upstream/), without a nested `.git`. The baseline SHA-256 manifest is [`upstream-sha256.json`](upstream-sha256.json). It records the original import, including reference files subsequently removed; it is not a checksum manifest of current code.
- License: [`upstream/LICENSE`](upstream/LICENSE) (Apache-2.0) retained with the source. No upstream `NOTICE` file exists at this revision. Result package metadata also declares MIT; retain third-party notices in installed dependencies when redistributing builds.
- Maintained runtime updates: Node 24, .NET 10, Npgsql 10.0.3, Newtonsoft.Json 13.0.4 and StackExchange.Redis 2.13.17. Root `compose.yaml` is the supported lab definition. Superseded upstream Compose/Swarm/Kubernetes/editor/CI references and old-version backups were removed at the user’s request. Licenses, active source, health checks and regression tests remain.

Run the lab from this directory, using root Compose, not an upstream development configuration.

A simpler official alternative is [Docker Awesome Compose `flask-redis`](https://github.com/docker/awesome-compose/tree/master/flask-redis), a two-service page-hit counter with Redis published to the host. We retained the given example because Python, Redis, .NET, Postgres, and Node make queueing, worker consumption, readiness, and volume persistence visible. This remains a local exercise, not a production design.

.NET 7 and Node 18 from this upstream revision are out of support. See the official [.NET lifecycle](https://dotnet.microsoft.com/en-us/platform/support/policy/dotnet-core) and [Node.js releases](https://nodejs.org/en/about/previous-releases). PostgreSQL 15 remains supported per [PostgreSQL's version policy](https://www.postgresql.org/support/versioning/); keeping major 15 preserves upstream volume compatibility. .NET 10 is the current LTS. The retargeted worker publishes successfully on Linux x64 with SDK 10.0.401; this is a host-side compile check, not a container or data-path test. NuGet restoration initially identified vulnerable Npgsql and Redis transitive packages; the targeted updates above remove those restore warnings. The original npm lock had 14 audit findings; the compatible lock refresh now installs with zero reported npm audit findings. These point-in-time checks do not establish production security. Full image builds and runtime integration still need validation where Docker is available; see [VALIDATION.md](VALIDATION.md).

## Application maintenance refactor

Only maintained code is retained; pre-refactor copies have been deleted at the user’s request. The import hash manifest records historical provenance, not a requirement to retain old files.

- Vote page: remove mutable HTTP jQuery and unused cookie plugin; selected state is rendered by escaped Jinja markup, with no external script or font dependency.
- Result server: import `node:path` for its explicit HTML route; declare `express.urlencoded({ extended: false })`; use `Pool.query()` rather than retaining a checked-out database client; schedule the next poll after the current query finishes, including errors.
- Worker: use async database/Redis calls and cancellable delays instead of `.Result`, `Thread.Sleep`, and manual IPv4 DNS resolution. Replace exception-driven insert/update with one parameterized PostgreSQL `INSERT ... ON CONFLICT` statement. Skip malformed JSON instead of terminating the worker.
- Packages: Npgsql 10.0.3 and Newtonsoft.Json 13.0.4; StackExchange.Redis remains 2.13.17. No table migration, credential rotation, volume change, or deployment was performed.
- Regression harnesses: Node HTTP/database-boundary tests and a database-free .NET executable under `upstream/worker/tests/`. These do not prove real Redis/Postgres integration.

The bundled AngularJS frontend remains upstream legacy code; AngularJS is end-of-life. A replacement frontend is a separate migration, not accomplished by updating Node server dependencies. Queue pop/write remains non-transactional: a failed database write can lose the popped vote.
