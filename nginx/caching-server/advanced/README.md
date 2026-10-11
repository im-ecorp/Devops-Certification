# Advanced Caching Server

Add request bypass/storage exclusion, lock-based population, background updates and stale responses.

- Configuration: [`nginx.conf`](nginx.conf), a complete standalone config.
- Listener: `127.0.0.1:8085`.
- Prerequisites and safety notes: [main README](../../README.md).
- Directive details and comparison: [topic README](../README.md).

## Run

From `nginx/`, start this in terminal 1:

```bash
python3 scripts/run_lab.py caching-server/advanced
```

In terminal 2:

```bash
curl --noproxy '*' -i -H 'Cookie: session=practice' http://127.0.0.1:8085/
```

Expect BYPASS. Run `python3 tests/verify.py LabTests.test_cache_advanced` to verify stale availability when its disposable origin stops. Serving stale content trades freshness for availability; choose an application-specific policy before production use.

Stop with Ctrl+C in terminal 1. Restart after editing; configs are not automatically reloaded. Runtime state is kept in this lab's ignored `logs/`, `temp/`, and `cache/` directories. Never reload or overwrite the system Nginx service for this exercise.
