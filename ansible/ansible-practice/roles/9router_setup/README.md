Role Name
=========

Deploy [9router](https://github.com/decolua/9router) with Docker Compose via Ansible, including its [Headroom](https://github.com/chopratejas/headroom) dependency.

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
| `nine_router_image_tag` | `latest` | 9router Docker image tag |
| `nine_router_headroom_image_tag` | `latest` | Headroom Docker image tag |
| `restart_policy` | `always` | Container restart policy |
| `service_dir` | `{{ project_dir }}/9router` | Service directory on the remote host |
| `nine_router_port` | `20128` | Port 9router listens on |
| `nine_router_data_dir` | `/app/data` | Data directory inside the container |
| `nine_router_node_env` | `production` | Node.js environment |

Layout
------

- All configuration lives in `templates/.env.j2`, which is templated to
  `{{ service_dir }}/.env` (mode `0600`). Values come from
  `defaults/main/main.yml` (non-secret) and `defaults/main/vault.yml`
  (secrets).
- `docker-compose.yml` reads those values through Compose interpolation
  (`${image_tag}`, `${port}`, ...) and also passes the `.env` file to the
  9router container via `env_file`.

Dependencies
------------

- `docker_setup` (Docker must be installed on the target host)

Example Playbook
----------------

See `playbooks/9router.yml`:

    - hosts: all
      become: true
      gather_facts: true
      roles:
        - 9router_setup

Tags
----

- `install_9router`, `setup_9router` — run the whole role
- `preparing` — create networks, service directory, compose + env files
- `pull` — pull the Docker images
- `deploy` — start the stack

License
-------

MIT

Author Information
------------------

https://github.com/amati-sh
