# Dockerfile practice

Beginner labs for building images, running containers, and understanding why each
instruction belongs in a Dockerfile. These are local learning examples, not
complete production deployments.

## Contents

- [Directory structure](#directory-structure)
- [Start here](#start-here)
- [Dockerfile instructions](#dockerfile-instructions)
- [Write a Dockerfile correctly](#write-a-dockerfile-correctly)
- [Optimize image size](#optimize-image-size)
- [Use caching effectively](#use-caching-effectively)
- [Improve security](#improve-security)
- [Follow common conventions](#follow-common-conventions)
- [Troubleshooting and verification](#troubleshooting-and-verification)
- [Official references](#official-references)

## Directory structure

Labs use lowercase kebab-case folder names under `dockerfiles/`; the
conventional build filename remains exactly `Dockerfile`.

```text
docker/
├── README.md
└── dockerfiles/
    ├── README.md
    ├── hello-python/
    ├── flask-app/
    ├── static-site/
    ├── build-args-env/
    ├── entrypoint-cmd/
    ├── multi-stage/
    ├── nodejs-sample/
    └── dotnet-sample/
```

Each lab contains its own `Dockerfile`, `.dockerignore`, README, source, and
host-side check. Local editing snapshots are ignored and not published.

| Recommended order | Example | Main concept |
| --- | --- | --- |
| 1 | [Hello Python](dockerfiles/hello-python/README.md) | Basic image instructions |
| 2 | [Flask app](dockerfiles/flask-app/README.md) | Dependencies, caching, web ports |
| 3 | [Static site](dockerfiles/static-site/README.md) | HTML/CSS/JS served by non-root NGINX |
| 4 | [Build args and environment](dockerfiles/build-args-env/README.md) | `ARG` versus `ENV` |
| 5 | [ENTRYPOINT and CMD](dockerfiles/entrypoint-cmd/README.md) | Default command and arguments |
| 6 | [Multi-stage build](dockerfiles/multi-stage/README.md) | Keep compilers out of runtime images |
| 7 | [Node.js API](dockerfiles/nodejs-sample/README.md) | Test stages and locked npm dependencies |
| 8 | [.NET API](dockerfiles/dotnet-sample/README.md) | Separate SDK and ASP.NET runtime stages |

## Start here

Prerequisite: Docker Engine or Docker Desktop with a running daemon. First builds
need network access to pull base images and dependencies. See the
[lab index](dockerfiles/README.md) for optional host-side testing prerequisites.

From the repository root:

```bash
docker version
cd docker/dockerfiles/hello-python
docker build -t learn-hello-python .
docker run --rm learn-hello-python
```

Expected output: `Hello from a Docker container!`.

- **Dockerfile:** the recipe.
- **Image:** the packaged filesystem and runtime configuration built from it.
- **Container:** a running or stopped instance of an image.
- **Build context:** files available to the build. The final `.` means the current directory.
- `-t` names the image. `--rm` removes this disposable container after it exits;
  it does not remove the image or your source files.

## Dockerfile instructions

| Instruction | What it does | Common mistake |
| --- | --- | --- |
| `FROM` | Selects the base image or starts a new stage | Using `latest` without an update policy |
| `WORKDIR` | Sets an absolute working directory for later steps and runtime | Expecting `RUN cd /app` to persist into another instruction |
| `COPY` | Copies selected files from the context or another stage | Copying secrets or unrelated repository files |
| `RUN` | Executes during the build | Starting a web server here |
| `ENV` | Stores runtime environment defaults; also available during build | Treating it as secret storage |
| `ARG` | Declares build-time variables | Expecting it to exist at runtime automatically |
| `USER` | Sets the user for subsequent build steps and runtime | Running the application as root unnecessarily |
| `EXPOSE` | Documents a listening container port | Assuming it publishes a host port |
| `CMD` | Sets the default runtime command or entrypoint arguments | Defining multiple commands and expecting all to run |
| `ENTRYPOINT` | Sets the executable, often paired with default `CMD` arguments | Forgetting arguments after the image name replace `CMD` |
| `LABEL` | Adds image metadata | Using deprecated `MAINTAINER` |
| `HEALTHCHECK` | Defines an optional runtime health probe | Assuming unhealthy containers automatically restart in plain Docker |

## Write a Dockerfile correctly

1. Choose a trusted base with the runtime you need.
2. Set `WORKDIR` to an absolute path.
3. Copy dependency manifests and install dependencies before copying changing source.
4. Copy only the files the application needs.
5. Set a non-root runtime user and give it only the permissions it needs.
6. Document web ports with `EXPOSE`; publish them explicitly when running.
7. Use exec-form `CMD` or `ENTRYPOINT` to start the process in the foreground.

The [Flask Dockerfile](dockerfiles/flask-app/Dockerfile) is a complete example.
This shorter excerpt illustrates the ordering; it is not a separate lab:

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
USER 10001:10001
EXPOSE 5000
CMD ["python", "app.py"]
```

`RUN` happens while building; `CMD` happens when running. Prefer
`CMD ["python", "app.py"]` over shell-form `CMD python app.py` so signals reach
the process directly. Exec form does not expand shell variables: use application
configuration or an intentional shell wrapper when expansion is needed.
`COPY` is the ordinary choice for local files. Use `ADD` only when its additional
features, such as archive extraction, are actually required.

## Optimize image size

- Choose a small compatible base, such as `python:3.12-slim`. Alpine is small,
  but its musl libc can complicate Python packages and precompiled binaries;
  smaller is not always simpler.
- Install only required packages, not editors or debugging tools by default.
- Use `pip install --no-cache-dir` so download caches are not shipped.
- Use `.dockerignore` to exclude `.git`, virtual environments, caches, tests,
  credentials, and unrelated files. Explicit `COPY` limits what enters the image;
  `.dockerignore` also limits the context sent to the builder.
- Install and clean OS package indexes in the **same** `RUN` instruction:

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
```

This removes disposable package indexes **inside the build layer**, not on the
host. Removing files in a later layer does not erase bytes from earlier layers.
Keep `apt-get update` with the install so a cached index cannot become stale.

- Use [multi-stage builds](dockerfiles/multi-stage/README.md) to leave compilers,
  source, and build dependencies out of the final image.
- Optimize content first, not merely instruction count. Fewer lines do not
  automatically mean a smaller or better image.

## Use caching effectively

Docker can reuse unchanged build steps. A changed input normally invalidates its
step and dependent later steps in the stage.

Good dependency ordering:

```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
```

Changing `app.py` can reuse the expensive installation layer. Copying everything
before installation would cause code edits to invalidate it.

From `docker/dockerfiles/flask-app/`:

```bash
docker build --progress=plain -t learn-flask .
```

Build twice, then edit only `app.py` and build again to observe reused steps.
Docker's build cache and pip's download cache are different mechanisms.
For larger projects, BuildKit cache mounts can speed package downloads without
shipping them in the image; they are optional for these small labs.

- `--pull` checks for a newer base image under the selected tag.
- `--no-cache` reruns build steps; it does **not** pull a fresh base on its own.
- Use `--pull --no-cache` together when you deliberately need both. Do not disable
  caching for every ordinary source edit.

## Improve security

- Run as a non-root user. Install OS packages before switching `USER`;
  avoid switching back to root during runtime.
- Give write permissions only where needed. Fix ownership deliberately; do not
  use `chmod 777` to hide permission errors.
- Never bake passwords, tokens, private keys, or `.env` secrets into an image.
  Deleting a copied secret later does not remove it from earlier layers.
  `ARG` and `ENV` are not secret stores; use BuildKit secret mounts for builds
  and appropriate runtime secret injection for deployments.
- Use trusted, maintained base images. Version tags improve clarity but can
  move. Pin an image digest (`image:tag@sha256:<verified-digest>`) for an immutable
  base, then deliberately update it for security fixes. Do not copy an invented digest.
- Pin application dependencies and, for production, lock transitive dependencies
  and verify package hashes. The Flask lab pins only its direct dependency.
- Rebuild regularly with patched dependencies; an existing image does not update itself.
- Scan images with your available scanner, review findings, and reduce unnecessary
  packages. Small images are not automatically secure.
- Publish learning ports on localhost, such as
  `-p 127.0.0.1:5000:5000`, rather than all interfaces.
- Do not use `--privileged`, host networking, or a Docker socket mount for these labs.
- Keep runtime data in deliberate mounts when needed. Do not rely on a disposable
  container filesystem for persistent data; these examples require no persistence.

The Flask development server is **not for production**. Production needs a WSGI
server and appropriate TLS, access controls, logging, and deployment configuration.
The static example uses a maintained non-root NGINX variant; plain HTML/CSS/JS
needs no Node.js runtime in the image.

## Follow common conventions

- Name the build file exactly `Dockerfile`; use uppercase instructions.
- Use lowercase kebab-case directories and descriptive image tags.
- Put `# syntax=docker/dockerfile:1` at the top to use the stable Dockerfile frontend.
- Use absolute `WORKDIR` paths and explicit `COPY` sources.
- Keep one application concern per container; a web server may legitimately
  create worker processes. Do not add a database to the same Flask image.
- Send logs to stdout/stderr and keep the main process in the foreground.
- Use one effective `CMD` and `ENTRYPOINT` per stage; later definitions replace earlier ones.
- Use `LABEL` for metadata, not deprecated `MAINTAINER`.
- Comment on **why**, not merely what a line already says.
- Keep one independent build context per lab with its own README and `.dockerignore`.

## Troubleshooting and verification

| Symptom | Check |
| --- | --- |
| `docker: command not found` | Install Docker separately; these files do not install it. |
| Cannot connect to the Docker daemon | Confirm Docker is running and your user has authorized access. Docker-group access is effectively root-level. |
| `COPY` cannot find a file | Build from the correct lab directory; check `.dockerignore`. `-f` selects a Dockerfile but does not change the context. |
| Web page is unreachable | Confirm the process binds `0.0.0.0`, the published container port matches the app, and the container is still running. |
| Host port already in use | Choose another host port, for example `127.0.0.1:5001:5000`. The container port remains 5000. |
| Container exits immediately | Expected for the printing labs; inspect logs if it is a web server. |
| Changes are not visible | Rebuild the image and start a new container. |
| Permission denied | Check `USER`, file ownership, and writable paths; do not grant blanket permissions. |

Read-only diagnostics:

```bash
docker ps -a
docker images
docker logs 'CONTAINER_ID'
docker image inspect learn-flask
docker history learn-flask
```

Replace `CONTAINER_ID` with the actual ID before running. Avoid global prune
commands for lab cleanup: they may remove unrelated Docker resources.

Verification checklist:

1. Build the image from its documented directory.
2. Run the container and verify the expected greeting or HTTP response.
3. For websites, load CSS and JS too, and click the button in a browser.
4. Inspect the runtime user and image history.
5. Repeat a build to observe caching; compare final and builder sizes for the multi-stage lab.
6. Review dependencies and security findings before using the pattern in production.

Each lab documents optional host-side tests. These test application behavior,
not image builds. Docker builds and container runtime checks are still required.

## Official references

- [Docker build best practices](https://docs.docker.com/build/building/best-practices/)
- [Dockerfile instruction reference](https://docs.docker.com/reference/dockerfile/)
- [Build context and .dockerignore](https://docs.docker.com/build/concepts/context/)
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Build secrets](https://docs.docker.com/build/building/secrets/)
- [NGINX unprivileged image](https://github.com/nginx/docker-nginx-unprivileged)
