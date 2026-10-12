# Docker Compose scenarios

Multi-container learning labs. Each directory is an independent Compose project
with its own README, configuration, and persistent data. Use Docker with Linux
containers and Docker Compose v2.20+ (or current Compose). Start on a local practice
machine, not a production server.

| Scenario | Architecture | Local URL |
| --- | --- | --- |
| [WordPress with Nginx](wordpress-nginx/README.md) | Nginx, WordPress PHP-FPM, MariaDB; shared web-root volume | <http://127.0.0.1:8085/> |
| [WordPress with Traefik](wordpress-traefik/README.md) | File-provider HTTP proxy, WordPress Apache, MariaDB | <http://127.0.0.1:8086/> |
| [Todo application](todo-app/README.md) | Built React frontend and Node API, private MySQL, multi-stage source build | <http://127.0.0.1:8092/> |
| [Voting application](voting-app/README.md) | Python vote, Redis queue, .NET worker, PostgreSQL, Node.js results | Vote: <http://127.0.0.1:8093/>; results: <http://127.0.0.1:8094/> |

## Learning order

1. Nginx WordPress: service DNS, FastCGI, shared volumes, secret files, and DB readiness.
2. Traefik WordPress: static versus dynamic proxy configuration without a Docker socket.
3. Todo: source builds and an application/database stack.
4. Voting: several languages, asynchronous messaging, and persistent storage.

The Nginx lab uses PHP-FPM; the Traefik lab uses the HTTP-serving Apache variant.
These are two different designs, not interchangeable proxy configuration files.
Both WordPress labs use private database networks, generated secret files, separate
project-scoped volumes, and no exposed database ports.

## Common workflow

Read the chosen lab's README first. It gives the exact setup/configuration and
expected behavior. Run commands **inside that scenario directory**:

```bash
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=50
```

WordPress requires `sh setup-secrets.sh` before starting. Some source builds need
substantial downloads and CPU/RAM. Do not run every scenario at once on a small VM.
Ports are deliberately distinct; use the same project name and configuration on
all lifecycle commands.

## Stop without losing data

```bash
docker compose stop
docker compose start
```

To remove a lab's containers and networks while retaining named data volumes:

```bash
docker compose down
```

Use `up -d` after `down`, not `start`. Never add `-v` unless you explicitly intend
to delete that lab's data and have a verified independent backup. Avoid global
prune commands. Persistent volumes are not backups; preserve password files too.

## Scope and safety

These labs are for local learning, not public production deployments. Review
security, TLS, credentials, dependencies, resource limits, and backup/upgrade
procedures before adapting them. Secrets under ordinary Compose are local file
mounts, not encrypted vault storage. Upstream source attribution and changes are
recorded in the application labs; do not remove their license notices.

Compose configuration checks do not prove runtime behavior. See the
[validation boundary and Docker-host checklist](VALIDATION.md), then verify the
browser UI, application writes, results, and persistence on a Docker host using
each README's checklist. No Swarm initialization or host reverse-proxy changes
are required.

[Docker directory overview](../README.md) ·
[Dockerfile labs](../dockerfiles/README.md) ·
[Dockerfile best practices](../dockerfile-best-practices.md)
