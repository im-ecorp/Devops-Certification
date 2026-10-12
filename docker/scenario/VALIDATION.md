# Scenario validation boundary

Checked on 2026-10-12. These files are implemented learning stacks, but this
authoring environment has no Docker Engine/daemon/socket. No stack was deployed,
no existing endpoint was changed, and no existing database was accessed.

## Checks performed

- Real standalone Docker Compose v5.6.0 (release checksum verified) rendered all
  four root Compose files successfully after their documented local secret setup.
- Assertions checked 3/3/2/5 services respectively, localhost-only published ports
  8085, 8086, 8092, 8093/8094, unpublished databases/cache, private backend networks,
  and absence of Docker socket mounts.
- WordPress setup scripts generated ignored password files and repeated runs reused
  the passwords. Host secret directories are mode 0700; files are mode 0444 so PHP
  workers can read their container mounts. No existing secrets were replaced.
- Real Traefik 3.7.14 (release checksum verified) loaded a temporary copy of the
  dynamic WordPress router and forwarded an HTTP request to a temporary localhost
  backend. Path and Host header preservation were asserted. This did not test
  Docker DNS, container privileges, or WordPress/Apache.
- Following the maintenance refactor, tests ran against Todo's actual edited source:
  8 backend suites/12 tests, 3 client suites/10 tests, ESLint and Vite build passed.
  The earlier four-route checks used a validation copy; the newer checks do not.
  Its production npm dependency audits report 0 findings, while backend
  development tooling reports 22 (19 moderate, 3 high).
- Voting's static validator passed source-provenance and maintained-source contracts,
  credential matching, network, readiness, volume, and documentation contracts.
  Its result HTTP tests passed (2), worker harness checks passed (4), and .NET
  10 Release build passed with 0 warnings/errors. npm and NuGet advisory checks
  report 0 current findings. The worker build used an isolated SDK.
- Reviewed local README/provenance links and shell snippets passed checks. See the
  voting lab's [detailed validation record](voting-app/VALIDATION.md) for its own checks.

## Not verified here

Container image builds, Nginx configuration execution, WordPress installer/login,
container health behavior, actual DB queries from applications, voting end to end,
and data persistence across container recreation have **not** been exercised.
Compose validation and host-side application tests do not establish those results.

Run each lab's README checks on a Docker host. In particular:

1. Start one scenario from its root directory and inspect service health/logs.
2. WordPress: run `docker compose exec nginx nginx -t` in the Nginx lab, complete
   the installer, create a post/upload, and verify them after a restart.
3. Todo: add a disposable item using the UI/API and verify it after restart.
4. Voting: cast a vote, check the results UI and the SQL query, then verify stored
   votes after restart. Pending Redis messages are deliberately not persistent.
5. Stop with `docker compose stop`, or remove containers/networks with plain
   `docker compose down`. Do not add `-v` to ordinary cleanup.

## Security limits

Local port binding is not authentication. These examples omit production TLS,
full backup/upgrade operations, and deployment security review. Todo's updated
backend development dependencies still have reported advisories; voting retains
upstream's public hardcoded demo DB login and end-of-life AngularJS frontend.
Neither is a production-secure application.
Superseded development Compose/Swarm/Kubernetes references and old-version
backups were removed from Todo and Voting at the user’s request. Use the root
`compose.yaml` of each lab.

[Back to scenarios](README.md)
