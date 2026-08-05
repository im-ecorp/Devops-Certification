# DevOps Certification — Infrastructure Automation Lab

A hands-on practice environment for DevOps certification, demonstrating end-to-end infrastructure automation using **Ansible**, **Docker**, **Traefik**, **Nginx**, **Vagrant**, and supporting DevOps tools (GitLab, Nexus, MinIO, AWX, RustFS).

## Repository Structure

| Directory | Purpose |
|---|---|
| [`ansible/`](ansible/) | Ansible automation — playbooks, roles, inventory, and AWX deployment guide |
| `ansible/ansible-practice/` | Production-oriented Ansible project with 11 playbooks and 13 roles |
| `ansible/ansible-gui/awx/` | Manual guide for deploying AWX on Kind |
| [`nginx/`](nginx/) | Nginx server configs — reverse proxy, TLS, PHP-FPM, basic auth |
| [`vagrant/`](vagrant/) | Vagrantfile for a 3-node Debian VM cluster |

## Tech Stack

| Layer | Technology |
|---|---|
| **Local VMs** | Vagrant + VirtualBox (3-node Debian cluster) |
| **Config Management** | Ansible — provisioning, hardening, service deployment |
| **Security Hardening** | DevSec Ansible roles (OS kernel, PAM, SSH, auditd, sysctl, SUID, fail2ban, Lynis) |
| **Container Host** | Docker Engine (automated via Ansible) |
| **Reverse Proxy** | Traefik (edge router) + Nginx (legacy/PHP hosting) |
| **DevOps Services** | GitLab CE, Sonatype Nexus, MinIO (S3), AWX (Ansible GUI) |
| **Encrypted FS** | RustFS (FUSE-based) |

## Ansible Overview

Multi-region inventory (`ecorp`) spanning Iran and EU hosts, with `ProxyJump` bastion access.

**Playbooks:**

| Playbook | Description |
|---|---|
| `preparing.yml` | Server bootstrap — packages, iptables, fail2ban, Lynis |
| `docker.yml` | Docker Engine installation |
| `hardening.yml` | OS + SSH security hardening (DevSec) |
| `python.yml` | Python 3 setup |
| `traefik.yml` | Traefik reverse proxy deployment |
| `nexus.yml` | Nexus Repository OSS + API configuration |
| `gitlab.yml` | GitLab CE + optional runner |
| `minio.yml` | MinIO S3-compatible storage |
| `rustfs.yml` | RustFS encrypted filesystem |
| `awx.yml` | AWX on Kind (Kubernetes-in-Docker) |
| `maintenance.yml` | OS updates + Docker/K8s cleanup |

## Getting Started

```bash
# Clone the repo
git clone https://github.com/<your-org>/Devops-Certification.git
cd Devops-Certification

# Spin up local test VMs
cd vagrant && vagrant up

# Run Ansible against local VMs
cd ../ansible/ansible-practice
ansible-playbook -i inventory/hosts.yml playbooks/preparing.yml
```

## License

MIT