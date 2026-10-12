# Portainer: a Docker administration UI

[Back to Compose examples](../README.md)

Read [compose.yaml](compose.yaml). One service runs Portainer Community Edition. A named volume stores its users/settings, and a bind mount exposes the local Docker Engine API socket to Portainer. Compose automatically creates a default bridge network because no network is explicitly declared. Only HTTPS port `9443` is published, on host loopback. Ports `9000` (legacy HTTP) and `8000` (Edge agent tunnel) are unnecessary for this example.

**Security boundary:** Access to `/var/run/docker.sock` gives Portainer administrative control of the Docker host and its containers, effectively root-level power. Use a trusted practice machine and a strong admin password. Mounting the socket with `:ro` would not make Docker API operations read-only. Do not expose this UI publicly or mount the socket into untrusted applications.

## Start and initialize

Requires a local **rootful Linux Docker Engine** with `/var/run/docker.sock`, or a Docker Desktop Linux-container environment exposing that socket. Rootless Docker, a remote Docker context, and SELinux need separate configuration; this file does not add `privileged: true` or disable host protections as a workaround.

From the repository root:

```bash
cd docker/compose/portainer
docker compose config --quiet
docker compose up -d
docker compose ps
docker compose logs --tail=50 portainer
```

Open **https://127.0.0.1:9443** promptly. Expect a self-signed certificate warning on this local lab; verify the local address before accepting it. Create an admin account with a strong unique password, then select the local Docker environment (often through **Get Started**). If initial setup times out, restart the service and complete setup immediately:

```bash
docker compose restart portainer
```

You should see containers from the same Docker Engine in the UI, including this Portainer service. Do not change or delete existing host workloads while exploring. This example is not isolated from other projects: Portainer can manage everything that daemon permits.

For a **local lab connectivity check only**:

```bash
curl -k -I https://127.0.0.1:9443/
```

`-k` bypasses certificate verification for this self-signed local endpoint; it is not a production TLS check. An HTTP response checks reachability, not successful admin setup or permission isolation. Replace the self-signed certificate with trusted TLS before any approved remote access.

## Understand the mounts and stop

- `/var/run/docker.sock:/var/run/docker.sock` is a host bind mount, not stored Portainer data.
- `portainer-data:/data` is a project-scoped named volume. It retains admin accounts, settings, and environment definitions when the service is recreated.
- `restart: unless-stopped` restarts the process after an unexpected exit/reboot, but respects a manual stop.

```bash
docker compose stop
docker compose start
# Removes the container/network; keeps portainer-data:
docker compose down
```

Running `up -d` again should keep your account/settings. Do not use `down -v` or delete data to reset an admin password. The Portainer volume does **not** back up the managed containers or their databases. Keep source-managed labs under their own Compose CLI control; avoid editing the same project through both a Portainer stack editor and local files.

**Reference:** [Official Portainer installation guide](https://docs.portainer.io/start/install-ce/server/docker/linux). The image is pinned to a release tag for readability; pin its tested digest when exact repeatability matters.
