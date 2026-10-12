# Flask: a small web application

Scenario: package a tiny HTTP service with one dependency. `/` returns a greeting;
`/health` returns `{"status":"ok"}`. There is no database, authentication, or persistent data.

## Files and instructions

- `app.py`: routes and server startup. `0.0.0.0` lets traffic reach the process from outside the container. Binding to `127.0.0.1` inside the container would block published-port access.
- `requirements.txt`: pins the direct Flask dependency. Transitive dependencies are not locked; a production project should lock and review the full dependency set.
- `FROM python:3.12-slim`: Python runtime without a full development toolchain.
- `ENV`: disables bytecode files and makes logs appear immediately.
- `WORKDIR /app`: stable location for files and the startup command.
- `COPY requirements.txt .` then `RUN pip install --no-cache-dir ...`: install dependencies before copying code so code edits can reuse the dependency layer. `--no-cache-dir` avoids storing pip's download cache; it does not disable Docker's layer cache.
- `RUN groupadd ... && useradd ...`: creates an unprivileged account.
- `COPY --chown=app:app app.py .` and `USER app`: copies the code and runs it without root.
- `EXPOSE 5000`: documents the container port; does not publish it.
- `CMD ["python", "app.py"]`: starts the service when a container runs, not during build.
- `.dockerignore`: excludes tests, docs, and local Python artifacts.

## Build and run

Prerequisites: Docker with a running daemon; `curl` for the checks. From the repository root:

```bash
cd docker/dockerfiles/flask-app
docker build -t learn-flask .
docker run --rm -p 127.0.0.1:5000:5000 learn-flask
```

In another terminal:

```bash
curl http://127.0.0.1:5000/
curl http://127.0.0.1:5000/health
```

Expected: `Hello from Flask in Docker!` and `{"status":"ok"}`.
Open <http://127.0.0.1:5000/> in a browser. Stop with Ctrl+C;
`--rm` then removes the disposable container.

**Learning only:** this uses Flask's development server with debug mode off.
Do not expose it publicly or deploy it as a production server. Production needs a
WSGI server such as Gunicorn, reviewed dependencies, and appropriate deployment controls.

## Cache exercise

1. Build once.
2. Change the greeting in `app.py`, then build again with `--progress=plain`.
3. Observe that the requirements installation can stay cached.
4. Change `requirements.txt`, then rebuild. That invalidates the dependency layer and subsequent steps.

## Test without Docker

Prerequisite: Python 3 with `venv`. Run from this example directory:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m unittest -v test_app.py
```

[Back to examples](../README.md)
