hermes_webui_setup
==================

Deploy [Hermes WebUI](https://github.com/nesquena/hermes-webui) (web interface
for the Hermes Agent) with Docker Compose via Ansible, reverse-proxied through
Traefik. The container joins `web_net` only; no host port is published.

The role uses the [published image](https://github.com/nesquena/hermes-webui/pkgs/container/hermes-webui)
unchanged, pinned by tag. It builds nothing.

Requirements
------------

- Docker and Docker Compose v2 installed on the target host (`docker_setup` role)
- The `community.docker` Ansible collection (see `requirements.yml`)
- A Traefik reverse proxy exposing the `web_net` network (`traefik_setup` role)
- `main_domain` and `project_dir` set in `inventory/group_vars/all/general.yml`
- An existing Hermes installation on the host: `/root/.hermes/config.yaml`,
  `/root/.hermes/state.db` and `/usr/local/lib/hermes-agent`. The role checks
  for them and never creates them, because an empty Hermes home would start
  the WebUI without any configuration.

Role Variables
--------------

See `defaults/main/main.yml` for all configurable variables.

| Variable | Default | Description |
|---|---|---|
| `hermes_webui_image_tag` | `0.52.353` | Hermes WebUI image tag (pinned) |
| `restart_policy` | `unless-stopped` | Container restart policy |
| `service_dir` | `{{ project_dir }}/hermes-webui` | Service directory on the remote host |
| `hermes_webui_domain` | `hermes.{{ main_domain }}` | Public domain served by Traefik |
| `hermes_webui_url` | `https://{{ hermes_webui_domain }}` | Public URL, also the allowed CORS origin |
| `hermes_webui_port` | `8787` | Port the app listens on inside the container |
| `hermes_webui_password_min_length` | `16` | The role refuses a shorter login password |
| `hermes_webui_force_recreate` | `false` | Recreate the container even when nothing changed |
| `hermes_webui_home_dir` | `/root/.hermes` | Existing Hermes CLI home, mounted as the container's `~/.hermes` |
| `hermes_webui_agent_dir` | `/usr/local/lib/hermes-agent` | Installed Agent source, copied to `agent-source/` |
| `hermes_webui_agent_source_excludes` | `.git/`, `venv/`, ... | Host build artefacts left out of that copy |
| `hermes_webui_workspaces` | `[{path: /root, read_only: false}]` | Host directories mounted at the same path |
| `hermes_webui_workspace_forbidden_paths` | `/etc`, `/usr`, ... | Paths refused as workspaces |
| `hermes_webui_host_fs_enabled` | `true` | Mount the whole host filesystem |
| `hermes_webui_host_fs_mount_point` | `/host` | Where it appears in the container |
| `hermes_webui_host_fs_read_only` | `false` | Mount it read-only |
| `hermes_webui_ssh_enabled` | `true` | Mount the host SSH directory read-only as `~/.ssh` |
| `hermes_webui_ssh_dir` | `/root/.ssh` | Host SSH directory |
| `hermes_webui_ssh_key_name` | `id_rsa` | Private key the host executor uses |
| `hermes_webui_host_executor_enabled` | `true` | Let the agent SSH back to the host (needs `hermes_webui_ssh_enabled`) |
| `hermes_webui_host_alias` | `host.docker.internal` | Name of the Docker host inside the container |
| `hermes_webui_host_ssh_port` | `{{ ansible_port \| default(22) }}` | Host sshd port |
| `hermes_webui_python_version` | `3.14` | Python for the WebUI venv (`UV_PYTHON`); must match the Agent's runtime |
| `hermes_webui_container_path` | `...:/app/venv/bin` | `PATH` in the container, so `hermes` resolves |
| `hermes_webui_secure` | `1` | Secure cookies (Traefik terminates TLS) |
| `hermes_webui_trust_forwarded` | `1` | Trust Traefik's `X-Forwarded-*` headers |
| `hermes_webui_skip_onboarding` | `1` | Use the existing `config.yaml` without the wizard |
| `hermes_webui_skip_chmod` | `1` | Don't change modes of the CLI's credential files |
| `hermes_webui_memory_limit` | `4g` | Container memory limit |
| `hermes_webui_cpu_limit` | `2.0` | Container CPU limit |
| `hermes_webui_log_max_size` / `_file` | `20m` / `5` | Container log rotation |

To upgrade, set `hermes_webui_image_tag` to a newer
[released tag](https://github.com/nesquena/hermes-webui/pkgs/container/hermes-webui)
after testing it with the installed Agent. Avoid `latest`: it changes on every
upstream release, and `0.52.113` failed to install the Agent.

Secrets (vault)
---------------

Secrets live in `defaults/main/vault.yml`, encrypted with `ansible-vault`:

    ansible-vault edit defaults/main/vault.yml

| Variable | Description |
|---|---|
| `hermes_webui_password` | WebUI login password, at least 16 characters |

Agent access to the host
------------------------

The agent runs inside the container, so it only sees what is mounted there.
The role gives it three ways in:

1. **Workspaces** (`hermes_webui_workspaces`, default `/root`) are mounted at
   their host paths, so `/root/mygit/...` in the UI is the same file on the
   host. System directories such as `/etc` or `/usr` are refused, because
   mounting over them replaces the container's own OS.
2. **`/host`** holds the whole host filesystem. The host's `/etc/nginx` is
   `/host/etc/nginx`. The container gets `HERMES_HOST_FS=/host`.
3. **The host executor** runs commands on the host itself (`systemctl`,
   `docker`, `ansible-playbook`). The image has no Ansible, so the agent SSHes
   back to the host through `host.docker.internal`:

       $HERMES_HOST_EXECUTOR_SSH "$HERMES_HOST_EXECUTOR_ENV bash -lc 'cd /root/mygit/Devops-Certification/ansible/ansible-practice && ansible-playbook playbooks/hermes-web-ui.yml'"

   `HERMES_HOST_EXECUTOR_ENV` sets a UTF-8 locale, which Ansible requires and
   a non-interactive SSH session lacks.

> **Security.** With the defaults, a logged-in WebUI session is equal to root
> on this host: it can write the whole filesystem and SSH wherever the mounted
> keys are authorised. Keep the password strong and consider Authelia in front
> of the service. To narrow access, set `hermes_webui_host_fs_read_only: true`,
> `hermes_webui_ssh_enabled: false` (with `hermes_webui_host_executor_enabled:
> false`), or point `hermes_webui_ssh_dir` at a dedicated key.

Root-owned Hermes home
----------------------

The upstream entrypoint remaps its `hermeswebui` account to the owner of the
Hermes home (`WANTED_UID`). When that owner is root, the remap breaks the init.
`files/root-entrypoint.sh` wraps the upstream entrypoint. When the home is
root-owned (`HERMES_WEBUI_ROOT_HOME_MODE=1`, set from the owner the role
detects), it skips only the remap branch and runs the rest unchanged. The
container then runs as root, so the agent's home is `/root`. Otherwise the
wrapper runs the upstream entrypoint as-is. If a future image changes the
patched line, the container refuses to start instead of running with the wrong
ownership.

Named providers in the model picker
-----------------------------------

The picker may hide a named entry under `providers:` in the Hermes
`config.yaml` that uses `key_env` but has no `models:` list. Add a short list
of verified model IDs to each such entry. The picker also changes underscores
in provider keys to hyphens, and the Agent does not treat the two as the same.
Keep the original entry for existing sessions and add a hyphenated alias with
the same `api` and `key_env`, without a pinned `model` or `default_model`.
Back up `config.yaml` before editing it and leave `model.provider` and
`model.default` unchanged. After editing, redeploy with
`-e hermes_webui_force_recreate=true` so the WebUI reloads its model cache.

Layout
------

- All settings live in `templates/.env.j2`, which is templated to
  `{{ service_dir }}/.env` (mode `0600`). Values come from
  `defaults/main/main.yml` (non-secret) and `defaults/main/vault.yml`
  (secrets).
- `docker-compose.yml` reads those values through Compose interpolation
  (`${image_tag}`, `${hermes_webui_domain}`, ...). Jinja in the compose file
  only adds the workspace loop and the optional host-access blocks.
- `{{ service_dir }}` also holds `agent-source/` (copy of the Agent source),
  `state/` (WebUI sessions and settings) and `root-entrypoint.sh`.

Dependencies
------------

- `docker_setup` (Docker must be installed on the target host)
- `traefik_setup` (provides the `web_net` network and the TLS certresolver)

Example Playbook
----------------

See `playbooks/hermes-web-ui.yml`:

    - hosts: all
      become: true
      gather_facts: true
      roles:
        - hermes_webui_setup

Tags
----

- `install_hermes_webui`, `setup_hermes_webui` — run the whole role
- `preparing` — create networks and directories, copy the Agent source and
  entrypoint, template compose + env files
- `pull` — pull the Docker image
- `deploy` — start the stack and wait for `/health`
- `verify` — check from inside the container that the `hermes` CLI,
  workspaces, `/host` and the host executor work

The preflight checks (password, Hermes home, workspaces, SSH key) always run.

License
-------

MIT
