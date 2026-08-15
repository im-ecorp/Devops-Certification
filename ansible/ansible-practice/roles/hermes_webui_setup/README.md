Role Name
=========

Deploy [Hermes WebUI](https://github.com/nesquena/hermes-webui) (web interface for
Hermes Agent) with Docker Compose via Ansible, reverse-proxied through Traefik.
The container binds only to the internal `web_net` network and is reached through
Traefik labels — no host port is published.

Requirements
------------

- Docker and Docker Compose v2 installed on the target host (`docker_setup` role)
- The `community.docker` Ansible collection (see `requirements.yml`)
- A Traefik reverse proxy exposing the `web_net` network
  (`traefik_setup` role)
- `main_domain` and `project_dir` set in `inventory/group_vars/all/general.yml`

Role Variables
--------------

See `defaults/main/main.yml` for all configurable variables.

| Variable | Default | Description |
|---|---|---|
| `hermes_webui_image_tag` | `latest` | Hermes WebUI Docker image tag |
| `restart_policy` | `unless-stopped` | Container restart policy |
| `service_dir` | `{{ project_dir }}/hermes-webui` | Service directory on the remote host |
| `hermes_webui_home_dir` | `/root/.hermes` | Existing Hermes CLI home mounted as `~/.hermes` |
| `hermes_webui_agent_dir` | `/usr/local/lib/hermes-agent` | Official installer source directory |
| `hermes_webui_agent_export_dir` | `{{ service_dir }}/agent-source` | Filtered source export mounted read-only at `/opt/hermes` |
| `hermes_webui_state_dir` | `{{ service_dir }}/state` | Separate writable WebUI sessions/settings directory |
| `hermes_webui_allow_root_runtime` | `true` | Permit the guarded root-owned-home entrypoint |
| `hermes_webui_domain` | `hermes.{{ main_domain }}` | Public domain served by Traefik |
| `hermes_webui_url` | `https://{{ hermes_webui_domain }}` | Public base URL of the WebUI |
| `hermes_webui_port` | `8787` | Port the app listens on inside the container |
| `hermes_webui_secure` | `1` | Force the Secure cookie flag (HTTPS via Traefik) |
| `hermes_webui_allowed_origins` | `https://hermes.{{ main_domain }}` | Allowed public origin for requests |
| `hermes_webui_trust_forwarded_host` | `1` | Trust the forwarded Host header from Traefik |
| `hermes_webui_trust_forwarded_for` | `1` | Trust the X-Forwarded-For header from Traefik |
| `hermes_webui_trust_forwarded_proto` | `1` | Trust the X-Forwarded-Proto header from Traefik |
| `hermes_webui_skip_onboarding` | `1` | Use the existing `config.yaml` without onboarding |
| `hermes_webui_skip_chmod` | `1` | Prevent WebUI startup from rewriting CLI credential modes |

Layout
------

- All configuration lives in `templates/.env.j2`, templated to
  `{{ service_dir }}/.env` (mode `0600`). Values come from
  `defaults/main/main.yml` (non-secret) and `defaults/main/vault.yml`
  (secrets).
- `docker-compose.yml` reads those values through Compose interpolation
  (`${hermes_webui_password}`, `${hermes_webui_domain}`, ...) — the same split
  used by `docmost_setup`.
- The `hermes-webui` service is attached only to the external `web_net`
  network. Traefik routes `https://hermes.<main_domain>` to the container port
  `8787` through labels; no host port is published.
- Existing Hermes data is mounted read-write because normal WebUI chat and
  session operations use the same Agent state as the CLI. The role does not
  create, migrate, `chown`, or `chmod` that directory.
- WebUI-owned JSON sessions, settings, projects, and attachments live in the
  separate `{{ service_dir }}/state` mount rather than
  `/root/.hermes/webui`.
- The role uses `rsync` to create a filtered export of the installed Agent
  source, excluding its host virtualenv, Node modules, Git metadata, bytecode,
  and build artifacts. The export is mounted read-only at `/opt/hermes`. This
  gives the container the exact Agent implementation used by the host without
  copying roughly 2 GB of unrelated host artifacts at container startup.
- `HERMES_WEBUI_AGENT_DIR=/opt/hermes` explicitly selects that read-only
  source. This is required because WebUI's runtime discovery does not infer the
  Agent directory from the dependency installation step.

Secrets (vault)
---------------

Secrets live in `defaults/main/vault.yml`, encrypted with `ansible-vault`:

    ansible-vault edit defaults/main/vault.yml

| Variable | Description |
|---|---|
| `hermes_webui_password` | Password required to log in to the WebUI. Mandatory because the service is publicly reachable through Traefik. |

Existing Hermes home safety
---------------------------

This role is intentionally for an existing official Hermes installation. It
fails before deployment unless all of these paths exist:

- `/root/.hermes/config.yaml`
- `/root/.hermes/state.db`
- `/usr/local/lib/hermes-agent/pyproject.toml`
- `/usr/local/lib/hermes-agent/run_agent.py`

For a root-owned home, the upstream image's normal UID-remapping phase cannot
be used safely: it recursively changes ownership and attempts to turn its
runtime account into UID 0. The role mounts a small guarded entrypoint that
skips only that phase, validates the upstream marker before doing so, and then
runs the rest of the official startup script. `HERMES_SKIP_CHMOD=1` prevents
the WebUI permission fixer from changing `.env`, `auth.json`, and other CLI
credential modes.

The existing host gateway may remain running. The WebUI container does not
start a second gateway daemon; it runs WebUI chat turns in-process and reads
CLI sessions through Hermes' SQLite state store. Do not separately add a
`hermes gateway run` command to this Compose service.

Back up `/root/.hermes` before the first deployment. A backup protects against
application-level changes made intentionally from the WebUI, but it is not a
substitute for the ownership and path preflight checks above.

The Agent home remains read-write by design. This is required for full WebUI
chat, resume, profile, memory, and task functionality. If a strictly read-only
viewer is required, do not deploy this role against the live home; use a
consistent SQLite backup in an isolated Hermes home instead.

Dependencies
------------

- `docker_setup` (Docker must be installed on the target host)
- `traefik_setup` (provides the `web_net` network and the TLS certresolver)

Example Playbook
----------------

See `playbooks/hermes.yml`:

    - hosts: all
      become: true
      gather_facts: true
      roles:
        - hermes_webui_setup

Tags
----

- `install_hermes_webui`, `setup_hermes_webui` — run the whole role
- `preparing` — create networks, service directory, data dirs, compose + env files
- `pull` — pull the Docker image
- `deploy` — start the stack and wait for Hermes WebUI to answer health checks

License
-------

MIT

Author Information
------------------

https://github.com/amati-sh
