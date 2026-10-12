# WordPress with Nginx and PHP-FPM

A three-service lab demonstrating that an HTTP server and PHP runtime are different
components. It is fully configured for local use; no hand-written WordPress install is needed.

## Architecture and components

```text
Browser (127.0.0.1:8085)
  Nginx (HTTP :8080, frontend network)
    WordPress PHP-FPM (FastCGI :9000, frontend + backend)
      MariaDB (:3306, private backend)
```

| Component/file | Role |
| --- | --- |
| `compose.yaml` | Isolated project, networks, startup dependency, volumes and secret grants. |
| `nginx/default.conf` | Complete server-block include for `/etc/nginx/conf.d/`; not a full `nginx.conf`. |
| `nginxinc/nginx-unprivileged:1.30-alpine` | Non-root HTTP server; serves static files and forwards PHP to FPM. |
| `wordpress:7.1.1-php8.3-fpm` | Official WordPress runtime; FastCGI is not an HTTP endpoint. |
| `mariadb:11.8` | Private database with official readiness check. |
| `wordpress_data` | Shared web root: writable in WordPress, read-only in Nginx at the same `/var/www/html` path. |
| `db_data` | Persistent database files. |
| `setup-secrets.sh` | Generates private local password files without replacing existing credentials. |

The Nginx `try_files` fallback sends WordPress permalinks to `index.php`.
`SCRIPT_FILENAME` points to the identical shared path in the FPM container.
PHP scripts in uploads, `wp-config.php`, and hidden files are denied. Nginx's request
limit is 16 MB, but PHP's own limits can be lower; this lab does not tune large uploads.

From the repository root:

```bash
cd docker/scenario/wordpress-nginx
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

Wait for MariaDB initialization (first startup may take a minute), then open <http://127.0.0.1:8085/> and complete the WordPress setup wizard with a **new local admin account**.
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

HTTP and Nginx configuration checks:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8085/
docker compose exec nginx nginx -t
```

Before setup, expect an HTTP redirect to the installer; after setup, expect your
site. `nginx -t` checks configuration only, not PHP/database behavior.

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
