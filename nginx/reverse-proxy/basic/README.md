# Basic Reverse Proxy

Forward requests to one origin while preserving paths and forwarding headers.

- Configuration: [`nginx.conf`](nginx.conf), a complete standalone config.
- Listener: `127.0.0.1:8081`.
- Prerequisites and safety notes: [main README](../../README.md).
- Directive details and comparison: [topic README](../README.md).

## Run

From `nginx/`, start this in terminal 1:

```bash
python3 scripts/run_lab.py reverse-proxy/basic
```

In terminal 2:

```bash
curl --noproxy '*' -i http://127.0.0.1:8081/
```

Expect HTTP 200 and Origin A. Edit the destination port in `proxy_pass` to a free unused port, restart the runner, and observe 502; restore the value afterwards.

Stop with Ctrl+C in terminal 1. Restart after editing; configs are not automatically reloaded. Runtime state is kept in this lab's ignored `logs/`, `temp/`, and `cache/` directories. Never reload or overwrite the system Nginx service for this exercise.
