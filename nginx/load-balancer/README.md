# Load Balancer

Distributes requests across multiple backend services to improve availability, fault tolerance, and scalability.

## Architectures

| Approach | Directory | Port | Features |
|---|---|---|---|
| **Basic** | [`basic/`](basic/) | `8086` | Round-robin load balancing (default). Routes alternating requests across `site-a` and `site-b`. |
| **Advanced** | [`advanced/`](advanced/) | `8087` | Least-connections routing with passive failure detection (`max_fails`, `fail_timeout`) and controlled retry on connection/server errors (`proxy_next_upstream`). |

## Try It

Run from `nginx/`. Keep the runner in one terminal and run curl from another. Stop with Ctrl+C before switching variants.

```bash
# Basic lab
python3 scripts/run_lab.py load-balancer/basic

# Send repeated requests to observe Site A and Site B alternating
for n in 1 2 3 4; do curl -s http://127.0.0.1:8086/; done

# Advanced lab
python3 scripts/run_lab.py load-balancer/advanced
for n in 1 2 3 4; do curl -s http://127.0.0.1:8087/; done
```

The runner owns both static origins. To practice backend failure without touching unrelated processes, run the automated test; it stops its own disposable Origin A and verifies continued HTTP 200 responses from B:

```bash
python3 tests/verify.py LabTests.test_balancer_advanced
```

Retries apply only before a response has been sent to the client. Non-idempotent requests such as POST are not blindly replayed here; the `non_idempotent` option is deliberately omitted.

## Key Directives

- `upstream backends`: Names a pool of backend servers.
- `least_conn`: Chooses the server with the lowest number of active connections.
- `max_fails=1 fail_timeout=5s`: Temporarily marks an origin unavailable after a failed attempt; Nginx open-source performs **passive** checks here, not active periodic health checks.
- `proxy_next_upstream error timeout http_502 ...`: Defines which failures trigger a retry on another server.
- `proxy_next_upstream_tries 2`: Limits the maximum attempts for one request to two.

**Note:** Basic round-robin alternates reliably for independent requests with equal-weight backends. Advanced least-connections may not follow a deterministic sequence when requests overlap.
