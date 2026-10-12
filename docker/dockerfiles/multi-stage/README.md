# Multi-stage build: keep the compiler out

Scenario: compile a tiny C program, then ship only its binary and runtime libraries.
C is used to make the difference between a build stage and a runtime stage visible.
You do not need a compiler on the host to build with Docker.

## Instructions

- `FROM debian:bookworm-slim AS builder`: names a stage containing build tools.
- `RUN apt-get update && apt-get install ... && rm ...`: installs `gcc` and C headers without optional packages. Package indexes are removed in the same layer, not a later layer.
- `WORKDIR /src` and `COPY hello.c .`: isolate compilation input.
- `RUN gcc ... -o /hello`: compiles with warnings enabled and produces a binary.
- A second `FROM debian:bookworm-slim AS runtime` starts a clean stage.
- `COPY --from=builder /hello /app/hello`: copies just the compiled artifact, not the compiler or source.
- `USER 10001:10001`: the program needs no root privileges.
- `CMD ["/app/hello"]`: runs the binary.
- `.dockerignore`: excludes the host-side test and caches.

Both stages use the same Debian release for compatible C runtime libraries.
This binary is dynamically linked: copying it into `scratch` would omit its
loader and libraries and would not work.

## Build and run

Prerequisite: Docker with a running daemon and network access for Debian packages.
From the repository root:

```bash
cd docker/dockerfiles/multi-stage
docker build -t learn-multi-stage .
docker run --rm learn-multi-stage
docker build --target builder -t learn-multi-stage-builder .
docker image ls learn-multi-stage
docker image ls learn-multi-stage-builder
docker run --rm --entrypoint sh learn-multi-stage -c 'command -v gcc || echo "No compiler in runtime image"'
```

Expected greeting: `Hello from a multi-stage build!`.
The final image should be smaller than the builder image; actual sizes depend on
platform and base image updates. The final check prints `No compiler in runtime image`.

## Test without Docker

Prerequisites: Python 3 and GCC on the host. From this example directory:

```bash
python3 -m unittest -v test_hello.py
```

The test compiles into a temporary directory and checks the output. It does not
verify the image's runtime libraries or the absence of build tools.

[Back to examples](../README.md)
