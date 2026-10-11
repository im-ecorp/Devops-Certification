# Basic Caching Server

Cache public 200 responses for 10 seconds and inspect cache state.

- Configuration: [`nginx.conf`](nginx.conf), a complete standalone config.
- Listener: `127.0.0.1:8084`.
- Prerequisites and safety notes: [main README](../../README.md).
- Directive details and comparison: [topic README](../README.md).

## Run

From `nginx/`, start this in terminal 1:

```bash
python3 scripts/run_lab.py caching-server/basic
```

In terminal 2:

```bash
curl --noproxy '*' -i http://127.0.0.1:8084/?exercise=basic
curl --noproxy '*' -i http://127.0.0.1:8084/?exercise=basic
```

Expect MISS then HIT on a fresh URL. Wait 11 seconds and request again to observe expiry. A prior run may already have warmed the URL. Do not use this variant for personalized pages.

Stop with Ctrl+C in terminal 1. Restart after editing; configs are not automatically reloaded. Runtime state is kept in this lab's ignored `logs/`, `temp/`, and `cache/` directories. Never reload or overwrite the system Nginx service for this exercise.
