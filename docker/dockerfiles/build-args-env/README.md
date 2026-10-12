# Build arguments versus environment variables

Scenario: set a default greeting at build time, then override it without rebuilding.

## Instructions

- `FROM`, `WORKDIR`, `COPY`, `USER`, and exec-form `CMD` follow the [first example](../hello-python/README.md).
- `ARG APP_NAME="Docker learner"` declares a build-time value. `ARG` alone does not become a container environment variable.
- `ENV APP_NAME=${APP_NAME}` deliberately stores that value as a runtime default.
- `app.py` reads the runtime environment and prints a greeting.
- `.dockerignore` excludes tests and local artifacts.

## Build and run

Prerequisite: Docker with a running daemon. From the repository root:

```bash
cd docker/dockerfiles/build-args-env
docker build -t learn-config .
docker run --rm learn-config
docker run --rm -e APP_NAME=Hossein learn-config
docker build --build-arg APP_NAME="Build-time learner" -t learn-config-custom .
docker run --rm learn-config-custom
```

Expected outputs, in order:

```text
Hello, Docker learner!
Hello, Hossein!
Hello, Build-time learner!
```

Changing `-e` changes one container. Changing `--build-arg` creates a new image.
An `ARG` declared before `FROM` must be redeclared inside a stage to use it there.
Never use `ARG` or `ENV` for passwords or tokens; use BuildKit secret mounts for
build-time credentials and deployment secret mechanisms at runtime.

## Test without Docker

Prerequisite: Python 3. From this example directory:

```bash
python3 -m unittest -v test_config.py
```

[Back to examples](../README.md)
