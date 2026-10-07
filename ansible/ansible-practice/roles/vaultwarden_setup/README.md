# Vaultwarden Setup Role

Deploys [Vaultwarden](https://github.com/dani-garcia/vaultwarden) behind Traefik reverse proxy using Docker Compose, adhering strictly to the repository conventions.

## Architecture

- **Image**: `vaultwarden/server:{{ vaultwarden_image_tag }}` (official upstream Debian-based release).
- **Networks**: Vaultwarden joins only `web_net`. The role creates both `web_net` and `app_net` and declares them external, matching the repository convention. No database service is needed; Vaultwarden uses SQLite in `/data`.
- **Storage**: Persistent named Docker volume `vaultwarden_data` mounted at `/data`.
- **Traefik**: Uses Docker labels exclusively; no dynamic configuration files in Traefik's directory.
  - HTTP router on entrypoint `web`
  - HTTPS router on entrypoint `web-secure` with TLS resolver `myproduction`
  - Backend service pointing to container port `${ROCKET_PORT}` (default: `80`, handling both HTTP and WebSockets)
- **Healthcheck**: Internal container check calling `/healthcheck.sh` (`/alive` endpoint).

## Variables

Key non-secret variables are defined in `defaults/main/main.yml`:

| Variable | Default | Description |
|---|---|---|
| `vaultwarden_image_tag` | `"1.37.4"` | Upstream Vaultwarden image tag |
| `restart_policy` | `"unless-stopped"` | Restart after failures/reboots unless intentionally stopped |
| `service_dir` | `"{{ project_dir }}/vaultwarden"` | Directory on target host |
| `vaultwarden_main_domain` | `"vault.{{ main_domain }}"` | Domain evaluated by Traefik `Host()` rule |
| `vaultwarden_main_url` | `"https://{{ vaultwarden_main_domain }}"` | Public URL configured in Vaultwarden `DOMAIN` |
| `vaultwarden_port` | `80` | Internal HTTP/WebSocket port |
| `vaultwarden_websocket_enabled` | `true` | Integrated WebSocket notification server toggle |
| `vaultwarden_signups_allowed` | `false` | Allow public signups |
| `vaultwarden_invitations_allowed` | `true` | Allow organization invitations |
| `vaultwarden_show_password_hint` | `false` | Never expose password hints on public pages |
| `vaultwarden_password_hints_allowed` | `false` | Disable password hints entirely |
| `vaultwarden_login_ratelimit_seconds` | `60` | Upstream login limit average interval (seconds) |
| `vaultwarden_login_ratelimit_max_burst` | `10` | Upstream login limit burst allowance |
| `vaultwarden_admin_session_lifetime` | `20` | Admin session lifetime (minutes), when enabled |
| `vaultwarden_admin_ratelimit_seconds` | `300` | Upstream admin limit average interval (seconds) |
| `vaultwarden_admin_ratelimit_max_burst` | `3` | Upstream admin limit burst allowance |
| `vaultwarden_admin_token_enabled` | `false` | Enable `/admin` panel access |
| `vaultwarden_smtp_enabled` | `false` | Enable SMTP mail notifications |

Vault secrets are in `defaults/main/vault.yml` (encrypted with Ansible Vault):
- `vaultwarden_admin_token`: Argon2id hashed secret for `/admin`.
- `vaultwarden_smtp_password`: SMTP authentication password.

## Production defaults

Public registration is closed; organization owners/admins can still invite users. Disable `vaultwarden_invitations_allowed` as well if only the instance administrator should onboard users.

`vaultwarden_admin_token_enabled: false` is the conservative default for an Internet-facing service. Enable it only when needed, with an Argon2id token, HTTPS, and preferably VPN/IP-restricted access to `/admin`. It is not necessary for normal vault/client operation. Admin invitations work even with public registration and organization invitations disabled. Existing `/data/config.json` values can override these environment defaults; setting this toggle to false alone does not remove a previously saved admin token.

SMTP remains disabled because no real server/credentials are configured. Configure authenticated TLS SMTP for production email features. Do not enable mandatory email verification before working mail delivery is confirmed. Login and admin rate limits retain upstream defaults; client 2FA, tested backups and timely security updates remain separate operational requirements.

Sources: [admin panel and token security](https://github.com/dani-garcia/vaultwarden/wiki/Enabling-admin-page), [registration and invitations](https://github.com/dani-garcia/vaultwarden/wiki/Disable-registration-of-new-users), and [upstream environment settings](https://github.com/dani-garcia/vaultwarden/blob/1.37.4/.env.template).

## Prerequisites and configuration

- Docker Engine and the Compose v2 plugin must already be installed on the target.
- Deploy the existing `traefik_setup` role separately. Its `web` entrypoint redirects HTTP to HTTPS; this role does not change Traefik.
- Point `vault.{{ main_domain }}` at the target and allow Traefik's ports 80/443 and ACME TLS challenge. With the current inventory variables, the URL is `https://vault.w.k8sforfun.com`.
- Install the existing collection requirement with `ansible-galaxy collection install -r requirements.yml`.
- Ansible uses the vault password source configured in `ansible.cfg`. The encrypted role vault initially contains empty values; no credentials are generated.

To enable `/admin`, set `vaultwarden_admin_token_enabled: true`, generate an Argon2id hash using Vaultwarden's `/vaultwarden hash` command, and save only the hash as `vaultwarden_admin_token` using:

```bash
ansible-vault edit roles/vaultwarden_setup/defaults/main/vault.yml
```

The role rejects an enabled admin panel without an Argon2id hash. Single quoting in `.env.j2` preserves the hash's `$` characters.

For email, set `vaultwarden_smtp_enabled: true` and configure a server reachable from the container. `127.0.0.1` would address the container itself. Set the SMTP password in the encrypted vault when authentication is used. An empty username permits a trusted unauthenticated relay; no credentials are passed in that case.

## Playbook execution

Run from the Ansible project root. Always select an explicit host:

```bash
ansible-playbook playbooks/vaultwarden.yml --list-hosts --limit <host>
ansible-playbook playbooks/vaultwarden.yml --limit <host>
```

Tags: `install_vaultwarden`, `setup_vaultwarden`, `preparing`, `docker`, `pull`, and `deploy`.

## First account

No account is created automatically. Public registration and `/admin` are disabled by default. Before deployment, choose one bootstrap method:

- Enable the protected admin panel as described above and invite the first account through `/admin`.
- Temporarily set `vaultwarden_signups_allowed: true` on a restricted deployment, register the first account, then set it back to `false` and rerun the role.

Do not leave public registration enabled unintentionally. Organization invitations remain allowed by default.

## Operations

The role flushes restart handlers before checking container health and the public HTTPS `/alive` endpoint. It skips pull, deployment and readiness checks in Ansible check mode. Environment files use mode `0600`, suppress secret diffs/logging, and preserve previous configurations with template backups.

Back up the full `vaultwarden_data` volume before upgrades, including SQLite, attachments and keys. Do not remove this volume. Configuration saved through `/admin` in `/data/config.json` can override environment settings; inspect it if role changes appear ineffective.

Local validation covered syntax, the convention checker, and rendered Compose configurations for defaults, admin/authenticated SMTP, and an unauthenticated relay. No live deployment or runtime idempotency test was performed.
