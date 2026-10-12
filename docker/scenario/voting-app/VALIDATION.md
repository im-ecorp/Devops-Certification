# Validation record and handoff

Checked on 2026-10-12 without Docker Engine, Docker daemon, Docker CLI, or a host .NET installation. All downloaded check tools and build artifacts were confined to ignored `.validation/` within this lab. No containers were deployed and no host configuration was changed.

- The standalone Docker Compose v5.6.0 Linux x86-64 CLI was downloaded into `.validation/` and its SHA-256 compared against the release `checksums.txt`. `./.validation/docker-compose -f compose.yaml config --quiet` passed. Its JSON render confirms exactly two loopback publications (vote 8093, result 8094), five services, no DB/Redis published port, named Postgres volume, and an internal back network. This validates Compose syntax/model without a daemon, **not** image builds or runtime networking.
- SDK 10.0.401 Linux x64 tarball SHA-512 matched Microsoft's release metadata. `dotnet restore -a amd64` and `dotnet publish -c Release -a amd64 --self-contained false --no-restore` succeeded for the worker, matching its Dockerfile build arguments. The first restore on original NuGet packages warned about high/critical advisories; after the targeted updates, restore/build produced no warnings. No runtime DB/Redis interaction was exercised.
- `npm ci --ignore-scripts` for the original Node lock reported 14 audit vulnerabilities. `npm audit fix` on an isolated copy updated compatible lock entries; a subsequent `npm ci --ignore-scripts --audit` against `upstream/result` reported **0 vulnerabilities**. This does not prove all dependencies are safe; the app was not launched. Node `--check upstream/result/server.js`, Python `compileall` for `upstream/vote`, and XML parse of `Worker.csproj` passed.
- Run `python3 validate.py .validation/docker-compose` to repeat static contract and provenance checks locally, or `python3 validate.py docker compose` with installed Docker/Compose. This checks client/DB credential literals, backed-up modifications against the upstream hash manifest, local Markdown links, and Bash code-block syntax.

- `git diff --cached --check` flags inherited whitespace in exported upstream files and a byte-preserved backup. Those files are deliberately not normalized so provenance hashes stay meaningful. The check restricted to lab-authored root files passes.

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
