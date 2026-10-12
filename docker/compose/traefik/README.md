# Traefik: proxy and backend in one Compose file

[Back to Compose examples](../README.md)

Read [compose.yaml](compose.yaml). Traefik accepts HTTP on host port `8088`; it forwards requests to the `whoami` service, a small diagnostic HTTP server. Both services share `proxy-net`. The backend has no published host port.

## Start and test

Requires **Docker Compose v2.23.1+** because `configs.content` embeds the routing YAML directly in the Compose file. No domain, certificate, external routing file, or Docker socket is required.

From the repository root:

```bash
cd docker/compose/traefik
docker compose version
docker compose config --quiet
docker compose up -d
docker compose ps
curl http://127.0.0.1:8088/
```

The response should contain the backend's hostname, IP addresses, and request headers. Open **http://127.0.0.1:8088** in a browser for the same output. A short `502` during startup can happen because `depends_on` here only starts the backend first; it does not wait for HTTP readiness. For persistent errors:

```bash
docker compose logs --tail=50 traefik whoami
```

## Understand the two kinds of configuration

1. **Compose `services`:** Defines the two containers, their images, network attachments, proxy port, and configuration mount.
2. **Traefik static configuration (`command`):** Declares the `web` entry point listening on container port 80 and enables the file provider. The dashboard is disabled.
3. **Traefik dynamic configuration (`configs.routes.content`):** Declares a router named `demo`. `PathPrefix(`/`)` matches every request arriving at the web entry point. The router uses Traefik service `demo`, whose load balancer forwards to `http://whoami:80`.

A Traefik **service** here is a routing backend, not the same concept as a Compose **service**. Compose mounts the inline text as `/etc/traefik/dynamic.yaml`; Traefik reads it. The file provider avoids mounting the Docker socket or teaching Docker-provider labels in this first example. Compose parsing does not validate Traefik's routing semantics; the real HTTP request above does.

Try changing the router rule to `PathPrefix(`/hello`)`, then apply it:

```bash
docker compose config --quiet
docker compose up -d --force-recreate traefik
curl http://127.0.0.1:8088/hello
curl -i http://127.0.0.1:8088/
```

`/hello` should still show backend details; `/` should return Traefik's `404` because no router matches. Recreating the proxy explicitly ensures it reads the new inline config. Do not rely on file watching to propagate edits to an inline Compose config; this command briefly interrupts this lab's proxy.

## Stop

```bash
docker compose stop
docker compose start
docker compose down
```

This example has no persistent application state and needs no named volume. It demonstrates HTTP forwarding, not HTTPS, authentication, automatic Docker discovery, or production ingress. Keep the port on loopback and do not expose the diagnostic backend publicly.

**References:** [Compose configs](https://docs.docker.com/reference/compose-file/configs/) · [Traefik file provider](https://doc.traefik.io/traefik/reference/install-configuration/providers/others/file/) · [Whoami](https://github.com/traefik/whoami).
