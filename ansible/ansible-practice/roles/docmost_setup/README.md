Role Name
=========

Deploy [Docmost](https://github.com/docmost/docmost) (open-source Confluence
alternative) with Docker Compose via Ansible, reverse-proxied through Traefik.

Requirements
------------

- Docker and Docker Compose v2 installed on the target host (`docker_setup` role)
- The `community.docker` Ansible collection (see `requirements.yml`)
- A Traefik reverse proxy exposing the `web_net`/`app_net` networks
  (`traefik_setup` role)
- `main_domain` and `project_dir` set in `inventory/group_vars/all/general.yml`

Role Variables
--------------

See `defaults/main/main.yml` for all configurable variables.

| Variable | Default | Description |
|---|---|---|
| `docmost_image_tag` | `latest` | Docmost Docker image tag |
| `docmost_postgres_image_tag` | `18` | PostgreSQL image tag |
| `docmost_redis_image_tag` | `8` | Redis image tag |
| `restart_policy` | `always` | Container restart policy |
| `service_dir` | `{{ project_dir }}/docmost` | Service directory on the remote host |
| `docmost_main_domain` | `docs.{{ main_domain }}` | Public domain served by Docmost |
| `docmost_main_url` | `https://{{ docmost_main_domain }}` | Public base URL (also APP_URL) |
| `docmost_port` | `3000` | Port the app listens on inside the container |
| `docmost_jwt_token_expires_in` | `30d` | JWT token lifetime |
| `docmost_file_upload_size_limit` | `50mb` | Maximum upload size |
| `docmost_disable_telemetry` | `true` | Disable anonymous usage telemetry |
| `docmost_storage_driver` | `local` | Storage driver: `local` or `s3` |
| `docmost_s3_endpoint` | `http://minio-api.{{ main_domain }}` | MinIO endpoint (S3 mode) |
| `docmost_s3_region` | `us-east-1` | S3 region (S3 mode) |
| `docmost_s3_bucket` | `docmost` | S3 bucket name (S3 mode) |
| `docmost_mail_enable` | `false` | Enable outgoing email via SMTP |
| `docmost_mail_driver` | `smtp` | Mail driver (`smtp` or `postmark`) |
| `docmost_mail_from_address` | `docmost@{{ main_domain }}` | From address for emails |
| `docmost_mail_from_name` | `Docmost` | From name for emails |
| `docmost_smtp_host` | `127.0.0.1` | SMTP server host |
| `docmost_smtp_port` | `587` | SMTP server port |
| `docmost_smtp_secure` | `false` | Use TLS on the SMTP connection |
| `docmost_smtp_ignore_tls` | `false` | Ignore TLS certificate errors on SMTP |

Layout
------

- All configuration lives in `templates/.env.j2`, which is templated to
  `{{ service_dir }}/.env` (mode `0600`). Values come from
  `defaults/main/main.yml` (non-secret) and `defaults/main/vault.yml`
  (secrets).
- `docker-compose.yml` reads those values through Compose interpolation
  (`${APP_URL}`, `${APP_SECRET}`, ...) — the same split used by
  `gitlab_setup`. The `environment:` section of the `docmost` service only
  references the `.env` variables.
- S3 and SMTP blocks are emitted only when their variables are actually
  configured. Both `.env` and `docker-compose.yml` render the S3 block when
  `docmost_storage_driver == 's3'` **and** both `docmost_s3_username` and
  `docmost_s3_password` are non-empty. The SMTP block is rendered when
  `docmost_mail_enable` is true **and** `docmost_smtp_host` is non-empty.

Secrets (vault)
---------------

Secrets live in `defaults/main/vault.yml`, encrypted with `ansible-vault`:

    ansible-vault edit defaults/main/vault.yml

| Variable | Description |
|---|---|
| `docmost_app_secret` | App secret, min 32 chars (`openssl rand -hex 32`) |
| `docmost_db_password` | PostgreSQL password; use URL-safe characters so it can be embedded in `DATABASE_URL` |
| `docmost_s3_username` / `docmost_s3_password` | MinIO credentials (only used in S3 mode) |
| `docmost_smtp_username` / `docmost_smtp_password` | SMTP credentials (only used when `docmost_mail_enable` is true) |

The `requirements` superuser is created on first launch through the web UI
(`/setup`) after deployment.

Dependencies
------------

- `docker_setup` (Docker must be installed on the target host)
- `traefik_setup` (provides the `web_net` network and the TLS certresolver)

Example Playbook
----------------

See `playbooks/docmost.yml`:

    - hosts: all
      become: true
      gather_facts: true
      roles:
        - docmost_setup

Tags
----

- `install_docmost`, `setup_docmost` — run the whole role
- `preparing` — create networks, service directory, compose + env files
- `pull` — pull the Docker images
- `deploy` — start the stack and wait for Docmost to answer health checks

License
-------

MIT

Author Information
------------------

https://github.com/amati-sh