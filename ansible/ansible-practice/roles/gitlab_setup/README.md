Role Name
=========

Deploy GitLab CE using Docker Compose via Ansible.

Requirements
------------

- Docker and Docker Compose installed on the target host
- The `community.docker` Ansible collection

Role Variables
--------------

See `defaults/main/main.yml` for all configurable variables.

| Variable | Default | Description |
|---|---|---|
| `gitlab_image_tag` | `latest` | GitLab Docker image tag |
| `restart_policy` | `always` | Container restart policy |
| `service_dir` | `{{ project_dir }}/gitlab` | Service directory on the remote host |
| `gitlab_domain` | `gitlab.{{ main_domain }}` | GitLab domain name |
| `gitlab_main_url` | `https://{{ gitlab_domain }}` | GitLab external URL |
| `gitlab_config_dir` | `{{ service_dir }}/config` | GitLab config directory |
| `gitlab_logs_dir` | `{{ service_dir }}/logs` | GitLab logs directory |
| `gitlab_data_dir` | `{{ service_dir }}/data` | GitLab data directory |
| `gitlab_hostname` | `gitlab` | Container hostname |
| `gitlab_memory` | `4g` | Container memory limit |
| `gitlab_cpus` | `2` | Container CPU limit |
| `gitlab_root_password` | *(vault)* | GitLab root password |

Secrets (vault)
---------------

Encrypt `defaults/main/vault.yml` with:

    ansible-vault encrypt defaults/main/vault.yml

Then set `gitlab_root_password` to a secure value.

Dependencies
------------

- docker_setup (Docker must be installed on the target host)

Example Playbook
----------------

    - hosts: servers
      roles:
         - role: gitlab_setup

License
-------

MIT

Author Information
------------------

https://github.com/amati-sh
