# Reverse proxy

A reverse proxy fronts a known application. Clients request the proxy URL; Apache forwards requests to the configured origin. `ProxyRequests Off` prevents explicit forward-proxy operation and must remain off in both variants.

| Approach | Purpose | Listener |
|---|---|---|
| [Basic](basic/README.md) | HTTP forwarding and redirect-header rewriting | `127.0.0.1:18081` |
| [Advanced](advanced/README.md) | Separate WebSocket route, connection timeout, response timeout | `127.0.0.1:18082` |

Both use an origin on `127.0.0.1:19001`. `ProxyPassReverse` rewrites backend redirect headers, not links embedded in HTML. Configure the application's public URL separately. These examples do not preserve arbitrary client-supplied Host headers or claim to sanitize all forwarded headers; production apps must trust only reviewed proxy hops.

Read [prerequisites and validation](../README.md) before loading either virtual-host snippet.
