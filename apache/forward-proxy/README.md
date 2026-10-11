# Forward proxy

[Back to Apache labs](../README.md)

A forward proxy is selected by the client to reach an origin. This topic has **one restricted HTTP-only approach**, so its files live directly here rather than in Basic/Advanced directories.

Use [`proxy.conf`](proxy.conf) with `proxy` and `proxy_http` loaded. Keep `proxy_connect` disabled for this lab. Read the [root prerequisites](../README.md) before loading the virtual-host snippet.

## Access policy

- Bind only to `127.0.0.1:18083`.
- `ProxyRequests On` enables explicit proxy requests only in this virtual host.
- Deny all destinations by default.
- Allow only local clients requesting `http://127.0.0.1:19001/` and its paths.
- Deny CONNECT and other unlisted methods. HTTPS tunneling is deliberately not configured.

This is a local teaching proxy, **not** an internet proxy. Do not change the listener to `0.0.0.0` or replace the deny policy with `Require all granted`. Adding HTTPS CONNECT requires a separate reviewed destination/port/access policy; enabling the module alone is not sufficient.

## Requests

Start your local HTTP origin on `127.0.0.1:19001`, load the snippet into an isolated Apache instance, and validate its configuration before starting it. Explicitly clear curl's proxy bypass list because localhost is commonly excluded by `NO_PROXY`.

```bash
# Allowed; expect the local origin's response.
curl --noproxy '' --proxy http://127.0.0.1:18083 \
  -i http://127.0.0.1:19001/

# Forbidden destination; expect HTTP 403 without contacting it.
curl --noproxy '' --proxy http://127.0.0.1:18083 \
  -i http://example.com/

# Forbidden HTTPS CONNECT; expect a non-success response.
curl --noproxy '' --proxy http://127.0.0.1:18083 \
  --max-time 5 -I https://example.com/
```

`ProxyVia On` adds a `Via` header. It is not an anonymization guarantee. The destination allowlist is a deliberately narrow lab policy, not a general-purpose defense against SSRF or DNS rebinding for arbitrary domains.
