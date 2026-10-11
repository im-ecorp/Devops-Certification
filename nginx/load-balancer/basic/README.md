# Basic Load Balancer

Spread independent requests equally using default round-robin routing.

- Configuration: [`nginx.conf`](nginx.conf), a complete standalone config.
- Listener: `127.0.0.1:8086`.
- Prerequisites and safety notes: [main README](../../README.md).
- Directive details and comparison: [topic README](../README.md).

## Run

From `nginx/`, start this in terminal 1:

```bash
python3 scripts/run_lab.py load-balancer/basic
```

In terminal 2:

```bash
for n in 1 2 3 4; do curl --noproxy '*' -s http://127.0.0.1:8086/; done
```

Expect both Origin A and Origin B. Add `weight=2` to A, restart, and compare counts across multiple requests; restore the equal-weight setup after the exercise.

Stop with Ctrl+C in terminal 1. Restart after editing; configs are not automatically reloaded. Runtime state is kept in this lab's ignored `logs/`, `temp/`, and `cache/` directories. Never reload or overwrite the system Nginx service for this exercise.
