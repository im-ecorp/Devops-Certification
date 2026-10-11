# Caching Server

Accelerates response delivery and relieves backend load by storing origin responses on disk and serving repeated requests locally.

## Architectures

| Approach | Directory | Port | Features |
|---|---|---|---|
| **Basic** | [`basic/`](basic/) | `8084` | File-backed proxy cache (`levels=1:2`), 10-second TTL for `200` responses, `X-Cache-Status` diagnostic response header (`HIT`/`MISS`). |
| **Advanced** | [`advanced/`](advanced/) | `8085` | Cache stampede prevention (`proxy_cache_lock`), stale cache serving during origin failures and updates (`proxy_cache_use_stale`), background cache refreshes, and cache bypass/exclusion rules for `Authorization` headers, session cookies, and private paths (`/private/`, `/admin/`). |

## Try It

Run from `nginx/`. Keep the runner in one terminal and run curl from another. Stop with Ctrl+C before switching variants.

```bash
# Basic lab
python3 scripts/run_lab.py caching-server/basic

# Request twice to observe cache transition from MISS to HIT
curl -i http://127.0.0.1:8084/
curl -i http://127.0.0.1:8084/

# Advanced lab
python3 scripts/run_lab.py caching-server/advanced

# Verify bypass when Authorization or Cookie header is provided
curl -i -H "Authorization: Bearer token123" http://127.0.0.1:8085/
curl -i -H "Cookie: session=xyz" http://127.0.0.1:8085/

# Private path bypasses cache, but the static fixture returns 404 (no such file).
curl -i http://127.0.0.1:8085/private/dashboard

# Automated fixture verifies BYPASS and stale responses after origin failure.
python3 tests/verify.py LabTests.test_cache_advanced
```

The basic variant is for **public, non-personalized responses only**. The advanced variant skips both cache lookup and storage for cookies, Authorization, and private paths. Both respect origin `Cache-Control: no-store` and `Set-Cookie` behavior; never use `proxy_ignore_headers` to disable those protections without a deliberate policy. Origin freshness headers can override `proxy_cache_valid`.

To change cached content, wait for the 10-second TTL or use a fresh query string. No purge endpoint or unsupported cache-purge module is provided.

## Key Directives

- `proxy_cache_path`: Sets cache storage directory, directory hierarchy (`levels`), shared memory keys zone name, and maximum cache size.
- `proxy_cache`: Activates the named cache zone in the `server` or `location` context.
- `proxy_cache_valid 200 10s`: Specifies how long to consider HTTP 200 responses fresh.
- `proxy_cache_lock on`: Protects origins from stampedes; when multiple requests arrive for a new or expired resource, one request populates a new cache entry while others wait, subject to lock timeouts.
- `proxy_cache_use_stale error timeout updating http_500 http_502 ...`: Serves stale cached pages if backend servers are updating or down.
- `proxy_cache_bypass $variable`: Directs Nginx not to look up cached copies when variable evaluates to non-empty or non-zero.
- `proxy_no_cache $variable`: Directs Nginx not to save the origin response to cache.
