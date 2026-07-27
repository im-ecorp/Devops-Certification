# Docker Setup Role

Installs Docker Engine from the Docker APT repository and manages
`/etc/docker/daemon.json`.

## What this role does

The role runs these stages in order:

1. Installs required system packages.
2. Downloads the Docker repository GPG key.
3. Configures either the official Docker repository or a Nexus mirror.
4. Removes distribution-provided `docker` and `docker-engine` packages.
5. Installs Docker Engine, containerd, Buildx, and Compose.
6. Generates `/etc/docker/daemon.json`.
7. Enables and restarts Docker and containerd when required.

## Requirements

- Debian or Ubuntu
- APT package manager
- Root access through Ansible privilege escalation (`become`)
- Network access to the selected Docker repository and GPG-key URL
- Ansible facts enabled

This role has no Ansible Galaxy role dependencies.

## Basic usage

```yaml
---
- name: Install and configure Docker
  hosts: docker_hosts
  become: true

  roles:
    - role: docker_setup
```

Run the playbook:

```bash
ansible-playbook -i inventory/hosts.yml playbooks/docker.yml
```

## Repository configuration

The official Docker repository is used by default:

```yaml
use_nexus: false
```

To use the configured Nexus repository:

```yaml
use_nexus: true
```

Repository defaults:

```yaml
docker_repo:
  channel:
    stable_enabled: true
    test_enabled: false
    nightly_enabled: false
  nexus_repo_urls:
    debian: "https://repo.mecan.ir/repository/debian-docker/"
    ubuntu: "https://repo.mecan.ir/repository/ubuntu-docker/"
  nexus_gpg_urls:
    debian: "https://repo.mecan.ir/repository/debian-docker/gpg"
    ubuntu: "https://repo.mecan.ir/repository/ubuntu-docker/gpg"
  official_repo_url: "https://download.docker.com/linux/{{ ansible_facts.distribution | lower }}"
  official_gpg_url: "https://download.docker.com/linux/{{ ansible_facts.distribution | lower }}/gpg"

docker_gpg_key_path: /etc/apt/keyrings/docker.asc
```

The generated APT entry uses `signed-by={{ docker_gpg_key_path }}`. The key
served by the selected `gpg_url` must match the key used to sign that
repository.

## Docker daemon configuration

Each section can be enabled or disabled independently. Enabled sections are
written to `/etc/docker/daemon.json` in this order:

1. Proxy
2. Logging options
3. Registry mirror
4. Insecure registry
5. Experimental mode
6. Live restore

Default configuration:

```yaml
docker_config:
  proxy:
    enabled: true
    http_proxy: "http://127.0.0.1:8090"
    https_proxy: "{{ docker_config.proxy.http_proxy }}"
    no_proxy: "hub.mecan.ir, 127.0.0.1/8, localhost"

  logging:
    enabled: true
    labels: "{{ inventory_hostname }}"
    max_file: "5"
    max_size: "100M"

  mirror_registry:
    enabled: true
    urls: "https://hub.hamdocker.ir"

  insecure_registry:
    enabled: true
    urls: "https://test.k8sforfun.com"

  experimental:
    enabled: true

  live_restore:
    enabled: true
```

The template removes an `http://` or `https://` prefix from the insecure
registry value because Docker expects a registry host, optionally followed by
a port.

If there is no proxy listening on `127.0.0.1:8090`, disable the proxy:

```yaml
docker_config:
  proxy:
    enabled: false
```

When overriding `docker_config`, define every nested section needed by the
template. Ansible replaces dictionaries at different variable-precedence
levels unless hash merging has been explicitly enabled.

## Main variables

| Variable | Purpose |
| --- | --- |
| `docker_dependencies` | Packages installed before configuring Docker |
| `docker_packages` | Docker packages installed by the role |
| `use_nexus` | Selects Nexus (`true`) or the official repository (`false`) |
| `docker_repo` | Repository URLs, GPG URLs, and channel settings |
| `repo_url` | Resolved repository URL |
| `gpg_url` | Resolved GPG-key URL |
| `docker_gpg_key_path` | Destination of the repository signing key |
| `docker_config` | Settings used to generate `daemon.json` |
| `docker_apt_arch` | Optional APT architecture; defaults to `amd64` |

See [`defaults/main.yml`](defaults/main.yml) for the complete package lists and
default values.

## Tags

Run the entire role:

```bash
ansible-playbook -i inventory/hosts.yml playbooks/docker.yml --tags docker
```

Run one stage:

```bash
ansible-playbook -i inventory/hosts.yml playbooks/docker.yml --tags docker_preparing
ansible-playbook -i inventory/hosts.yml playbooks/docker.yml --tags docker_installation
ansible-playbook -i inventory/hosts.yml playbooks/docker.yml --tags docker_configuration
```

## Example with overrides

```yaml
---
- name: Install Docker using Nexus
  hosts: docker_hosts
  become: true

  vars:
    use_nexus: true

    docker_config:
      proxy:
        enabled: false
        http_proxy: ""
        https_proxy: ""
        no_proxy: ""

      logging:
        enabled: true
        labels: "{{ inventory_hostname }}"
        max_file: "3"
        max_size: "50M"

      mirror_registry:
        enabled: true
        urls: "https://hub.hamdocker.ir"

      insecure_registry:
        enabled: false
        urls: ""

      experimental:
        enabled: false

      live_restore:
        enabled: true

  roles:
    - role: docker_setup
```

## Troubleshooting

Validate the generated Docker configuration:

```bash
sudo dockerd --validate --config-file=/etc/docker/daemon.json
```

Inspect Docker startup errors:

```bash
sudo systemctl status docker.service
sudo journalctl -xeu docker.service
```

Check the configured APT repository:

```bash
cat /etc/apt/sources.list.d/docker.list
```

If APT reports a missing signing key, confirm that the configured GPG URL
serves the key that signed the selected repository.
