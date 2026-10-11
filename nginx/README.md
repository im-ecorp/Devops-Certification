# Nginx Hands-on Labs

Seven standalone Nginx Open Source configurations covering four roles. Each config is a **complete `nginx.conf`**, not a fragment to copy into `conf.d`. Basic variants introduce the mechanism; advanced variants add operational behavior. All listeners bind to `127.0.0.1`, so these labs do not publish services on your network.

## Topics

- [Reverse Proxy](reverse-proxy/README.md) — Basic HTTP forwarding; Advanced WebSocket upgrades, keepalive and timeouts.
- [Forward Proxy](forward-proxy/README.md) — One restricted HTTP-only configuration; no unsupported HTTPS CONNECT example.
- [Caching Server](caching-server/README.md) — Basic response caching; Advanced bypass rules, locking and stale responses.
- [Load Balancer](load-balancer/README.md) — Basic round-robin; Advanced least-connections and passive failover.

## Directory Structure

```text
nginx/
├── README.md
├── .gitignore
├── reverse-proxy/
│   ├── README.md
│   ├── basic/       # nginx.conf + README.md
│   └── advanced/    # nginx.conf + README.md
├── forward-proxy/
│   ├── README.md
│   └── nginx.conf
├── caching-server/
│   ├── README.md
│   ├── basic/       # nginx.conf + README.md
│   └── advanced/    # nginx.conf + README.md
├── load-balancer/
│   ├── README.md
│   ├── basic/       # nginx.conf + README.md
│   └── advanced/    # nginx.conf + README.md
├── fixtures/
│   ├── site-a/index.html
│   └── site-b/index.html
├── scripts/run_lab.py
└── tests/
    ├── verify.py
    └── test_runner.py
```

Use lowercase kebab-case topic names consistently. Forward proxy has one directory because this lab deliberately avoids custom CONNECT modules. Runtime `logs/`, `temp/`, and `cache/` directories are created on demand and ignored by Git.

## Prerequisites

- Linux with Nginx Open Source **1.26.3 or newer**; tests were exercised on 1.26.3.
- Python 3.9+ (standard library only) and curl.
- Free loopback ports 9001, 9002, and the selected lab port below.

```bash
nginx -v
python3 --version
curl --version
```

Install Nginx using your distribution's package instructions if needed. No Docker, external domains, certificates, third-party modules, or internet origins are required. Installing a distro package may start a system service; these labs do not modify or reload that service.

## Quick Start

1. Open a terminal in this directory:

   ```bash
   cd /root/mygit/Devops-Certification/nginx
   python3 scripts/run_lab.py --list
   python3 scripts/run_lab.py reverse-proxy/basic
   ```

   Use your clone's `nginx/` path if different. The runner validates the config, starts static Origin A on 9001 and Origin B on 9002, and runs one Nginx master in the foreground. A port conflict aborts startup rather than using another application's origin.

2. From a second terminal, send a request:

   ```bash
   curl --noproxy '*' -i http://127.0.0.1:8081/
   ```

   Expect HTTP 200 and `Origin A (port 9001)` in the HTML body.

3. Stop with **Ctrl+C** in the runner terminal. It stops only its own Nginx and origin servers. Stop one lab before starting another because all runners use the same origin ports.

| Lab selector | Listener | What to observe |
|---|---|---|
| `reverse-proxy/basic` | 8081 | Origin A served through Nginx |
| `reverse-proxy/advanced` | 8082 | Same HTTP response; automated WebSocket handshake test |
| `forward-proxy` | 8083 | Explicit curl proxy request; forbidden unlisted destinations |
| `caching-server/basic` | 8084 | `X-Cache-Status: MISS`, then `HIT` within 10 seconds |
| `caching-server/advanced` | 8085 | Cookie/Authorization `BYPASS`; stale availability in tests |
| `load-balancer/basic` | 8086 | Origin A/B alternating across independent requests |
| `load-balancer/advanced` | 8087 | Least-connections selection and tested backend failover |

Read each topic README for commands and directive explanations. If Nginx is not on PATH, append `--nginx /absolute/path/to/nginx` to runner or verification commands.

## Validation

```bash
# Tests all seven configs with nginx -t and real HTTP requests.
python3 tests/verify.py

# Tests the user-facing runner's startup and shutdown (ports 8081/9001/9002).
python3 tests/test_runner.py

# Alternative binary for both commands:
python3 tests/verify.py --nginx /absolute/path/to/nginx
NGINX_BINARY=/absolute/path/to/nginx python3 tests/test_runner.py
```

`verify.py` allocates disposable origin/listener ports, changes **only numeric addresses in scratch copies**, and exercises URL/header forwarding, WebSocket handshake propagation, forward-proxy allowlist and CONNECT rejection, cache MISS/HIT, origin `no-store`/`Set-Cookie` protections, personalized-request bypass, stale responses after origin failure, round-robin distribution, and advanced failover. The stale test waits 11 seconds beyond its 10-second TTL. This is not a benchmark, a complete WebSocket implementation, or a concurrent least-connections distribution test.

Tests preserve scratch evidence under `$TMPDIR` (or the platform's temporary directory) and stop their own child processes. No cache purge or broad process-kill commands are used.

## Operations and Troubleshooting

- Inspect the chosen lab's `logs/error.log` and `logs/access.log`.
- `502 Bad Gateway`: verify that the runner's origins started, or check your custom backend's address.
- `Address already in use`: stop the other lab with Ctrl+C; do not kill unrelated services.
- Cache changes: wait for the TTL or use a fresh query string. Persistent lab caches remain after shutdown.
- Prefer running as a **normal user** in a writable clone. If invoked as root, the runner keeps lab workers as root to access `/root` and private directories; this is only for loopback practice, **not production**.
- Do not copy these configs over `/etc/nginx/nginx.conf`. They intentionally use local writable paths and loopback origins. Production requires a reviewed user/permission model, TLS, trusted forwarded-header handling, network policy, and monitoring.

The former site-specific configuration and password file are not part of these labs. Removing them from the working tree does not remove their contents from existing Git history.

References: [proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html), [upstream module](https://nginx.org/en/docs/http/ngx_http_upstream_module.html), [WebSocket proxying](https://nginx.org/en/docs/http/websocket.html), [load balancing](https://nginx.org/en/docs/http/load_balancing.html).
