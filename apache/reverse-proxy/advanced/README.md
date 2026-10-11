# Advanced reverse proxy

[Back to reverse proxy](../README.md)

Use [`proxy.conf`](proxy.conf) after reviewing the [root prerequisites](../../README.md). Requires Apache **2.4.47+** and modules `proxy`, `proxy_http`. No third-party module is needed.

This variant adds:

- A dedicated `/ws/` route using `upgrade=websocket`. The application must implement a WebSocket endpoint; Apache does not create one.
- A 3-second backend connection timeout and a 15-second HTTP response timeout.
- A 60-second WebSocket inactivity timeout; use application heartbeats for longer idle sessions.
- Specific routes before the catch-all `/` mapping, because the first matching `ProxyPass` wins.

Start your application on `127.0.0.1:19001`, load the snippet into an isolated Apache instance, and validate its configuration before starting it.

```bash
curl --noproxy '*' -i http://127.0.0.1:18082/

# Only succeeds if the backend implements /ws/.
curl --noproxy '*' --http1.1 --max-time 3 -i \
  -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
  -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  http://127.0.0.1:18082/ws/
```

For the WebSocket request, expect `101 Switching Protocols` and a valid `Sec-WebSocket-Accept` header. Curl may exit with a timeout after the upgrade because it is not a full WebSocket client. A static HTTP server cannot validate this behavior.

This is not a production TLS configuration or a load-balancing example. Timeout values are teaching defaults, not universal sizing recommendations.
