# Ansible practice project

This project contains reusable Ansible roles, environment-specific inventory,
and playbooks for preparing hosts and deploying services. Sonatype Nexus
Repository OSS is deployed in Docker behind an existing Traefik instance.

## Layout

- `ansible.cfg` defines the default practice inventory and local role path.
- `inventory/hosts.yml` contains inventory topology and host connection values.
- `inventory/group_vars/all/` contains variables applied to every inventory host.
- `playbooks/site.yml` is the complete project entry point.
- `playbooks/prepare.yml` applies the common host preparation role.
- `playbooks/configure-nginx.yml` invokes the Nginx role for web servers.
- `playbooks/deploy-nexus.yml` installs Docker Engine and deploys Nexus.
- `roles/` contains the `preparing`, `nginx`, `docker`, and `nexus` roles.

## Validate

Review the practice inventory and variables before running automation:

- `inventory/hosts.yml`
- `inventory/group_vars/`

Validate locally without connecting to managed hosts:

```bash
ansible-inventory --graph
ansible-playbook --syntax-check playbooks/site.yml
```

## Run

Run all playbooks:

```bash
ansible-playbook playbooks/site.yml
```

Run only the Nexus deployment:

```bash
ansible-playbook playbooks/deploy-nexus.yml
```

The Nexus role keeps persistent data in `/opt/nexus/nexus-data` by default and
does not publish port 8081 unless configured to do so. Traffic reaches Nexus
through Traefik. Rotate the generated initial administrator password after the
first sign-in, and store all managed secrets with Ansible Vault rather than as
plaintext repository files.
