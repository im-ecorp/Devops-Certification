# Learn Docker Compose

`compose/` uses one standalone, commented `compose.yaml` per example. Run each from its own directory; Compose creates a separate project for each folder. These examples need Docker Engine/Desktop with the **Docker Compose v2 plugin** (`docker compose`, not `docker-compose`). They use prebuilt images—no Dockerfiles, application source, or external YAML files.

| Example | What it teaches | Local address |
| --- | --- | --- |
| [WordPress](wordpress/README.md) | Two services, credentials, database readiness, private network, named volumes | http://127.0.0.1:8087 |
| [Traefik](traefik/README.md) | HTTP reverse proxy, entry point, router, service, embedded Compose config | http://127.0.0.1:8088 |
| [Portainer](portainer/README.md) | One-service admin UI, bind mount versus named volume | https://127.0.0.1:9443 |

## Read a Compose file

- `services` defines containers; each entry's name is also its DNS name on a shared Compose network.
- `image` selects a registry image. A versioned tag is used here instead of `latest`; tags can still change, so pin a tested digest for reproducible deployments.
- `environment` configures the image; `${VAR:?message}` makes a host variable mandatory before Compose can start. A `.env` file is optional, not required by these examples. Do not put passwords in tracked YAML or command arguments.
- `ports` maps `HOST_IP:HOST_PORT:CONTAINER_PORT`. `127.0.0.1` keeps these labs local to the Docker host; Docker Desktop users can open the URL on their desktop. Do not assume a remote server's `127.0.0.1` is accessible from your laptop.
- `volumes` persists data; a named volume belongs to the Compose project and survives `docker compose down` unless `-v` is added. A bind mount points to an existing host resource such as Portainer's Docker socket.
- `networks` defines container connectivity. Containers do not need published host ports to talk to each other on a shared network.
- `depends_on` with `service_healthy` waits for the declared health check, not for every application-level migration or setup task.
- `configs` in the Traefik example mounts inline configuration as a file. It requires Docker Compose **v2.23.1+**. Plain local Compose configs are not a secret store.

Open an example's README, then, **in that example's directory**, use `docker compose config --quiet` to validate and `docker compose up -d` to start. Inspect with `docker compose ps` and `docker compose logs`. `docker compose down` stops/removes that example's containers and network but keeps its named volumes. **Do not use `down -v`** on data you want to keep. A named volume is not an independent backup.

These are single-host learning labs, not production-ready services. Loopback binding, local credentials, plain HTTP (except Portainer's self-signed HTTPS), and local volumes need different treatment before public exposure. Portainer has Docker-host administrative power because it mounts the Docker socket. Running all examples together uses distinct host ports, but each project consumes resources and Portainer can see the other projects on the same daemon.
