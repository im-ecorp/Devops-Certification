# Podman

Podman runs OCI containers and images with Docker-like commands, without a permanent central daemon for local Linux use. **Rootless** mode runs containers under your normal user; do not use `sudo podman` for this lab. Rootful and rootless containers have separate storage and are not listed together.

## Podman vs Docker

| Area | Podman | Docker |
| --- | --- | --- |
| Architecture on Linux | Local CLI does not need a central daemon; an API service is optional | CLI normally talks to the Docker Engine daemon |
| Privileges | Rootless use is a first-class workflow; rootful use is also available | Engine is commonly rootful; Docker also supports rootless mode |
| Images and builds | OCI/Docker images; `podman build` accepts Dockerfiles and Containerfiles | OCI/Docker images; Dockerfile builds with a mature BuildKit ecosystem |
| Everyday commands | Similar `run`, `ps`, `logs`, `exec`, and `stop` commands | Comparable commands, but flags and behavior are not identical |
| Multiple containers | Native pods; optional external Compose provider | Integrated Docker Compose v2 plugin; Swarm for cluster services |
| Linux service startup | Quadlet integrates containers with systemd | Engine service plus container restart policies |
| macOS/Windows | Linux VM managed with `podman machine` | Docker Desktop provides a Linux VM for Linux containers |
| API/tool compatibility | Optional Docker-compatible API, not full behavioral parity | Native Docker API and broader Docker-tool integration |

Choose Podman for a rootless Linux/systemd workflow; choose Docker when your tooling depends on Docker-specific behavior. Both can run the same Nginx image. Neither is a security sandbox for arbitrary untrusted code. Installing Podman does not transfer Docker's existing containers or volumes.

## 1. Install

Use one option for your distribution on a Linux practice host:

```bash
# Debian 12+/Ubuntu 24.04+:
sudo apt-get update
sudo apt-get install -y podman uidmap passt slirp4netns fuse-overlayfs curl
```

```bash
# Fedora:
sudo dnf install -y podman shadow-utils passt fuse-overlayfs curl
```

Packages provide the runtime and rootless helpers. Current Podman uses `pasta` from `passt` for rootless networking; older packaged versions may use `slirp4netns`. No Docker daemon or `systemctl enable podman` is required for these CLI commands. Installation changes the host; these commands are instructions, not actions performed by this repository.

On macOS/Windows, install Podman using the [official installer](https://podman.io/docs/installation), then run `podman machine init` and `podman machine start` once to create/start its Linux VM. The example below targets native Linux; do not assume its filesystem/network behavior is identical through a VM.

## 2. Configure rootless Podman

**User mappings.** In a login session as your normal, non-root user:

```bash
id -u # Must not be 0 for rootless operation.
podman --version
awk -F: -v u="$(id -un)" '$1 == u {print}' /etc/subuid /etc/subgid
podman info --format '{{.Host.Security.Rootless}}' # Expected: true.
```

Your username should have a non-overlapping subordinate UID/GID range in **both** `/etc/subuid` and `/etc/subgid` (typically at least 65,536 IDs). Installers often configure it automatically. If entries are missing, ask the administrator to allocate unused ranges; do not copy a fixed range that may overlap another account. After changing mappings, log out/in and follow the installed version's `podman system migrate` guidance, which may stop that user's containers. Do not run migration against active work without checking its impact.

**Configuration files.** Defaults work for the Nginx example; do not create files merely to get started. Podman reads system defaults and user overrides. Inspect existing files before editing, and merge rather than replacing them:

| Purpose | System location | Rootless user location |
| --- | --- | --- |
| Container defaults (TOML) | `/etc/containers/containers.conf` | `~/.config/containers/containers.conf` |
| Registry search/mirrors (TOML) | `/etc/containers/registries.conf` | `~/.config/containers/registries.conf` |
| Image storage settings (TOML) | `/etc/containers/storage.conf` | `~/.config/containers/storage.conf` |

These paths assume the default XDG configuration directory. `containers.conf` layers vendor, system, and user settings; registry/storage user files can replace the system configuration rather than merge every setting. Check `man containers.conf`, `man containers-registries.conf`, and `man containers-storage.conf` for your installed version before introducing overrides.

For example, **only if you want to limit new containers' file-based logs**, merge this into the existing user `containers.conf` (do not add a second `[containers]` table):

```toml
[containers]
log_size_max = 10485760 # 10 MiB; affects new containers, not old logs.
```

Use `podman info` and `podman info --debug` to inspect the effective runtime, storage, and networking; `podman logs podman-nginx` checks the example container's logs. `log_size_max` is relevant for file-based container logging; on hosts using the journal, journal retention is configured through systemd instead. There is no need to change the network backend or storage driver for this lab; changing either on a host with existing containers may disrupt them.

**Images and registries.** Prefer fully qualified names such as `docker.io/library/nginx:1.28-alpine` so the pull source is unambiguous. `registries.conf` controls short-name search, blocking and mirrors; it is not a login file. TLS verification is on by default—do not mark a registry `insecure` to bypass certificate problems. For a private registry, use `podman login REGISTRY_HOST` interactively; credentials normally go into `$XDG_RUNTIME_DIR/containers/auth.json` on Linux and may not survive reboot. Review its permissions and use a properly protected persistent auth file only if your workflow requires one. Never commit registry credentials.

**Storage, networks, and ports.** Rootless image/container data normally lives under `~/.local/share/containers/storage` (XDG overrides may change this); check the actual paths with `podman info`. Volumes are separate from Docker's, and changing storage paths does not migrate existing data. Rootless networking commonly uses `pasta` from `passt`; distribution/version defaults may differ. Bind the example to `127.0.0.1:8090:80`: the host port is unprivileged and local-only, while port 80 is inside the container. Do not lower host port security settings to bind a rootless container to host port 80. Docker and Podman can coexist, but their published host ports can conflict.

**Optional API and boot startup.** Ordinary `podman run` needs no service or API socket. If a trusted Docker-API client requires the rootless Podman socket on a Linux systemd host, inspect the unit first, then use `systemctl --user start podman.socket`; its socket lives at `$XDG_RUNTIME_DIR/podman/podman.sock`. Socket access gives the caller full control of your Podman containers as your user: do not expose it over TCP or mount it into untrusted containers. For containers that should start after reboot, use a user-systemd Quadlet; keeping user services alive without an interactive login requires an administrator-approved `loginctl enable-linger USERNAME`. Neither the API socket nor lingering is required for this lab.

Rootless mode reduces host privileges; it does not make untrusted images safe.

## 3. Run a service

Follow the [Nginx example](nginx/README.md): pull an image, run it locally, test HTTP, inspect logs, and stop/start the container. It needs no Dockerfile, Compose provider, external config, or custom application files.

For automatic startup after reboot, use a user-systemd **Quadlet** on supported Podman versions; this manual lab does not configure boot persistence. `podman compose` delegates to an external Compose provider and is not needed here.

**References:** [Installation](https://podman.io/docs/installation) · [Rootless setup](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md) · [Podman run](https://docs.podman.io/en/latest/markdown/podman-run.1.html).
