# Basic reverse proxy

[Back to reverse proxy](../README.md)

Use [`proxy.conf`](proxy.conf) after reviewing the [root prerequisites](../../README.md). Required modules: `proxy`, `proxy_http`.

- `ProxyRequests Off` disables explicit forward proxying.
- `ProxyPass` forwards all paths to the known HTTP origin.
- `ProxyPassReverse` adjusts origin redirect headers to the frontend URL.

Start your test HTTP application on `127.0.0.1:19001`, load the snippet into an isolated Apache instance, and validate its configuration before starting it. Then request:

```bash
curl --noproxy '*' -i http://127.0.0.1:18081/
```

Expect the origin's status and response body. A redirect pointing to `http://127.0.0.1:19001/` should be rewritten to the proxy's address. Backend HTML links are not rewritten. A missing origin produces a gateway error; check Apache's error log and the origin listener.
