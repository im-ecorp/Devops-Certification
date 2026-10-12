# Hello Python: your first image

A one-file program prints a greeting and exits. Start here before the web examples.

## Files and instructions

| File or instruction | Purpose |
| --- | --- |
| `hello.py` | Prints one line; no third-party packages. |
| `FROM python:3.12-slim` | Starts with Python installed on a small Debian base. |
| `WORKDIR /app` | Sets the directory for later `COPY` and the runtime command. |
| `COPY hello.py .` | Copies only the application into `/app`. |
| `USER 10001:10001` | Runs without root; no account entry is needed for this program. |
| `CMD ["python", "hello.py"]` | Default command, in exec form. |
| `.dockerignore` | Keeps tests, caches, and documentation out of the build context. |

## Build and run

Prerequisite: Docker with a running daemon. From the repository root:

```bash
cd docker/dockerfiles/hello-python
docker build -t learn-hello-python .
docker run --rm learn-hello-python
```

Expected output: `Hello from a Docker container!`. Exiting immediately is correct.
`--rm` removes this disposable container after exit, not the image or source files.

## Try it

Change the greeting, build again, and run again. Editing source does not update an existing image.

## Test without Docker

Prerequisite: Python 3.

```bash
python3 -m unittest -v test_hello.py
```

[Back to examples](../README.md)
