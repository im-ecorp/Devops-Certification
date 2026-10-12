# Validation record and handoff

Checked on 2026-10-12 without Docker Engine, Docker daemon, Docker CLI, or a host .NET installation. All downloaded check tools and build artifacts were confined to ignored `.validation/` within this lab. No containers were deployed and no host configuration was changed.

- The standalone Docker Compose v5.6.0 Linux x86-64 CLI was downloaded into `.validation/` and its SHA-256 compared against the release `checksums.txt`. `./.validation/docker-compose -f compose.yaml config --quiet` passed. Its JSON render confirms exactly two loopback publications (vote 8093, result 8094), five services, no DB/Redis published port, named Postgres volume, and an internal back network. This validates Compose syntax/model without a daemon, **not** image builds or runtime networking.
- SDK 10.0.401 Linux x64 tarball SHA-512 matched Microsoft's release metadata. `dotnet restore -a amd64` and `dotnet publish -c Release -a amd64 --self-contained false --no-restore` succeeded for the worker, matching its Dockerfile build arguments. The first restore on original NuGet packages warned about high/critical advisories; after the targeted updates, restore/build produced no warnings. No runtime DB/Redis interaction was exercised.
- `npm ci --ignore-scripts` for the original Node lock reported 14 audit vulnerabilities. `npm audit fix` on an isolated copy updated compatible lock entries; a subsequent `npm ci --ignore-scripts --audit` against `upstream/result` reported **0 vulnerabilities**. This does not prove all dependencies are safe; the app was not launched. Node `--check upstream/result/server.js`, Python `compileall` for `upstream/vote`, and XML parse of `Worker.csproj` passed.
- Run `python3 validate.py docker compose` with installed Docker/Compose to check client/DB credential literals, current source contracts, local Markdown links and Bash code-block syntax. No old source backups are required.

- `git diff --cached --check` flags inherited whitespace in exported upstream files. Those files are deliberately not normalized so provenance hashes stay meaningful. The check restricted to lab-authored root files passes.

## Refactor verification

Repeated against the edited source, not an old validation copy:

- `node --test upstream/result/test/server.test.js`: **2 tests pass**, including an actual local HTTP request. PostgreSQL and Socket.IO are isolated boundary substitutes, not real integration.
- `dotnet run --project upstream/worker/tests/Worker.Tests.csproj`: **4 checks pass** (parameterized upsert, cancellation before dequeue, parsed payload, malformed JSON). Host checks use the isolated SDK with `DOTNET_SYSTEM_GLOBALIZATION_INVARIANT=1` because the authoring host lacks ICU. Do not enable that override by default in containers.
- `dotnet build upstream/worker/Worker.csproj -c Release`: **0 warnings, 0 errors**. `dotnet list ... package --vulnerable --include-transitive` reports no vulnerable packages from current NuGet sources.
- Result `npm audit --json` and `npm audit --omit=dev --json`: **0 findings**.
- `python3 validate.py <standalone-compose>`: **5 services**, expected loopback 8093/8094, internal network, persistent volume, 7 maintained-source differences from the historical import manifest. Removed reference files and deleted backups are not required by the validator.
- No credentials, schema, ports or volume names were changed. Old-version snapshots and cached source copies were subsequently removed at the user’s request.

This closes the previous compile-only boundary, not the container/DB/Redis/browser integration boundary. Existing vendored AngularJS is legacy end-of-life code and was not rewritten. Redis pop/write remains non-transactional. Test-generated crash dumps and old cached result source were subsequently deleted during the requested cleanup.

Remaining checks on a Docker host:

```bash
cd /root/mygit/Devops-Certification/docker/scenario/voting-app
docker compose config --quiet
python3 validate.py docker compose
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 worker result vote
# Visit http://127.0.0.1:8093 and cast a test vote, then check http://127.0.0.1:8094.
docker compose exec db psql -U postgres -d postgres -c 'SELECT vote, COUNT(*) FROM votes GROUP BY vote;'
docker compose down
```

If a first-time build fails (registry, PyPI, npm, NuGet, or Dockerfile), inspect the actual error before modifying packages. Avoid `down -v`, which deletes votes. This is an intentionally insecure local demo; see [README.md](README.md) for the credential and persistence limitations.
