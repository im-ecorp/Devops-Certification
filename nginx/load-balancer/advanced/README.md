# Advanced Load Balancer

Route by least active connections with passive failure detection and bounded retries.

- Configuration: [`nginx.conf`](nginx.conf), a complete standalone config.
- Listener: `127.0.0.1:8087`.
- Prerequisites and safety notes: [main README](../../README.md).
- Directive details and comparison: [topic README](../README.md).

## Run

From `nginx/`, start this in terminal 1:

```bash
python3 scripts/run_lab.py load-balancer/advanced
```

In terminal 2:

```bash
for n in 1 2 3 4; do curl --noproxy '*' -s http://127.0.0.1:8087/; done
```

Use `python3 tests/verify.py LabTests.test_balancer_advanced` to verify failover. Sequential requests do not prove the algorithm favors a less-busy server; experiment with overlapping slow requests in your own backend to see that behavior.

Stop with Ctrl+C in terminal 1. Restart after editing; configs are not automatically reloaded. Runtime state is kept in this lab's ignored `logs/`, `temp/`, and `cache/` directories. Never reload or overwrite the system Nginx service for this exercise.
