# WordPress with Traefik

A three-service HTTP reverse-proxy lab. Traefik routes HTTP to the Apache variant
of WordPress; it does not speak FastCGI directly to PHP-FPM.

## Architecture and components

```text
Browser (127.0.0.1:8086)
  Traefik (HTTP :8000, frontend network)
    WordPress Apache/PHP (HTTP :80, frontend + backend)
      MariaDB (:3306, private backend)
```

| Component/file | Role |
| --- | --- |
| `compose.yaml` | Services, isolated networks, volumes, secret grants, and static Traefik startup flags. |
| `traefik/dynamic/wordpress.yaml` | Dynamic router/service file; backend is `http://wordpress:80`. |
| `traefik:v3.7.14` | File-provider HTTP proxy with access logging; no dashboard or Docker socket. |
| `wordpress:7.1.1-php8.3-apache` | Official WordPress image with an HTTP server and PHP. |
| `mariadb:11.8` | Private DB, started before WordPress using a readiness check. |
| `wordpress_data`, `db_data` | Separate persistent WordPress and database volumes. |
| `setup-secrets.sh` | Non-overwriting local password generator. |

The entrypoint listens on unprivileged port 8000. The watched **directory** is
mounted read-only, so Traefik can reload dynamic routing changes without container
recreation. The rule ``PathPrefix(`/`)`` matches all requests on this dedicated localhost
entrypoint; a public deployment should use a scoped Host rule and appropriate TLS.
This teaches static versus dynamic configuration without giving Traefik access to
the Docker daemon. Docker-label discovery is intentionally not enabled.

From the repository root:

```bash
cd docker/scenario/wordpress-traefik
```

## Setup and configuration

Prerequisites: Docker Engine/Desktop with Linux containers, Docker Compose v2.20+
(or current Compose), OpenSSL, and internet access to image registries. Use a local
practice machine, not an existing production WordPress volume. Commands below run
from this scenario directory after the initial `cd` from the repository root.

```bash
sh setup-secrets.sh
docker compose config --quiet
docker compose pull
docker compose up -d
```

The setup script creates random DB and root passwords; it never prints them and
refuses to overwrite existing or incomplete secrets. Re-running it reuses both
passwords. It creates `secrets/` with mode 0700 and files with mode 0444: the directory
limits host access, while PHP's non-root workers can read mounted files in containers.
Compose secrets are local bind mounts, **not an encrypted secret vault**. Only the
DB gets the root password; WordPress receives only its application password.
The files are ignored by Git and Docker builds. Do not commit or share them.

No `.env` file or public domain is required. The Compose project name keeps each
lab's networks and volumes separate. For a second independent instance, use a
unique `docker compose -p NAME` consistently for every command and another host
port. Changing project names selects different volumes; it does not migrate data.

DB name/user are `wordpress`. Password files configure initialization of a new
MariaDB volume. Changing them later does not change credentials stored in an
existing database. Preserve them and the volumes; do not regenerate passwords or
remove volumes to troubleshoot authentication failures.

## Verify and complete installation

Wait for MariaDB initialization (first startup may take a minute), then open <http://127.0.0.1:8086/> and complete the WordPress setup wizard with a **new local admin account**.
The DB password is not the WordPress admin password. Health ordering waits for the
DB, not for PHP/Apache to finish copying WordPress files; retry a temporary startup
502/503 rather than resetting volumes.

```bash
docker compose ps
docker compose logs --tail=50 db wordpress
```

Do not publish logs containing personal data or credentials. Create a sample post
and upload a small image in the admin UI, restart the containers, and check that
both remain. That tests the database and WordPress filesystem, not just an HTTP port.

```bash
docker compose restart
```

Routing checks:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8086/
docker compose logs --tail=50 traefik
```

Before setup, expect an installer redirect; after setup, expect your site. Check
Traefik logs for provider/configuration errors. `docker compose config` validates
Compose, not the contents of Traefik's dynamic routing file.

## Stop and resume

```bash
docker compose stop
docker compose start
```

To remove only the lab containers and networks while keeping its named data volumes:

```bash
docker compose down
```

After `down`, use `docker compose up -d` to recreate containers. **Do not add `-v`**:
that deletes the database and WordPress files. Do not use global Docker prune
commands. Data is not a backup: keep independent backups of the database, uploads,
and secret files before any migration, credential rotation, or image upgrade.

## What to learn and limits

- Service names (`db`, `wordpress`) are DNS names inside their Compose networks.
- The DB is attached only to an `internal: true` backend network and has no host port.
  WordPress shares that network and a frontend network; the proxy cannot connect to the DB directly.
- Named volumes preserve the database and WordPress core/plugins/uploads across
  container recreation. The official WordPress entrypoint seeds an empty content volume.
  Changing the image does not by itself guarantee persisted WordPress files are upgraded;
  use a deliberate backed-up upgrade process.
- MariaDB readiness uses its official `healthcheck.sh`; Compose waits with
  `condition: service_healthy`. This is startup ordering, not automatic dependency repair.
- Versioned image tags are explicit but mutable. Inspect and pin verified digests
  for a reproducible deployment; review updates and back up before upgrading.
- These are HTTP-only localhost learning labs. They omit public TLS, backups,
  production resource budgets, mail delivery, and full application hardening.
  Never expose them publicly without a deployment/security review.
- The standard WordPress and MariaDB entrypoints need startup privileges for
  initialization and ownership. Do not force arbitrary `user:` values and break
  them. Nginx/Traefik are unprivileged; application workers use the image defaults.

Sources: [WordPress image](https://hub.docker.com/_/wordpress),
[MariaDB image](https://hub.docker.com/_/mariadb),
[Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/).

[Back to scenarios](../README.md)
