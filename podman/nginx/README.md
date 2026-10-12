# Nginx with rootless Podman

[Back to Podman setup](../README.md). Run this on a native Linux host **as your normal user** after the rootless checks pass. Ensure port `8090` is free. The image is the official Nginx image from Docker Hub; the tag selects its 1.28 Alpine series. Tags can change over time; pin a tested digest if exact repeatability is required.

## Run and test

```bash
podman pull docker.io/library/nginx:1.28-alpine
podman run -d --name podman-nginx --publish 127.0.0.1:8090:80 docker.io/library/nginx:1.28-alpine
podman ps
curl -I http://127.0.0.1:8090/
```

Expect `HTTP/1.1 200 OK` and the default Nginx welcome page at <http://127.0.0.1:8090/>. The `127.0.0.1` binding keeps it accessible only from this host. If using SSH to a remote machine, use a reviewed SSH port forward rather than publishing the demo publicly. Host port `8090` maps to container port `80`; rootless users can publish an unprivileged host port. `podman run -d` keeps the container in the background, and `--name` gives it a stable local name.

If the container exits or HTTP fails, inspect its state and output:

```bash
podman ps -a
podman logs podman-nginx
podman port podman-nginx
```

Try the lifecycle commands:

```bash
podman stop podman-nginx
podman start podman-nginx
curl -I http://127.0.0.1:8090/
```

`stop` leaves the container available for `start`; the default page is bundled in the image. This exercise has no named volume or user data.

## Cleanup

After the exercise, **if you no longer need this particular practice container**, remove it by its exact name:

```bash
podman stop podman-nginx
podman rm podman-nginx
```

These commands remove only that container, not other containers or images. Skip cleanup if you intend to keep it. Do not use `podman system prune` as a shortcut: it can affect unrelated workloads. For a real server, replace the sample page, add persistent configuration and appropriate TLS, and consider a user-systemd Quadlet for restart on boot. This is a local HTTP demonstration, not a production deployment.

**Reference:** [Podman run options](https://docs.podman.io/en/latest/markdown/podman-run.1.html).
