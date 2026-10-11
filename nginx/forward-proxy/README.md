# Forward Proxy

A forward proxy accepts outbound HTTP requests from internal clients and fetches external web resources on their behalf.

Unlike Reverse Proxy (which shields servers from external clients), a Forward Proxy shields internal clients from destination servers and acts as a single egress gateway.

## Single Approach Layout

Nginx can fetch HTTP destinations through variable-based `proxy_pass`, but it is not a full general-purpose forward proxy. This lab routes only two numeric loopback origins through an explicit allowlist; it needs no DNS resolver. Stock Nginx does not support HTTPS `CONNECT` tunneling. Use a dedicated forward proxy such as Squid for that purpose; TCP pass-through is not a replacement for HTTP CONNECT. A third-party CONNECT module needs separate compilation and security review, so no untested advanced variant is included.

## Architecture

- **Directory:** [`forward-proxy/`](.)
- **Listen Port:** `127.0.0.1:8083`
- **Security:** Locked to loopback and restricted to an explicit origin allowlist via Nginx `map` table (`127.0.0.1:9001` and `127.0.0.1:9002`). Unapproved destinations return `403 Forbidden`. `CONNECT` requests are rejected: core Nginx may return `400` before the configured `405` handler is reached.

> **Security Warning:** Never expose an unrestricted forward proxy to a public network. Open forward proxies are rapidly exploited as attack vectors, spam relays, and SSRF jump hosts.

## Try It

Run from `nginx/`. Keep the runner in one terminal and run curl from another. `--noproxy ""` prevents environment settings from bypassing the proxy for loopback destinations.

```bash
# Run the forward proxy lab
python3 scripts/run_lab.py forward-proxy

# Use curl configured with Nginx as its HTTP proxy
curl --noproxy "" -x http://127.0.0.1:8083 http://127.0.0.1:9001/

# Test origin allowlist enforcement (blocked destination returns 403)
curl --noproxy "" -x http://127.0.0.1:8083 http://example.invalid/

# Confirm CONNECT rejection (returns 405 or 400)
curl --noproxy "" -p -x http://127.0.0.1:8083 https://127.0.0.1:9001/
```

## Key Directives

- `proxy_pass http://$allowed_origin`: Evaluates the requested destination host and routes to the authorized destination.
- `proxy_set_header Host $http_host`: Preserves the destination host requested by the client.
- `map $http_host $allowed_origin`: Whitelists trusted backend endpoints and blocks arbitrary outbound network access.
