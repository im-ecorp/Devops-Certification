# Authelia Setup Role

This role deploys Authelia behind Traefik using Docker Compose.

## Role Variables

| Variable | Description | Default |
| -------- | ----------- | ------- |
| `authelia_image_tag` | Authelia Docker image version | `4.38.16` |
| `restart_policy` | Docker container restart policy | `always` |
| `service_dir` | Path to service deployment | `{{ project_dir }}/authelia` |
| `authelia_main_domain` | The FQDN for the Authelia instance | `auth.{{ main_domain }}` |

## Example Playbook

```yaml
- hosts: all
  become: true
  roles:
    - authelia_setup
```
