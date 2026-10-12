# DevOps Certification — Infrastructure Practice

Hands-on infrastructure practice with independent **Terraform**, **Nginx**, **Apache**, and **Nexus** labs, plus **Ansible** service automation and a **Vagrant** Debian cluster. Start with a lab README; the Ansible inventory is for separately configured hosts, not the Vagrant cluster.

## Repository Structure

| Directory | Purpose |
|---|---|
| [`ansible/ansible-practice/`](ansible/ansible-practice/) | Ansible inventory, 24 playbooks, and 24 roles for host preparation and service deployment |
| [`ansible/ansible-gui/awx/`](ansible/ansible-gui/awx/README.md) | Manual AWX-on-Kind deployment guide |
| [`terraform/`](terraform/README.md) | Independent language, Docker, Kubernetes, and Cloudflare infrastructure-as-code labs |
| [`nginx/`](nginx/README.md) | Seven loopback-only reverse/forward proxy, caching, and load-balancing configs |
| [`apache/`](apache/README.md) | Loopback-only reverse and forward proxy virtual-host snippets |
| [`nexus/`](nexus/README.md) | Standalone Nexus Compose alternatives with Traefik or Nginx |
| [`podman/`](podman/README.md) | Brief rootless installation/configuration guide and a local [Nginx example](podman/nginx/README.md) |
| [`vagrant/`](vagrant/Vagrantfile) | Three-node Debian 13 VirtualBox cluster |

## Tech Stack

| Area | Technology |
|---|---|
| **Local VMs** | Vagrant + VirtualBox; three Debian 13 nodes |
| **Infrastructure as code** | Terraform with Docker, Kubernetes, and Cloudflare provider labs |
| **Configuration management** | Ansible playbooks and roles for provisioning, hardening, and services |
| **Containers and routing** | Docker Engine, Docker Compose, Portainer, Traefik, Nginx, Apache |
| **Identity and services** | Authelia, Vaultwarden, GitLab CE, Nexus, AWX, Docmost, docker-mailserver + Roundcube |
| **Object storage** | MinIO, RustFS, SeaweedFS |
| **AI tooling** | 9router, OmniRoute, Hermes WebUI and agent update, DeepSeek Harness |

## Ansible Overview

The checked-in `ecorp` inventory contains remote hosts; it is **not a safe local default**. Review host addresses, SSH settings, group variables, and per-role defaults before using it. Some roles load encrypted Ansible Vault files. The project config expects a local vault password file and disables SSH host-key checking; review those settings before connecting.

**Playbooks:**

| Playbook | Description |
|---|---|
| `preparing.yml` | Server bootstrap — packages, iptables, fail2ban, Lynis |
| `docker.yml` | Docker Engine installation |
| `nginx.yml` | Nginx installation and site configuration |
| `hardening.yml` | OS + SSH security hardening (DevSec) |
| `python.yml` | Python 3 setup |
| `maintenance.yml` | OS updates + Docker/K8s cleanup |
| `reboot.yml` | Rolling reboot with wait-for-return |
| `traefik.yml` | Traefik reverse proxy deployment |
| `authelia.yml` | Authelia SSO with PostgreSQL + Redis |
| `vaultwarden.yml` | Vaultwarden password manager deployment |
| `portainer.yml` | Portainer container management UI |
| `nexus.yml` | Nexus Repository OSS + API configuration |
| `gitlab.yml` | GitLab CE + optional runner, backups and email |
| `awx.yml` | AWX on Kind (Kubernetes-in-Docker) |
| `minio.yml` | MinIO S3-compatible storage |
| `rustfs.yml` | RustFS S3-compatible object storage |
| `seaweedfs.yml` | SeaweedFS distributed storage |
| `docmost.yml` | Docmost wiki with PostgreSQL + Redis |
| `mailserver.yml` | docker-mailserver with DKIM + Roundcube webmail |
| `9router.yml` | 9router LLM router (+ Headroom) |
| `omniroute.yml` | OmniRoute LLM router with Redis |
| `hermes-web-ui.yml` | Hermes WebUI for the Hermes Agent |
| `hermes-update.yml` | Update Hermes Agent and restart its gateway |
| `deepseek.yml` | DeepSeek Harness (`dsh`) web UI |

### Role conventions

Layouts vary by role:

- Defaults live in `defaults/main.yml` or `defaults/main/`; encrypted `vault.yml` files hold secrets where used.
- Container roles use Compose files and Jinja templates, often with a rendered `.env`; inspect each role's defaults and tasks for its dependencies.
- Many container services use Traefik labels and the shared `web_net` network. AWX, host Nginx, mail, and maintenance roles have different requirements.
- Review tags, handlers, exposed ports, persistent storage, and health checks before running a playbook. These examples are not a production security baseline.

## Getting Started

1. Clone the repository:

   ```bash
   git clone https://github.com/im-ecorp/Devops-Certification.git
   cd Devops-Certification
   ```

2. Choose one independent practice area:

   | Start here | Requirements and scope |
   |---|---|
   | [Terraform language](terraform/learn-terraform/terraform-language/README.md) | Terraform; no real servers required |
   | [Terraform provider labs](terraform/README.md#3-practice-labs) | Terraform 1.7+; Docker, a Kubernetes practice cluster, or a scoped Cloudflare token as applicable |
   | [Nginx labs](nginx/README.md#quick-start) | Nginx 1.26.3+, Python 3.9+, curl, and free loopback ports |
   | [Apache labs](apache/README.md) | Apache 2.4; 2.4.47+ recommended for advanced WebSocket proxying; a local origin server |
   | [Standalone Nexus](nexus/README.md) | Docker Compose; review the chosen proxy, certificates, and volume ownership |

3. For optional local VMs, install Vagrant and VirtualBox first, then:

   ```bash
   cd vagrant
   vagrant validate
   vagrant up
   vagrant ssh vmbox11
   ```

   The `bento/debian-13` cluster defines `vmbox11`, `vmbox12`, and `vmbox13` at `192.168.56.111–113`, each with 1 CPU and 1 GiB RAM. Check host capacity and network conflicts before startup. To use these VMs with Ansible, create a separate local inventory using connection details from `vagrant ssh-config`; do not reuse the remote inventory unchanged.

4. For Ansible, start from the repository root with Ansible installed:

   ```bash
   cd ansible/ansible-practice
   ansible-galaxy collection install -r requirements.yml
   ansible-inventory -i inventory/hosts.yml --graph
   ansible-playbook -i inventory/hosts.yml playbooks/preparing.yml --list-hosts
   ansible-playbook -i inventory/hosts.yml playbooks/preparing.yml --syntax-check
   ```

   Review `ansible.cfg` first: it expects `~/.ansible/vault.pass`, an SSH key, and a writable Ansible log path. Supply your own vault access securely; never commit credentials. The inventory and syntax commands above do not deploy services. Most playbooks target `all`, so choose a reviewed inventory and explicit host limit before execution.

**Safety:** Ansible deployments, Vagrant startup, Terraform apply, and Compose startup change infrastructure. Review the selected lab instructions, ports, resource ownership, and backups first. Keep secrets, local environment files, Terraform state, and saved plans out of Git. Never destroy resources or remove persistent volumes as routine cleanup without reviewing the impact.

## License

[MIT](LICENSE)
