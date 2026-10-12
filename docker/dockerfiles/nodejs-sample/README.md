# Node.js: a small Express API

An original, compact learning example informed by the official Node image guidance.
It is not a clone of an upstream repository. Existing folder name `nodejs-sample/`
is retained to preserve the structure you created.

## Why this example

Docker's [Node sample repository](https://github.com/docker/docker-nodejs-sample)
is a useful todo application with SQLite/PostgreSQL, a UI, and tests, but has no
checked-in Dockerfile at the time of review. Those extra components can obscure
Dockerfile basics. The [current Docker Node guide](https://docs.docker.com/guides/nodejs/)
is more comprehensive: TypeScript, separate build/dependency/runtime stages,
development workflow, database integration, and container tests. Its current DHI
images require registry login; this lab instead uses public Docker Official Node images.

This smaller API teaches a lockfile, cache mounts, non-root execution, a test stage,
and a health check without adding a database, TypeScript, or registry credentials.
For a compiled TypeScript app, add a separate compilation stage; this plain JS
app does not need one. Multi-stage builds alone do not guarantee a smaller image.

## Files and Dockerfile

- `src/server.js`: Express routes. `/` returns a JSON greeting; `/health` returns
  `{"status":"ok"}`. Unknown routes return 404. It binds `0.0.0.0` in normal use.
- `package.json` and `package-lock.json`: exact direct dependency plus locked
  transitive versions. `npm ci` refuses inconsistent manifests instead of changing the lock.
- `deps`: copies manifests before code and installs production dependencies.
  The BuildKit `/root/.npm` cache speeds downloads but is not part of the image layer.
- `test`: copies source and tests and executes `npm test`. Explicitly build this
  target: a normal runtime build may skip it because runtime does not depend on test.
- `runtime`: fresh `node:24-bookworm-slim`, only runtime dependencies and source.
  `USER node` uses the image's unprivileged account. Application files stay root-owned
  and readable, because this API does not need to modify itself.
- `NODE_ENV=production`: runtime default. `EXPOSE 3000` documents, not publishes, the port.
- Exec-form `CMD ["node", "src/server.js"]`: starts Node directly rather than through npm.
- `HEALTHCHECK`: probes `/health` using Node's built-in fetch, so curl is unnecessary.
  Docker records health status; plain Docker does not automatically restart unhealthy containers.
- `.dockerignore` excludes local dependencies and secrets; `.gitignore` excludes generated files.

## Build and run

Prerequisites: Docker with BuildKit, a running daemon, and access to Docker Hub and npm.
No host Node installation is needed for Docker builds. From the repository root:

```bash
cd docker/dockerfiles/nodejs-sample
docker build --target test -t learn-nodejs-test .
docker build --target runtime -t learn-nodejs .
docker run --rm --init -p 127.0.0.1:3000:3000 learn-nodejs
```

`--init` adds a small init process for signals and reaping child processes.
The service logs no startup banner; leave the terminal running. In another terminal:

```bash
curl -f http://127.0.0.1:3000/
curl -f http://127.0.0.1:3000/health
```

Expected: `{"message":"Hello from Node.js in Docker!"}` and `{"status":"ok"}`.
Stop with Ctrl+C; `--rm` removes this disposable container.

## Verify and experiment

With host Node.js 24 and npm, from this example directory:

```bash
npm ci
npm test
npm audit --omit=dev
node --check src/server.js
```

The HTTP test starts on an ephemeral localhost port and checks greeting, health,
and 404 responses. To see Docker caching, build twice, edit only the greeting,
and rebuild with `--progress=plain`; the dependency install should remain cached.

Read-only checks after building:

```bash
docker run --rm --entrypoint id learn-nodejs
docker ps
docker inspect --format='{{json .State.Health}}' 'CONTAINER_ID'
```

Replace `CONTAINER_ID` with the running container's ID. To change the port:

```bash
docker run --rm --init -e PORT=3001 -p 127.0.0.1:3001:3001 learn-nodejs
```

This is a stateless learning API, not a full production deployment. Review and
update dependencies and base digests before deployment, add appropriate limits
and logging, and terminate TLS appropriately. Versioned image tags can move.
Local tests and npm audit do not verify the image or its OS packages.

Sources: [Node image best practices](https://github.com/nodejs/docker-node/blob/main/docs/BestPractices.md),
[Docker Node guide](https://docs.docker.com/guides/nodejs/).

[Back to labs](../README.md)
