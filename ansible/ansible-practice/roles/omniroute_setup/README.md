Role Name
=========

Deploy [OmniRoute](https://github.com/diegosouzapw/OmniRoute) with Docker Compose via Ansible.

Requirements
------------

- Docker and Docker Compose v2 installed on the target host (`docker_setup` role)
- The `community.docker` Ansible collection (see `requirements.yml`)
- `main_domain` and `project_dir` set in `inventory/group_vars/all/general.yml`

Role Variables
--------------

See `defaults/main/main.yml` for all configurable variables.

| Variable | Default | Description |
|---|---|---|
| `omniroute_image_tag` | `3.8.51` | OmniRoute Docker image tag (pinned) |
| `omniroute_redis_image_tag` | `8.10.1-alpine` | Redis Docker image tag |
| `restart_policy` | `unless-stopped` | Container restart policy |
| `service_dir` | `{{ project_dir }}/omniroute` | Service directory on the remote host |
| `omniroute_main_domain` | `omniroute.{{ main_domain }}` | OmniRoute main domain |
| `omniroute_cloud_url` | `https://cloud.omniroute.online` | OmniRoute Cloud worker endpoint |
| `omniroute_port` | `20128` | App port inside the container |
| `omniroute_local_port` | `20128` | Host port bound on `127.0.0.1` for SSH-tunnel access |
| `omniroute_require_api_key` | `true` | Require an API key on `/v1/*` |
| `omniroute_auth_cookie_secure` | `true` | HTTPS-only dashboard session cookie |
| `omniroute_memory_mb` | `4096` | Node heap ceiling (`OMNIROUTE_MEMORY_MB`) |
| `omniroute_memory_limit` | `8g` | OmniRoute container memory limit |
| `omniroute_cpu_limit` | `min(vCPUs, 2)` | OmniRoute container CPU limit |
| `omniroute_pids_limit` | `512` | OmniRoute container PID limit |
| `omniroute_redis_maxmemory` | `128mb` | Redis `maxmemory` (LRU eviction) |
| `omniroute_redis_memory_limit` | `256m` | Redis container memory limit |
| `omniroute_redis_cpu_limit` | `0.5` | Redis container CPU limit |

Secrets in `defaults/main/vault.yml`: `omniroute_jwt_secret`,
`omniroute_api_key_secret`, `omniroute_initial_password`,
`omniroute_storage_encryption_key`. Never change or drop the storage
encryption key once the database exists; it becomes unreadable without it.

Sizing
------

The defaults (4 GB Node heap, 8 GB container limit, up to 2 CPUs) cover the
dashboard, normal chat and a coding agent. Limits are ceilings, not
reservations, so idle usage stays low. For several concurrent long-context
agents, upstream recommends `omniroute_memory_mb: "8192"` with
`omniroute_memory_limit: "10g"`. Keep the container limit above the heap.

Layout
------

- All configuration lives in `templates/.env.j2`, which is templated to
  `{{ service_dir }}/.env` (mode `0600`). Values come from
  `defaults/main/main.yml` (non-secret) and `defaults/main/vault.yml`
  (secrets).
- `docker-compose.yml` reads those values through Compose interpolation
  (`${image_tag}`, `${omniroute_main_domain}`, ...) and also passes the `.env` file to the
  OmniRoute container via `env_file`.

Backups and Export All
----------------------

Through Traefik, OmniRoute treats every request as remote because Traefik
adds `X-Forwarded-*` headers. The app blocks its LOCAL_ONLY routes for
remote callers, and `/api/db-backups/exportAll` (the dashboard "Export All"
archive) is one of them, so it returns `403 LOCAL_ONLY` by default.

- **Database export** (`/api/db-backups/export`, a consistent `.sqlite`
  snapshot) is not LOCAL_ONLY. It works through the domain for any logged-in
  session.
- **Export All through the domain:** allow it once with the app's own
  LOCAL_ONLY bypass list. Open Dashboard -> Settings -> Authz, keep the
  bypass switch on, add the prefix `/api/db-backups/exportAll` next to the
  default `/api/mcp/`, and confirm with the dashboard password. The setting
  is stored in the database (the `omniroute_data` volume), so it survives
  redeploys. Only logged-in dashboard sessions or API keys with the `manage`
  scope pass the bypass. Anonymous requests still get 403.
- **Without the bypass:** use the loopback-only port through an SSH tunnel:

      ssh -L 20128:127.0.0.1:20128 <host>
      # then open http://localhost:20128

Automatic backups are written to `db_backups/` inside the `omniroute_data`
volume. Back up that volume from the host as well.

Dependencies
------------

- `docker_setup` (Docker must be installed on the target host)

Example Playbook
----------------

See `playbooks/omniroute.yml`:

    - hosts: all
      become: true
      gather_facts: true
      roles:
        - omniroute_setup

Tags
----

- `install_omniroute`, `setup_omniroute` — run the whole role
- `preparing` — create networks, service directory, compose + env files
- `pull` — pull the Docker images
- `deploy` — start the stack and wait for `/healthz`

License
-------

MIT
