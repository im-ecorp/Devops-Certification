# Podman

Podman runs OCI containers and images with Docker-like commands, without a permanent central daemon for local Linux use. **Rootless** mode runs containers under your normal user; do not use `sudo podman` for this lab. Rootful and rootless containers have separate storage and are not listed together.

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

## 2. Check rootless configuration

In a login session as your normal, non-root user:

```bash
id -u # Must not be 0 for rootless operation.
podman --version
awk -F: -v u="$(id -un)" '$1 == u {print}' /etc/subuid /etc/subgid
podman info --format '{{.Host.Security.Rootless}}' # Expected: true.
```

Your username should have a non-overlapping subordinate UID/GID range in **both** `/etc/subuid` and `/etc/subgid` (typically at least 65,536 IDs). Installers often configure it automatically. If entries are missing, ask the administrator to allocate unused ranges; do not copy a fixed range that may overlap another account. After changing mappings, log out/in and follow the installed version's `podman system migrate` guidance, which may stop that user's containers.

Defaults are enough for this example. Use fully qualified images such as `docker.io/library/nginx:1.28-alpine` to avoid short-name registry prompts. Optional user configuration belongs in `~/.config/containers/containers.conf` and `~/.config/containers/registries.conf`; inspect and merge existing settings rather than replacing them. Rootless image/container data normally lives under `~/.local/share/containers/storage` (XDG overrides may change this).

Use an unprivileged host port such as `8090`; there is no need to lower host security settings to bind port 80. Podman can coexist with Docker, but their storage and containers are separate and published ports can conflict. Rootless mode reduces host privileges; it does not make untrusted images safe.

## 3. Run a service

Follow the [Nginx example](nginx/README.md): pull an image, run it locally, test HTTP, inspect logs, and stop/start the container. It needs no Dockerfile, Compose provider, external config, or custom application files.

For automatic startup after reboot, use a user-systemd **Quadlet** on supported Podman versions; this manual lab does not configure boot persistence. `podman compose` delegates to an external Compose provider and is not needed here.

**References:** [Installation](https://podman.io/docs/installation) · [Rootless setup](https://github.com/containers/podman/blob/main/docs/tutorials/rootless_tutorial.md) · [Podman run](https://docs.podman.io/en/latest/markdown/podman-run.1.html).
