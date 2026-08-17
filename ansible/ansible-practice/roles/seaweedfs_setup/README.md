SeaweedFS Setup Role
====================

An Ansible role to deploy SeaweedFS (Master, Volume, and S3-compatible server) using Docker Compose and Traefik reverse proxy integration.

Role Structure
--------------

- `defaults/main/`
  - `main.yml`: Default non-sensitive variables (image tags, domain, service directory).
  - `vault.yml`: Vault variables (encrypted/sensitive configurations).
- `files/`
  - `docker-compose.yml`: SeaweedFS Docker Compose definition with Traefik router labels and networks.
- `handlers/`
  - `main.yml`: Handlers for restarting the SeaweedFS stack when config changes.
- `tasks/`
  - `main.yml`: Entry point importing installation task file.
  - `installation.yml`: Tasks for network creation, directory setup, copying Compose file, templating `.env`, pulling images, and starting the Compose stack.
- `templates/`
  - `.env.j2`: Template for environment variables used by Docker Compose.

Role Variables
--------------

Available variables with defaults are listed in `defaults/main/main.yml`:

- `seaweedfs_image_tag`: Docker image tag (default: `"3.75"`).
- `restart_policy`: Container restart policy (default: `"always"`).
- `service_dir`: Target directory on the remote host (default: `"{{ project_dir }}/seaweedfs"`).
- `seaweedfs_s3_domain`: S3 endpoint domain (default: `"s3.{{ main_domain }}"`).
- `seaweedfs_master_domain`: Master UI/API domain (default: `"seaweedfs-master.{{ main_domain }}"`).
- `seaweedfs_volume_domain`: Volume server domain (default: `"seaweedfs-volume.{{ main_domain }}"`).
- `seaweedfs_filer_domain`: Filer UI/API domain (default: `"seaweedfs-filer.{{ main_domain }}"`).
- `seaweedfs_webdav_domain`: WebDAV domain (default: `"seaweedfs-webdav.{{ main_domain }}"`).
- `seaweedfs_admin_domain`: Admin UI domain (default: `"seaweedfs-admin.{{ main_domain }}"`).

Endpoints
---------

The single SeaweedFS server container enables and routes the following endpoints:

- S3: port `8333`
- Master UI/API: port `9333`
- Volume server: port `9340`
- Filer UI/API: port `8888`
- WebDAV: port `7333`

The separate `seaweedfs-admin` container provides the Admin UI on port `23646`. The role exposes all endpoints through Traefik host-based routers and does not publish host ports, matching the repository's reverse-proxy convention. For direct localhost access, add explicit `ports` mappings to the Compose service.

Tags
----

- `install_seaweedfs` / `setup_seaweedfs`: Main setup tags.
- `preparing`: Directory and file setup tasks.
- `docker`: Network management.
- `pull`: Image pulling task.
- `deploy`: Stack deployment task.

Example Playbook
----------------

```yaml
- name: Deploy SeaweedFS
  hosts: all
  become: true
  roles:
    - seaweedfs_setup
```
