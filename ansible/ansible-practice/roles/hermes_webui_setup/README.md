hermes_webui_setup
==================

Deploy [Hermes WebUI](https://github.com/nesquena/hermes-webui) (web interface for
Hermes Agent) with Docker Compose via Ansible, reverse-proxied through Traefik.
The container binds only to the internal `web_net` network and is reached through
Traefik labels — no host port is published.

The [official published image](https://github.com/nesquena/hermes-webui/pkgs/container/hermes-webui)
is used **unmodified**. This role builds nothing.

The point of the role
---------------------

The WebUI runs the Hermes Agent *inside a container*. That single fact drives
almost every decision here, and it is the cause of the failure this role exists
to prevent:

> The path /root/mygit and the hermes CLI are absent. This WebUI session is
> running in an isolated container that lacks your repositories, Ansible, and
> Hermes agent.

The agent was not confused — it was describing its own filesystem accurately.
A container that is `healthy` is not the same thing as an agent that can do the
job. So the role explicitly provides three things, and then **verifies all
three after deploying**:

| The agent needs | How it gets it |
|---|---|
| Your repositories | `hermes_webui_workspaces`, bind-mounted at their **host paths** |
| The rest of the server | `hermes_webui_host_root_*` — the whole host filesystem at `/host` |
| The `hermes` CLI | Already in the image at `/app/venv/bin`; put on `PATH` via `hermes_webui_container_path` |
| Ansible | Not in the image. The agent SSHes back to the host and runs it there — see below |

Three ways to reach the server
------------------------------

They are not redundant; each solves a different problem.

1. **Path-identical workspaces** — `hermes_webui_workspaces`, default `/root`.
   A path typed in the UI resolves to the same file the host sees, so
   `/root/mygit/...` just works. Use this for the directories you actually
   work in.

2. **`/host` — the whole filesystem.** `hermes_webui_host_root_enabled` mounts
   the host's `/` read-write at `/host`, so the host's `/etc/nginx` is
   `/host/etc/nginx` and `/var/log` is `/host/var/log`. Paths are prefixed,
   which is the price of not shadowing the container's own OS. The prefix is
   in the container environment as `HERMES_HOST_FS`.

3. **The host executor** — for *doing* rather than reading. `systemctl`,
   `docker`, `apt` and `ansible` have to run on the host, not in the
   container. See the next section.

### Why not just mount everything at its real path?

Because the container needs its own `/etc`, `/var`, `/usr`, `/bin`, `/lib`,
`/sbin`, `/proc`, `/sys`, `/dev`, `/run` and `/tmp` to function — mounting the
host's over them replaces the OS the WebUI is running on, and the failure looks
like a corrupt image. `hermes_webui_workspace_forbidden_paths` makes preflight
reject that with an explanation rather than letting you find out at runtime.

`/root` is safe to shadow, and is the default, because the container's own
`/root` holds nothing but a uv cache. The read-only `/root/.ssh` mount nests
on top of the read-write `/root`, so the keys stay read-only either way.

Running Ansible from the WebUI
------------------------------

The image ships `git`, `ssh`, `rsync` and `uv`, but no Ansible. Rather than
modify the image, the agent runs playbooks **on the host** — the machine that
already has `ansible-core`, the collections, the inventory, the vault password
file and the SSH keys.

`hermes_webui_host_executor_enabled` publishes the Docker host under
`host.docker.internal` via `host-gateway`, and the container environment
carries the exact invocation:

```sh
$HERMES_HOST_EXECUTOR_SSH "$HERMES_HOST_EXECUTOR_ENV bash -lc 'cd /root/mygit/Devops-Certification/ansible/ansible-practice && ansible-playbook playbooks/hermes-web-ui.yml'"
```

which expands to:

```sh
ssh -p 3031 -i ~/.ssh/id_rsa -o BatchMode=yes -o StrictHostKeyChecking=no \
    -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR root@host.docker.internal \
    "LC_ALL=C.UTF-8 LANG=C.UTF-8 bash -lc '...'"
```

Two details are load-bearing, and both are baked into
`HERMES_HOST_EXECUTOR_ENV` / `HERMES_HOST_EXECUTOR_SSH` so nothing has to
rediscover them:

- **`LC_ALL` / `LANG` are mandatory.** A non-interactive `ssh host command`
  session inherits no locale, and Ansible aborts with
  `Ansible requires the locale encoding to be UTF-8; Detected None`.
- **`UserKnownHostsFile=/dev/null`.** `~/.ssh` is mounted read-only, so `ssh`
  cannot record the host key and would warn on every single invocation.

> **Security — read this before widening access.** With the defaults, an
> authenticated WebUI session is equivalent to root on this machine: it can
> read and write the entire filesystem at `/host`, holds `/root` read-write
> (including `~/.claude.json`, `.gnupg`, `.kube`, `.env` and every other
> credential kept there), and can SSH as root to this host and anywhere else
> those keys are authorised. The service is published on the public internet
> behind a single password.
>
> That is the access the role was asked for, and it is a deliberate choice, not
> an accident — but size the protection to match it:
>
> - Keep `vault_hermes_webui_password` strong; preflight enforces
>   `hermes_webui_password_min_length`.
> - Put the service behind Authelia (`authelia_setup`) if it is reachable from
>   the internet.
> - Pin `hermes_webui_image_digest`. An unpinned tag means a future `docker
>   pull` can change the code that holds all of this.
> - To narrow it: `hermes_webui_host_root_read_only: true` (read the server,
>   write only the workspaces), `hermes_webui_ssh_enabled: false` (no SSH
>   capability), or point `hermes_webui_ssh_dir` at a dedicated, narrowly
>   authorised key directory.

Requirements
------------

- Docker and Docker Compose v2 on the target host (`docker_setup` role)
- The `community.docker` collection (see `requirements.yml`)
- A Traefik reverse proxy exposing `web_net` (`traefik_setup` role)
- `main_domain` and `project_dir` in `inventory/group_vars/all/general.yml`
- An existing Hermes CLI installation on the host: `/root/.hermes/config.yaml`,
  `/root/.hermes/state.db` and `/usr/local/lib/hermes-agent`. The role asserts
  these rather than creating them, because an auto-created empty home would
  quietly start the WebUI with no configuration.
- `rsync` on the target host — installed by the role if missing

Usage
-----

Membership is explicit; the playbook targets the `hermes_webui` group rather
than `all`, so a public, key-bearing agent is never fanned out across the fleet
by accident.

```yaml
# inventory/hosts.yml
all:
  children:
    hermes_webui:
      hosts:
        hetzner-cactus: {}
```

```sh
ansible-playbook playbooks/hermes-web-ui.yml
```

Task files and tags
-------------------

| File | Tags | What it does |
|---|---|---|
| `preflight.yml` | `preparing`, `hermes_webui_preflight` | Asserts every precondition before anything is changed |
| `deploy.yml` | `deploy`, `hermes_webui_deploy` | Networks, directories, Agent source export, templates, Compose up |
| `verify.yml` | `verify`, `hermes_webui_verify` | Proves the agent can actually reach its workspaces, CLI and Ansible |

`install_hermes_webui` and `setup_hermes_webui` run all three.

Role Variables
--------------

See `defaults/main/main.yml` for the full set; `vars/main/main.yml` holds the
image-fixed container paths, which are not meant to be overridden.

### Image

| Variable | Default | Description |
|---|---|---|
| `hermes_webui_image_repository` | `ghcr.io/nesquena/hermes-webui` | Published image |
| `hermes_webui_image_tag` | `latest` | Tag to track; version tags such as `0.50.43` are also published |
| `hermes_webui_image_digest` | `""` | Digest pin. Empty tracks a mutable tag, and preflight warns |

Pin the digest in production. `latest` is a distinct build from the version
tags, so pin whichever you actually tested:

```sh
docker image inspect ghcr.io/nesquena/hermes-webui:latest --format '{{index .RepoDigests 0}}'
```

### Workspaces and host access

| Variable | Default | Description |
|---|---|---|
| `hermes_webui_workspaces` | `[{path: /root}]` | Host dirs mounted at the **same absolute path** in the container. String or `{path, read_only}` |
| `hermes_webui_workspaces_must_exist` | `true` | Fail if a declared workspace is missing, instead of letting Docker mount an empty dir over it |
| `hermes_webui_workspace_forbidden_paths` | `/etc`, `/var`, `/usr`, … | Paths preflight refuses as workspaces, because shadowing them breaks the container |
| `hermes_webui_host_root_enabled` | `true` | Mount the whole host filesystem, so the agent can reach the entire server |
| `hermes_webui_host_root_path` | `/` | What to mount |
| `hermes_webui_host_root_mount_point` | `/host` | Where it appears in the container; exported as `HERMES_HOST_FS` |
| `hermes_webui_host_root_read_only` | `false` | Set `true` to let the agent read the whole server but change only its workspaces |
| `hermes_webui_host_executor_enabled` | `true` | Publish the host as `host.docker.internal` so the agent can run Ansible there |
| `hermes_webui_host_alias` | `host.docker.internal` | Name the host is published under |
| `hermes_webui_host_ssh_port` | `{{ ansible_port \| default(22) }}` | Host sshd port as reachable from the container |
| `hermes_webui_host_executor_env` | `LC_ALL`/`LANG` = `C.UTF-8` | Locale every remote command must carry |
| `hermes_webui_ssh_enabled` | `true` | Mount SSH material read-only |
| `hermes_webui_ssh_dir` | `/root/.ssh` | Host SSH directory, mounted at the runtime account's `~/.ssh` |
| `hermes_webui_ssh_private_key_name` | `id_rsa` | Key the executor uses |

### Hermes data

| Variable | Default | Description |
|---|---|---|
| `hermes_webui_home_dir` | `/root/.hermes` | Existing Hermes CLI home, mounted as the container's `~/.hermes` |
| `hermes_webui_agent_dir` | `/usr/local/lib/hermes-agent` | Official installer source directory |
| `hermes_webui_agent_export_dir` | `{{ service_dir }}/agent-source` | Filtered source export, mounted read-only at `/opt/hermes` |
| `hermes_webui_state_dir` | `{{ service_dir }}/state` | Separate writable WebUI sessions/settings directory |
| `hermes_webui_allow_root_runtime` | `true` | Permit the guarded root-owned-home entrypoint |
| `hermes_webui_skip_onboarding` | `1` | Use the existing `config.yaml` without onboarding |
| `hermes_webui_skip_chmod` | `1` | Prevent WebUI startup from rewriting CLI credential modes |

### Runtime, networking and credentials

| Variable | Default | Description |
|---|---|---|
| `restart_policy` | `unless-stopped` | Container restart policy |
| `service_dir` | `{{ project_dir }}/hermes-webui` | Service directory on the remote host |
| `hermes_webui_container_path` | `…:/app/venv/bin` | `PATH` in the container, so `hermes` resolves |
| `hermes_webui_memory_limit` | `4g` | Memory ceiling — an unbounded agent can take the host down |
| `hermes_webui_cpu_limit` | `2.0` | CPU ceiling |
| `hermes_webui_log_max_size` / `_file` | `20m` / `5` | Log rotation |
| `hermes_webui_domain` | `hermes.{{ main_domain }}` | Public domain served by Traefik |
| `hermes_webui_port` | `8787` | Port the app listens on inside the container |
| `hermes_webui_password` | _(vaulted)_ | Login password; resolves to `vault_hermes_webui_password` |
| `hermes_webui_password_min_length` | `16` | Preflight refuses anything shorter |

### Verification

| Variable | Default | Description |
|---|---|---|
| `hermes_webui_verify_agent_toolchain` | `true` | Assert workspaces, `hermes`, the SSH key and the host executor all work |
| `hermes_webui_verify_public_url` | `false` | Also probe `https://…/health`. Off because a failure means DNS/ACME/Traefik, not the service |
| `hermes_webui_health_retries` / `_delay` | `30` / `10` | Container healthcheck wait |

The root-owned-home entrypoint
------------------------------

The upstream init phase remaps the `hermeswebui` account to `WANTED_UID` and
recursively `chown`s its home. When the existing Hermes home is root-owned,
remapping to UID 0 creates a second root account and re-enters the root init
branch after `su`.

`templates/root-entrypoint.sh.j2` patches out **only** that ownership-remap
branch and runs the rest of the upstream entrypoint unchanged, so path
validation, venv preparation and Agent source staging still happen. The patch
asserts its marker matches exactly once and refuses to start otherwise — a
future upstream image that restructures its init fails loudly instead of
silently running with the wrong ownership semantics.

Layout
------

- Scalar settings live in `templates/.env.j2` → `{{ service_dir }}/.env`
  (mode `0600`, rendered with `no_log`), and reach Compose through
  `${…}` interpolation — the same split used by `docmost_setup`.
- Structure and the mount list come from `templates/docker-compose.yml.j2`,
  so secrets never enter the Compose file.
- The rendered project is validated with `docker compose config --quiet`
  **before** deploy, so a bad template cannot take the running service down.
- A container recreate is forced only when something that matters actually
  changed: the Agent source export, the image, the entrypoint, `.env`, or the
  Compose file. A no-op run is `changed=0`.

Traefik
-------

`traefik_setup` configures the HTTP→HTTPS redirect globally at the entrypoint
(`--entryPoints.web.http.redirections.*`), so the `http-hermes-webui` router
here only needs to exist on the `web` entrypoint — matching the other roles in
this repo. TLS is issued by the `myproduction` resolver.
