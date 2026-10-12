# Docker learning directory

Practical Docker labs and reference material for beginners.

## Installation

1. Install Docker for your operating system using the official instructions:
   - **Linux:** [Docker Engine](https://docs.docker.com/engine/install/) (choose your distribution).
   - **Windows or macOS:** [Docker Desktop](https://docs.docker.com/desktop/).
2. Start Docker Engine or Docker Desktop.
3. Verify the client and daemon, then run Docker's test image:

```bash
docker version
docker run --rm hello-world
```

`docker version` should show both Client and Server information. The test image
prints a confirmation and exits. First builds need internet access for base
images and packages. These are setup instructions; nothing here installs Docker automatically.

## Configuration

- Use a local practice machine or VM. These labs are not production deployments.
- On Linux, use authorized daemon access (`sudo` if required) or follow the
  [post-installation guide](https://docs.docker.com/engine/install/linux-postinstall/).
  **Docker-group membership grants root-level privileges.** Do not make the Docker socket world-writable.
- Build from the chosen example folder so `.` is the correct build context.
  No shared `.env` file or custom daemon configuration is required for the eight Dockerfile labs.
- Keep website ports bound to localhost. For example,
  `-p 127.0.0.1:5000:5000` maps host port 5000 to container port 5000.
  If it is busy, change only the host port, such as `127.0.0.1:5001:5000`.
- Optional host-side tests use Python 3, Node.js 24, .NET 10 SDK, or GCC as described in each lab;
  those tools are not required on the host for Docker builds.

From the repository root, start with:

```bash
cd docker/dockerfiles/hello-python
docker build -t learn-hello-python .
docker run --rm learn-hello-python
```

Expected output: `Hello from a Docker container!`. `--rm` removes the disposable
container after it exits, not its image or your source files.

## Overview

**Navigate:** [Installation](#installation) · [Configuration](#configuration) ·
[Folders and materials](#folders-and-materials) · [Examples](#examples)

### Folders and materials

| Path | Contents and status |
| --- | --- |
| [dockerfiles/](dockerfiles/README.md) | Eight independent Dockerfile learning labs. |
| [scenario/](scenario/README.md) | Four multi-container Compose labs: WordPress with Nginx or Traefik, todo, and voting. |
| `swarm/` | Empty placeholder for future Docker Swarm material. |
| [dockerfile-best-practices.md](dockerfile-best-practices.md) | Detailed instruction reference, image size, caching, security, conventions, and troubleshooting. |
| `README.md` | This directory's installation, configuration, and navigation guide. |


Empty folders may not appear in a Git checkout because Git does not track empty directories.

### Examples

Follow this order:

| Example | What you learn |
| --- | --- |
| [Hello Python](dockerfiles/hello-python/README.md) | Basic `FROM`, `WORKDIR`, `COPY`, `USER`, and `CMD`. |
| [Flask application](dockerfiles/flask-app/README.md) | Dependencies, build caching, HTTP routes, and port publishing. |
| [Static website](dockerfiles/static-site/README.md) | Serve HTML, CSS, and JavaScript with non-root NGINX. |
| [Build arguments and environment](dockerfiles/build-args-env/README.md) | Build-time `ARG` versus runtime `ENV` overrides. |
| [ENTRYPOINT and CMD](dockerfiles/entrypoint-cmd/README.md) | Default executable, default arguments, and overrides. |
| [Multi-stage build](dockerfiles/multi-stage/README.md) | Compile a C program without shipping the compiler. |
| [Node.js API](dockerfiles/nodejs-sample/README.md) | Express, npm lockfile/cache, test stage, and non-root runtime. |
| [.NET API](dockerfiles/dotnet-sample/README.md) | ASP.NET Core minimal API with separate SDK/runtime stages. |

Each example includes source files, a `Dockerfile`, `.dockerignore`, a host-side
test, and a README explaining the instructions, build/run commands, and expected
results. Shared `.gitignore` rules keep local Python artifacts out of Git.

**Learning boundary:** Flask uses its development server for local practice only.
Host-side tests check application behavior; they do not replace Docker build and
container checks. The Swarm directory is still an empty placeholder.

For multi-container practice, continue with the [scenario index](scenario/README.md).
Each lab documents its architecture, setup, configuration, run/stop commands, and
persistence. WordPress labs require generated secret files before starting;
application labs include upstream attribution. Docker Compose is required.
Never remove data volumes or change database passwords casually.
