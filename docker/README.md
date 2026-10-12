# Docker learning directory

Practical Docker labs and reference material for beginners.

**Navigate:** [Installation](#installation) · [Configuration](#configuration) · [Overview](#overview)

## Installation

These instructions **document** installation; they do not install or reconfigure
Docker on your machine. Use a practice host or VM with network access to Docker's
package repository and image registries. On **Debian or Ubuntu**, check your
release and any existing Docker installation before changing packages:

```bash
. /etc/os-release
printf '%s %s (%s)\n' "$ID" "$VERSION_ID" "$VERSION_CODENAME"
dpkg --print-architecture
if command -v docker >/dev/null 2>&1; then docker version; fi
```

### Debian or Ubuntu: official APT repository

The example follows the [Docker Engine installation guide for Debian](https://docs.docker.com/engine/install/debian/)
and [Ubuntu](https://docs.docker.com/engine/install/ubuntu/). Use it only on a
**supported Debian or Ubuntu release**; the commands select the OS-specific
repository and release codename rather than assuming `bullseye` or `bookworm`.
On a derivative (for example, Linux Mint or Kali), consult the official guide
and select the corresponding supported base release manually. If Docker or
containerd already runs workloads, **do not remove conflicting packages or
replace its repository as a routine setup step**: review Docker's conflict list,
back up host configuration and workloads, and plan a migration first. In
particular, replacing `docker.io`, `containerd`, or `runc` can disrupt services.

1. Install only the APT prerequisites and register Docker's official signing key:

   ```bash
   sudo apt-get update
   sudo apt-get install -y ca-certificates curl
   sudo install -m 0755 -d /etc/apt/keyrings
   . /etc/os-release
   case "$ID" in debian|ubuntu) ;; *) printf 'Use the Docker guide for %s\n' "$ID" >&2; exit 1 ;; esac
   if [ -e /etc/apt/keyrings/docker.asc ]; then
     printf 'Existing Docker key found; verify it before reusing it.\n'
   else
     sudo curl -fsSL "https://download.docker.com/linux/$ID/gpg" -o /etc/apt/keyrings/docker.asc
     sudo chmod a+r /etc/apt/keyrings/docker.asc
   fi
   ```

2. Add the APT source for **your** distribution and inspect it before updating.
   If `/etc/apt/sources.list.d/docker.sources` already exists, review/merge it
   instead of overwriting it:

   ```bash
   . /etc/os-release
   case "$ID" in debian|ubuntu) ;; *) printf 'Unsupported example: %s\n' "$ID" >&2; exit 1 ;; esac
   CODENAME="${UBUNTU_CODENAME:-$VERSION_CODENAME}"
   if [ -e /etc/apt/sources.list.d/docker.sources ]; then
     printf 'Existing Docker APT source found; inspect and merge it manually.\n' >&2
   else
     printf 'Types: deb\nURIs: https://download.docker.com/linux/%s\nSuites: %s\nComponents: stable\nArchitectures: %s\nSigned-By: /etc/apt/keyrings/docker.asc\n' \
       "$ID" "$CODENAME" "$(dpkg --print-architecture)" | sudo tee /etc/apt/sources.list.d/docker.sources
   fi
   sudo apt-get update
   ```

   This writes a system APT source. Confirm your codename is supported before
   running it. Use the official key/repository by default; a third-party mirror
   requires separate trust and availability checks, especially behind a proxy.

3. Install Engine, CLI, containerd, Buildx, and the **Compose v2 plugin**:

   ```bash
   sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
   sudo systemctl status docker --no-pager
   ```

   On a normal systemd install, Docker should start automatically. If it has not
   started, diagnose the service before using `sudo systemctl start docker`.
   Do not restart an existing daemon casually: running containers are affected.

4. Verify the daemon and plugins, then run the disposable test image:

   ```bash
   sudo docker version
   sudo docker compose version
   sudo docker buildx version
   sudo docker run --rm hello-world
   ```

   `docker version` should show **Client and Server**; `hello-world` downloads an
   image, prints a confirmation, and exits. If the daemon is unreachable, check
   `sudo systemctl status docker --no-pager` before changing permissions.
   `docker-compose` (hyphen) is the old standalone command; these scenarios use
   `docker compose` (space).

**Windows/macOS:** Install [Docker Desktop](https://docs.docker.com/desktop/),
start it, then check `docker version`, `docker compose version`, and
`docker run --rm hello-world` in your terminal. The Linux APT and systemd steps
above do not apply. If you need Docker on another Linux distribution, follow
[its official Engine guide](https://docs.docker.com/engine/install/).

### Optional tools and Linux user access

The reference includes many administration tools; they are not all Docker
prerequisites. For a small learning toolkit, optionally install:

```bash
sudo apt-get install -y git vim bash-completion jq iproute2 dnsutils
```

Until configured otherwise, prefix Docker commands with `sudo`. For convenient
access, run the following **as the intended non-root user**, not from a root
shell:

```bash
getent group docker || sudo groupadd docker
sudo usermod -aG docker "$USER"
# Log out and back in, then verify without sudo:
docker version
```

**The `docker` group grants root-level access through the daemon.** Add only
trusted users; never make the socket world-writable. If that access is unsuitable,
consider [rootless Docker](https://docs.docker.com/engine/security/rootless/).
The [post-installation guide](https://docs.docker.com/engine/install/linux-postinstall/)
covers both permissions and service startup. Commands in the labs assume your
user has authorized Docker access; otherwise use `sudo`.

If downloading the APT key or packages fails (for example, with HTTP 403), check
network policy and approved proxy access first. Shell/`curl`, APT, and the Docker
daemon have separate proxy settings: configuring Docker alone does not fix APT
or key downloads. Do not bypass TLS verification or trust an unknown mirror.

## Configuration

The [configuration reference](https://github.com/AhmadRafiee/DevOps_Certification/tree/main/docker/configuration)
covers daemon options, networking, logging/plugins, and advanced networks. For
these local labs, Docker's defaults normally suffice. On a Linux Engine host,
`/etc/docker/daemon.json` is optional: **inspect and back up an existing file,
then merge only settings you need**. Never replace it blindly or configure an
unauthenticated TCP API listener. A daemon restart can interrupt workloads;
validate proposed settings and schedule the restart on shared hosts. Docker
Desktop settings are managed in the application, not through the host's
`/etc/docker/daemon.json`.

- **Registry access:** If pulls require an organizational HTTP proxy, consult
  [daemon proxy configuration](https://docs.docker.com/engine/daemon/proxy/).
  Configure the daemon separately from application containers; use Docker
  Desktop's proxy settings on Desktop. Do not publish proxy credentials in Git.
  Add registry mirrors only when you trust and have tested them.
- **Logs:** `docker info --format '{{.LoggingDriver}}'` shows the current driver.
  Docker's [logging guide](https://docs.docker.com/engine/logging/configure/)
  explains the rotating `local` driver or limits for `json-file`. A changed
  default affects newly created containers, not existing ones.
- **Networks and ports:** `docker network ls` lists the host's networks; the
  Compose scenarios create their own networks. Publish lab ports on loopback
  (`-p 127.0.0.1:5000:5000`), not all interfaces. Do not copy legacy bridge,
  macvlan, overlay, or plugin examples into a live host without understanding
  routing, firewall, and privilege effects. Docker-published ports can bypass
  some host firewall policies.
- **Build contexts and data:** Build within the chosen Dockerfile lab so `.` is
  its context. No shared `.env` or daemon configuration is required for those
  labs. The Compose apps have separate setup instructions and persistent data;
  do not use `docker compose down -v` for ordinary cleanup.

### Daemon settings: one small example

For a Linux Engine host, this optional `daemon.json` example limits logs.
**Merge these keys into existing JSON; do not paste over the whole file.** Add
`registry-mirrors` only if you have a trusted, working mirror, and omit proxy
settings unless your network needs them:

```json
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "3" }
}
```

For a required proxy, merge this **separate fragment** into the same JSON object
and replace the example address with your approved proxy:

```json
{
  "proxies": {
    "http-proxy": "http://proxy.example.com:3128",
    "https-proxy": "http://proxy.example.com:3128",
    "no-proxy": "localhost,127.0.0.1,::1,.example.internal"
  }
}
```

Do not concatenate two JSON objects. An alternative is a systemd drop-in via
`sudo systemctl edit docker`, setting `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY`
under `[Service]`; choose one proxy method rather than conflicting settings.
Do not replace the service's `ExecStart` merely to add a proxy or mirror.
After editing, check settings **before** a planned restart:

```bash
sudo dockerd --validate --config-file=/etc/docker/daemon.json
sudo systemctl cat docker
# Only after successful validation and an approved maintenance window:
# sudo systemctl daemon-reload  # Needed if a systemd drop-in changed
# sudo systemctl restart docker
sudo systemctl status docker --no-pager
sudo docker info
```

`--validate` checks daemon options, not registry/proxy reachability or conflicts
with every systemd flag. If a change fails, restore the previous configuration
and inspect `sudo journalctl -u docker -n 50 --no-pager`. Changing network pools,
`data-root`, or storage drivers requires a separate migration plan. Volume or
logging plugins are advanced, privileged extensions, not requirements for these
labs; review their permissions and documentation before installing them.

Optional host-side checks use Python 3, Node.js 24, .NET 10 SDK, or GCC as noted
in individual labs; those tools are not needed on the host for Docker builds.

## Overview

From the **repository root**, try the first example after Docker is running:

```bash
cd docker/dockerfiles/hello-python
docker build -t learn-hello-python .
docker run --rm learn-hello-python
```

Expected output: `Hello from a Docker container!`. `--rm` removes the test
container, not its image or source files. Each lab has its own README with exact
build, run, test, and stop instructions.

| Path | Learning material |
| --- | --- |
| [dockerfiles/](dockerfiles/README.md) | Eight single-image labs: Hello Python, Flask, static HTML/CSS/JS, `ARG`/`ENV`, `ENTRYPOINT`/`CMD`, multi-stage C, Node.js, and .NET. |
| [scenario/](scenario/README.md) | Four application scenarios: [WordPress + Nginx](scenario/wordpress-nginx/README.md), [WordPress + Traefik](scenario/wordpress-traefik/README.md), [Todo](scenario/todo-app/README.md), and [Voting](scenario/voting-app/README.md). |
| [compose/](compose/README.md) | Three standalone, commented Compose YAML examples: [WordPress](compose/wordpress/README.md), [Traefik](compose/traefik/README.md), and [Portainer](compose/portainer/README.md). |
| [dockerfile-best-practices.md](dockerfile-best-practices.md) | Dockerfile instructions, image size, caching, security, and conventions. |
| [swarm/](swarm/README.md) | Swarm concepts, manager/worker setup, and a [Voting App stack](swarm/voting-app/README.md) with multi-node operations. |

Use the Dockerfile labs first, then the standalone Compose examples and
multi-container application scenarios. The scenario WordPress labs generate local
secret files; the standalone WordPress Compose example requires local password
variables. Todo and Voting retain persistent database volumes. Read each
example's setup and stop instructions before starting it,
and do not use `docker compose down -v` as routine cleanup. These are learning
examples, not production deployments. Host-side tests do not prove that image
builds, container networking, or persistence work on your machine.

**References:** [Installation example](https://github.com/AhmadRafiee/DevOps_Certification/tree/main/docker/installation) · [Configuration examples](https://github.com/AhmadRafiee/DevOps_Certification/tree/main/docker/configuration). The install commands above follow current Docker documentation rather than copying hard-coded release names, untrusted mirrors, or exposed daemon sockets.
