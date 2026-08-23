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
| `omniroute_image_tag` | `latest` | OmniRoute Docker image tag |
| `omniroute_redis_image_tag` | `8.10.1-alpine` | Redis Docker image tag |
| `nginx_image_tag` | `1.27-alpine` | Export-proxy nginx image tag |
| `restart_policy` | `unless-stopped` | Container restart policy |
| `service_dir` | `{{ project_dir }}/omniroute` | Service directory on the remote host |
| `omniroute_main_domain` | `omniroute.{{ main_domain }}` | OmniRoute main domain |
| `omniroute_cloud_url` | `https://cloud.omniroute.online` | OmniRoute Cloud worker endpoint |

Layout
------

- All configuration lives in `templates/.env.j2`, which is templated to
  `{{ service_dir }}/.env` (mode `0600`). Values come from
  `defaults/main/main.yml` (non-secret) and `defaults/main/vault.yml`
  (secrets).
- `docker-compose.yml` reads those values through Compose interpolation
  (`${image_tag}`, `${omniroute_main_domain}`, ...) and also passes the `.env` file to the
  OmniRoute container via `env_file`.
- `files/nginx-export.conf` is a small nginx sidecar that forwards only the
  LOCAL_ONLY `/api/db-backups/exportAll` endpoint to the app while dropping the
  reverse-proxy forwarding headers. Without it, Traefik's `X-Forwarded-For`
  stamps the request as "remote" and the app answers `403 LOCAL_ONLY`,
  breaking the dashboard "Export All" (backup) button.

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
- `deploy` — start the stack

License
-------

MIT
