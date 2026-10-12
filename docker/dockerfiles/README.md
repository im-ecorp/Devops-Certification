# Dockerfile learning labs

Eight small, independent build contexts. Follow them in order. Each folder has a
`Dockerfile`, source files, a `.dockerignore`, and a README with the exact build,
run, expected output, and explanation of every significant instruction.

| Lab | Learn |
| --- | --- |
| [Hello Python](hello-python/README.md) | `FROM`, `WORKDIR`, `COPY`, `USER`, `CMD` |
| [Flask app](flask-app/README.md) | Python dependencies, cache ordering, `EXPOSE`, non-root runtime |
| [Static site](static-site/README.md) | HTML/CSS/JS with non-root NGINX and port publishing |
| [Build args and environment](build-args-env/README.md) | Build-time default versus runtime override |
| [ENTRYPOINT and CMD](entrypoint-cmd/README.md) | CLI defaults and argument overrides |
| [Multi-stage build](multi-stage/README.md) | Compile in one stage, run in a smaller stage |
| [Node.js API](nodejs-sample/README.md) | npm lockfile, cache mount, test stage, non-root Express API |
| [.NET API](dotnet-sample/README.md) | Separate SDK/ASP.NET runtime, restore caching, non-root minimal API |

## Prerequisites and workflow

Docker Engine or Docker Desktop with a running daemon is required for image
builds. Commands assume you are at the repository root unless the lab says
otherwise. Build **inside the chosen lab directory**: Docker only sees files in
the build context (`.`), not sibling labs. Public image registries and the
Python package index/npm registry are needed where applicable on first build.
Host-side checks use Python 3, Node.js 24, .NET 10 SDK, or GCC as noted in
each lab; Docker builds do not require those host tools.

```bash
cd docker/dockerfiles/hello-python
docker build -t learn-hello-python .
docker run --rm learn-hello-python
```

Read the [Dockerfile best-practices guide](../dockerfile-best-practices.md) before adapting the
examples for production. The Flask development server is for local learning
only. Examples use versioned base-image tags, not immutable digests; rebuild
with security updates and pin digests when reproducibility matters.
