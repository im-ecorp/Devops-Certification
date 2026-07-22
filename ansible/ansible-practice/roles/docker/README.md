# Docker role

Installs Docker Engine CE on Debian or Ubuntu from Docker's official apt
repository. The role installs the Engine, CLI, containerd, Buildx plugin, and
Compose plugin, then ensures the Docker service is enabled and running.

The implementation intentionally follows a short, explicit sequence:

1. Remove package names that conflict with Docker CE.
2. Install the apt repository prerequisites.
3. Configure Docker's signed apt repository.
4. Install the official Docker packages.
5. Apply optional daemon configuration and group membership.
6. Verify the daemon and Compose plugin.

## Variables

The defaults are documented in `defaults/main.yml`. Common overrides include:

```yaml
docker_users:
  - vagrant

docker_daemon_options:
  log-driver: json-file
  log-opts:
    max-size: 100m
    max-file: "3"
```

Set `docker_packages_state: latest` when you intentionally want an Ansible run
to upgrade the installed Docker packages. The safer default is `present`.

Membership in the `docker` group grants root-equivalent access. A user may need
to log out and back in before new group membership is visible in an existing
shell.
