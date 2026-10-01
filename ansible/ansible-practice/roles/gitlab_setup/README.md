Role Name
=========

Deploy GitLab CE (Omnibus image) with Docker Compose via Ansible, behind
Traefik, with the container registry, outgoing email, daily backups and
GitLab's documented low-memory settings.

Requirements
------------

- Docker and Docker Compose v2 installed on the target host (`docker_setup` role)
- The `community.docker` Ansible collection
- Traefik on the same host (`traefik_setup` role); it serves HTTPS for GitLab
  and the registry
- DNS records for `gitlab_main_domain` and `gitlab_registry_domain` pointing
  to the host
- Host TCP `gitlab_ssh_port` (default 2222) reachable for Git over SSH
- At least 4 GB of RAM plus swap for the GitLab container

Role Variables
--------------

See `defaults/main/main.yml` for all configurable variables.

| Variable | Default | Description |
|---|---|---|
| `gitlab_image_tag` | `19.4.1-ce.0` | GitLab CE image tag |
| `restart_policy` | `always` | Container restart policy |
| `service_dir` | `{{ project_dir }}/gitlab` | Service directory on the remote host |
| `gitlab_main_domain` | `git.k8sforfun.com` | GitLab domain |
| `gitlab_main_url` | `https://{{ gitlab_main_domain }}` | GitLab external URL |
| `gitlab_registry_domain` | `reg.k8sforfun.com` | Container registry domain |
| `gitlab_ssh_port` | `2222` | Host port for Git over SSH |
| `gitlab_memory_limit` | `4g` | Container memory limit |
| `gitlab_shm_size` | `256m` | Container shared memory |
| `gitlab_client_max_body_size` | `250m` | Maximum request size (pushes, uploads) |
| `gitlab_low_memory` | `true` | GitLab's memory-constrained settings (single Puma process, Sidekiq concurrency 10, Gitaly limits, no KAS) |
| `gitlab_signup_enabled` | `false` | Public sign-up page (Admin area setting) |
| `gitlab_web_ide_extension_host_domain` | `cdn.web-ide.gitlab-static.net` | Wildcard domain serving the Web IDE's VS Code assets (Admin area setting) |
| `gitlab_web_ide_single_origin_fallback_enabled` | `false` | Let the Web IDE serve those assets from GitLab's own origin when the extension host is unreachable (Admin area setting) |
| `gitlab_smtp_enable` | `true` | Send email through the mailserver |
| `gitlab_smtp_address` | `mail.k8sforfun.com` | SMTP server (SMTPS, implicit TLS) |
| `gitlab_smtp_port` | `465` | SMTP port |
| `gitlab_smtp_domain` | `k8sforfun.com` | SMTP HELO domain |
| `gitlab_smtp_username` | `admin@k8sforfun.com` | SMTP login |
| `gitlab_email_from` | `{{ gitlab_smtp_username }}` | Sender and reply-to address |
| `gitlab_email_display_name` | `GitLab` | Sender name |
| `gitlab_ip_whitelist` | see defaults | IPs that bypass RackAttack |
| `gitlab_backup_cron_enabled` | `true` | Daily `gitlab-backup create` from the host's cron |
| `gitlab_backup_cron_hour` / `_minute` | `3` / `0` | Backup time |
| `gitlab_backup_keep_time` | `604800` | Keep local backups for 7 days |
| `gitlab_backup_skip` | `registry` | Components left out of backups |
| `gitlab_minio_enabled` | `false` | Copy each backup to MinIO |
| `gitlab_minio_endpoint` | `https://minio-api.{{ main_domain }}` | MinIO API endpoint |
| `gitlab_minio_region` | `us-east-1` | S3 region |
| `gitlab_minio_bucket` | `gitlab-backups` | Bucket for backups |

Secrets (vault)
---------------

`defaults/main/vault.yml` is encrypted. It holds:

| Variable | Description |
|---|---|
| `gitlab_root_password` | Initial `root` password (applied on first start only) |
| `gitlab_smtp_password` | Password of `gitlab_smtp_username` |
| `gitlab_minio_access_key` / `gitlab_minio_secret_key` | Only when `gitlab_minio_enabled` is true |

Secrets reach GitLab as container environment variables and are read in
`gitlab.rb` through `ENV[...]`, so any character is safe in them.

Admin area settings
-------------------

Sign-up and the Web IDE settings are stored in GitLab's database, and
`gitlab.rb` has no option for them. After GitLab is up, the role reads them
with `gitlab-psql` and, only if a value differs, applies it with GitLab's
documented `::Gitlab::CurrentSettings.update!` in `gitlab-rails runner`. That
validates the values and refreshes GitLab's cache, so no restart is needed.
Values changed in the Admin area are reset on the next run.

With the single origin fallback off, the Web IDE works only when users'
browsers can reach `*.<gitlab_web_ide_extension_host_domain>`. If a network
blocks GitLab's default CDN, set up a custom extension host domain instead of
re-enabling the fallback.

Backups
-------

The host's cron runs `docker exec gitlab gitlab-backup create CRON=1` daily.
Archives go to the `gitlab_backups` volume and are pruned after
`gitlab_backup_keep_time`. With `gitlab_minio_enabled: true` each archive is
also uploaded to MinIO.

The backup archive does not contain `/etc/gitlab/gitlab-secrets.json`. It lives
in the `gitlab_config` volume; keep a copy of it somewhere safe, or restored
backups cannot decrypt CI variables and 2FA secrets.

Tags
----

| Tag | Runs |
|---|---|
| `preparing` | Networks, directory and templates |
| `pull` | Image pull |
| `deploy` | Stack deployment and wait for GitLab |
| `backup` | Backup cron job |
| `settings` | Sign-up and Web IDE Admin area settings |

Dependencies
------------

- docker_setup (Docker must be installed on the target host)
- traefik_setup (HTTPS for GitLab and the registry)

Example Playbook
----------------

    ansible-playbook playbooks/gitlab.yml --limit <host>

License
-------

MIT

Author Information
------------------

https://github.com/amati-sh
