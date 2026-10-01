# DevOps Certification — Infrastructure Automation Lab

A hands-on practice environment for DevOps certification, demonstrating end-to-end infrastructure automation using **Ansible**, **Docker**, **Traefik**, **Nginx**, **Vagrant**, and supporting DevOps tools (GitLab, Nexus, MinIO, SeaweedFS, AWX, Authelia, mail server, AI agent tooling).

## Repository Structure

| Directory | Purpose |
|---|---|
| [`ansible/`](ansible/) | Ansible automation — playbooks, roles, inventory, and AWX deployment guide |
| `ansible/ansible-practice/` | Production-oriented Ansible project with 22 playbooks and 23 roles |
| `ansible/ansible-gui/awx/` | Manual guide for deploying AWX on Kind |
| [`nginx/`](nginx/) | Nginx server configs — reverse proxy, TLS, PHP-FPM, basic auth |
| [`vagrant/`](vagrant/) | Vagrantfile for a 3-node Debian VM cluster |

## Tech Stack

| Layer | Technology |
|---|---|
| **Local VMs** | Vagrant + VirtualBox (3-node Debian cluster) |
| **Config Management** | Ansible — provisioning, hardening, service deployment |
| **Security Hardening** | DevSec Ansible roles (OS kernel, PAM, SSH, auditd, sysctl, SUID, fail2ban, Lynis) |
| **Container Host** | Docker Engine + Docker Compose (automated via Ansible), Portainer |
| **Reverse Proxy** | Traefik (edge router, Let's Encrypt TLS) + Nginx (legacy/PHP hosting) |
| **Identity** | Authelia (SSO / 2FA) |
| **DevOps Services** | GitLab CE, Sonatype Nexus, AWX (Ansible GUI) |
| **Object Storage** | MinIO, RustFS, SeaweedFS (S3-compatible) |
| **Collaboration & Mail** | Docmost (wiki), docker-mailserver + Roundcube |
| **AI Tooling** | 9router, OmniRoute (LLM routers), Hermes Agent + WebUI, DeepSeek Harness |

## Ansible Overview

Multi-region inventory (`ecorp`) spanning Iran and EU hosts, with `ProxyJump` bastion access. Secrets are kept in per-role `ansible-vault` files.

**Playbooks:**

| Playbook | Description |
|---|---|
| `preparing.yml` | Server bootstrap — packages, iptables, fail2ban, Lynis |
| `docker.yml` | Docker Engine installation |
| `hardening.yml` | OS + SSH security hardening (DevSec) |
| `python.yml` | Python 3 setup |
| `maintenance.yml` | OS updates + Docker/K8s cleanup |
| `reboot.yml` | Rolling reboot with wait-for-return |
| `traefik.yml` | Traefik reverse proxy deployment |
| `authelia.yml` | Authelia SSO with PostgreSQL + Redis |
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

Every service role follows the same layout and rules:

- Uses the **published upstream image unchanged**, pinned by a tag in `defaults/` — no custom Dockerfiles or `build:` steps.
- Values flow `defaults/main/main.yml` (or `vault.yml`) → `templates/.env.j2` → `${var}` in Docker Compose.
- Services are exposed only through **Traefik Docker labels** on their own container (`web` / `web-secure` entrypoints, `myproduction` cert resolver, shared `web_net` network). Only `traefik_setup` manages Traefik's own config.
- Task order: networks → service dir → compose + `.env` (with restart handler) → pull → deploy → health check.

## Getting Started

```bash
# Clone the repo
git clone https://github.com/<your-org>/Devops-Certification.git
cd Devops-Certification

# Spin up local test VMs
cd vagrant && vagrant up

# Install required collections
cd ../ansible/ansible-practice
ansible-galaxy collection install -r requirements.yml

# Run Ansible against local VMs
ansible-playbook -i inventory/hosts.yml playbooks/preparing.yml
```

## License

MIT
