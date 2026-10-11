# Advanced Reverse Proxy

Add upstream keepalive, WebSocket upgrade headers, bounded timeouts and a 10 MiB request-body cap.

- Configuration: [`nginx.conf`](nginx.conf), a complete standalone config.
- Listener: `127.0.0.1:8082`.
- Prerequisites and safety notes: [main README](../../README.md).
- Directive details and comparison: [topic README](../README.md).

## Run

From `nginx/`, start this in terminal 1:

```bash
python3 scripts/run_lab.py reverse-proxy/advanced
```

In terminal 2:

```bash
curl --noproxy '*' -i http://127.0.0.1:8082/
```

The static origins are not WebSocket apps. Use `python3 tests/verify.py LabTests.test_reverse_advanced` for a disposable handshake fixture. Inspect the `map`: an empty Connection header enables normal upstream keepalive.

Stop with Ctrl+C in terminal 1. Restart after editing; configs are not automatically reloaded. Runtime state is kept in this lab's ignored `logs/`, `temp/`, and `cache/` directories. Never reload or overwrite the system Nginx service for this exercise.
