# Nginx Setup

Install distribution Nginx on Debian/Ubuntu and manage named HTTP/HTTPS routes.
This is a **host service**, not a Docker or Traefik deployment.

## Structure

- `defaults/main.yml`: commented, overridable `nginx_*` variables.
- `tasks/main.yml`: installation and configuration imports with inherited tags.
- `tasks/installation.yml`: platform check and idempotent APT installation.
- `tasks/configuration.yml`: input validation, templates, site links and service.
- `handlers/main.yml`: validate before a graceful reload, only on changes.
- `templates/`: role-owned proxy headers, WebSocket map and site configuration.
- `tests/test_templates.py`: template regression tests.
- `playbooks/nginx.yml`: standalone entry point.

## Configuration

Define routes in inventory `host_vars` or `group_vars`. No route is enabled by
an empty `nginx_sites` list. Each site needs a unique safe filename, a
`server_name`, and exactly one of `proxy_pass` or `root`.

```yaml
nginx_sites:
  - name: app.conf
    server_name: app.example.com
    proxy_pass: http://127.0.0.1:8080
    client_max_body_size: 32M
    proxy_read_timeout: 300s

  - name: secure.conf
    server_name: secure.example.com
    proxy_pass: http://127.0.0.1:9000
    ssl_enabled: true
    ssl_cert_path: /etc/letsencrypt/live/secure.example.com/fullchain.pem
    ssl_key_path: /etc/letsencrypt/live/secure.example.com/privkey.pem

  - name: static.conf
    server_name: static.example.com
    root: /var/www/static
```

Optional site fields are `listen_port` (HTTP, default 80), `ssl_port` (default
443), `ssl_enabled` (boolean, default false), `client_max_body_size` and
`proxy_read_timeout`. HTTPS sites redirect HTTP to HTTPS. Certificates must
already exist; this role does not obtain or renew certificates. The static
root and its content must also already exist and be readable by Nginx.

Proxy routes use HTTP/1.1, WebSocket Upgrade/Connection headers and forwarded
client headers. Upstream HTTPS enables SNI; it uses Nginx's default upstream
certificate verification policy (verification is off). Use a trusted internal
backend or extend the configuration before proxying untrusted HTTPS backends.
The URI is preserved when `proxy_pass` has no trailing path; a trailing slash
or path follows standard Nginx `proxy_pass` URI replacement behavior.

## Safety and reuse

- Preserve `/etc/nginx/nginx.conf`, `/etc/nginx/proxy_params`, the distribution
  default site and unrelated configurations. No site files are deleted.
- Refuse existing site files without the role ownership marker.
- Own only the requested `sites-available/<name>` / `sites-enabled/<name>` and
  the namespaced snippet and map. Do not reuse a filename owned by another role
  (for example AWX). Changed templates keep Ansible timestamped backups.
- Removing an entry from `nginx_sites` does **not** disable or delete its old
  route. Decommission it separately after reviewing the traffic impact.
- The distribution `nginx.conf` must include `conf.d/*.conf` in HTTP context
  and `sites-enabled/*` (the Debian/Ubuntu package defaults do).
- The default site remains enabled. Managed routes are selected by their Host
  names; this role does not claim the default/catch-all listener.
- Full `nginx -t` runs before starting or reloading, including unrelated sites.
  Invalid files block reload, but remain on disk for diagnosis; there is no
  automatic rollback. Restore the timestamped backup before a manual restart.
- Check mode does not run `nginx -t` against files that were not written.
  It predicts changes; it does not prove live configuration validity.
- No firewall changes, DNS changes or automatic certificate issuance.
- Package installation can start the distribution service. Ensure ports are
  free and approve the traffic change before deployment.

## Run

From the project root, always scope the target explicitly:

```bash
ansible-playbook playbooks/nginx.yml --list-hosts --limit <host>
ansible-playbook playbooks/nginx.yml --syntax-check --limit <host>
ansible-playbook playbooks/nginx.yml --check --diff --limit <host>
ansible-playbook playbooks/nginx.yml --limit <host>
```

Tags: `install_nginx`, `configure_nginx`, `setup_nginx`; input assertions use
`always`, and directory preparation additionally uses `preparing`.
Run the full role once before using configuration-only tags on a fresh host.

## Local validation

```bash
python3 scripts/check-conventions.py nginx_setup
ansible-playbook playbooks/nginx.yml --syntax-check -i localhost, --limit localhost
ansible-lint --offline -c roles/nginx_setup/.ansible-lint roles/nginx_setup playbooks/nginx.yml
yamllint roles/nginx_setup playbooks/nginx.yml
pytest -q roles/nginx_setup/tests/test_templates.py
git diff --check
```

Use an isolated test host for two consecutive full runs before claiming live
idempotency; syntax and template tests do not deploy or modify inventory hosts.
