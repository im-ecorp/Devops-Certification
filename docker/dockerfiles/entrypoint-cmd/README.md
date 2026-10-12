# ENTRYPOINT and CMD

Scenario: make an image behave like a small command-line program.

## Instructions

- `FROM alpine:3.22`: small base with `/bin/sh` available; no extra packages.
- `WORKDIR /app` and `COPY greet.sh .`: put the script at a predictable path.
- `USER 10001:10001`: the script does not need root.
- `ENTRYPOINT ["sh", "/app/greet.sh"]`: fixes the executable. Explicit `sh` avoids needing executable file permissions.
- `CMD ["Docker learner"]`: default argument passed to the entrypoint.
- `greet.sh`: prints its first argument and exits. `set -eu` stops on command errors or unset variables; `${1:-...}` supplies a safe default.
- `.dockerignore`: excludes tests and local artifacts.

## Build and run

Prerequisite: Docker with a running daemon. From the repository root:

```bash
cd docker/dockerfiles/entrypoint-cmd
docker build -t learn-entrypoint .
docker run --rm learn-entrypoint
docker run --rm learn-entrypoint Hossein
docker run --rm --entrypoint sh learn-entrypoint -c 'id'
```

The first two runs print `Hello, Docker learner!` and `Hello, Hossein!`.
The third replaces the entrypoint and shows the unprivileged numeric user.
Arguments after the image name replace `CMD`; they do not replace an exec-form `ENTRYPOINT`.
Only the last `CMD` and last `ENTRYPOINT` in a stage take effect.
For long-running services launched through a wrapper script, end with
`exec "$@"` so the service receives stop signals directly. This short-lived
printing script does not launch a service.

## Test without Docker

Prerequisites: Python 3 and a POSIX shell. From this example directory:

```bash
sh -n greet.sh
python3 -m unittest -v test_greet.py
```

[Back to examples](../README.md)
