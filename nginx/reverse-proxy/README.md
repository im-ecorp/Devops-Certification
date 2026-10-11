# Reverse Proxy

Directs incoming client traffic to internal origins without exposing backend architecture.

## Architectures

| Approach | Directory | Port | Features |
|---|---|---|---|
| **Basic** | [`basic/`](basic/) | `8081` | Standard HTTP pass-through, `Host` forwarding, `X-Forwarded-*` headers, single origin. |
| **Advanced** | [`advanced/`](advanced/) | `8082` | HTTP/1.1 keepalive pooling, dynamic WebSocket upgrade mapping, bounded timeouts (connect, read, send), client upload cap (`10m`). |

## Try It

Run commands from the `nginx/` directory. Start one lab per terminal session; run `curl` from a second terminal. Stop the first lab with Ctrl+C before switching.

```bash
# Basic lab
python3 scripts/run_lab.py reverse-proxy/basic
curl -i http://127.0.0.1:8081/

# Advanced lab
python3 scripts/run_lab.py reverse-proxy/advanced
curl -i http://127.0.0.1:8082/

# Automated WebSocket handshake fixture (the static origin is not a WebSocket app)
python3 tests/verify.py LabTests.test_reverse_advanced
```

## Key Directives

- `proxy_pass`: Destination URI or upstream block.
- `proxy_set_header Host $host`: Retains the requested virtual host header.
- `proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for`: Appends the direct client IP. A backend must trust only known proxies; earlier values can be client-supplied.
- `proxy_pass` without a trailing URI preserves `/path?query`; adding a URI changes location-prefix replacement behavior.
- `proxy_http_version 1.1`: Enables HTTP/1.1 required for WebSocket and upstream keepalive.
- `map $http_upgrade $connection_upgrade`: Passes `Upgrade: websocket` only when the client sends an upgrade request; otherwise removes the `Connection` header so upstream keepalive can work.
