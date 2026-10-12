# WordPress: two services and persistent data

[Back to Compose examples](../README.md)

Read [compose.yaml](compose.yaml) from top to bottom. WordPress serves HTTP on port 80 using Apache; MariaDB stores its content. WordPress reaches `db:3306` using Compose DNS. Only WordPress's HTTP port is published. The database has no host port and uses an internal backend network. WordPress also has a frontend network for outbound plugin/update requests. `wordpress-data` stores files; `db-data` stores database records.

## Start

From the repository root:

```bash
cd docker/compose/wordpress
docker compose version
```

Before the **first** run, choose two different strong passwords and keep them in a password manager. In Bash, enter them without putting them in command history:

```bash
read -r -s -p 'WordPress database password: ' DB_PASSWORD; printf '\n'
read -r -s -p 'MariaDB root password: ' DB_ROOT_PASSWORD; printf '\n'
export DB_PASSWORD DB_ROOT_PASSWORD
docker compose config --quiet
docker compose up -d
docker compose ps
```

Empty passwords fail validation. Open **http://127.0.0.1:8087** and complete the WordPress installer with a separate site-admin username/password. If the database is still initializing, wait and inspect:

```bash
docker compose logs --tail=50 db wordpress
curl -I http://127.0.0.1:8087
```

An HTTP response or setup redirect shows the web server is responding; completing setup and saving a draft post tests the application/database path. `depends_on` waits for the MariaDB health check, but it does not install WordPress or guarantee the DB stays healthy afterward. `restart: unless-stopped` handles process exits/reboots, not arbitrary unhealthy status.

## Configuration and persistence

- `environment` uses variables from your shell; they are passed to containers. Run `config --quiet`, **not bare `config`**, to avoid printing rendered passwords. Docker administrators can still inspect the environment: this simple example is not a secret vault. For production, use the images' supported file-based secrets and a secure credential workflow.
- A new terminal requires exporting the **same** two database passwords before Compose commands. Environment values initialize a new MariaDB data directory; changing them does not rotate existing DB users' passwords and can break WordPress connectivity. Keep the values stable while reusing the volumes.
- To use a local `.env` instead, create it yourself with `DB_PASSWORD` and `DB_ROOT_PASSWORD`, restrict permissions, and never commit it; the folder ignores `.env*`. Shell variables take precedence over `.env`.
- The WordPress PHP tag and MariaDB family tag receive changes. Back up database and files before updates; pin tested image digests if you need exact repeatability. A volume is not a backup.

## Stop and explore

```bash
docker compose stop
docker compose start
# Remove this project's containers/network, keeping both named volumes:
docker compose down
```

With the same credentials exported, run `docker compose up -d` again and check that your draft post remains. Both database records and WordPress files matter for restoration. Do not add `-v`, rename the project, or delete volumes to fix a password mismatch; first diagnose the existing state. An explicit project-name change selects different volumes and can look like lost data.

Try changing only host port `8087`, rerun `up -d`, and observe that `WORDPRESS_DB_HOST` stays `db:3306`: host port mappings do not change container-to-container ports. This is a local HTTP lab, not a public WordPress deployment.

**References:** [WordPress image](https://hub.docker.com/_/wordpress) · [MariaDB image](https://hub.docker.com/_/mariadb) · [Compose interpolation](https://docs.docker.com/compose/how-tos/environment-variables/variable-interpolation/).
