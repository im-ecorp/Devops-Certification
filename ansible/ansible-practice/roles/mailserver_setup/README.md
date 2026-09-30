Role Name
=========

Deploy [docker-mailserver](https://github.com/docker-mailserver/docker-mailserver)
(Postfix, Dovecot, Rspamd, DKIM) with Docker Compose via Ansible. The TLS
certificate comes from the existing Traefik instance.

The configuration is the light setup the docker-mailserver docs recommend:
Rspamd for spam filtering, DKIM, DMARC and SPF, Fail2Ban against password
guessing, and IMAP only (no POP3, no ClamAV). Idle memory is roughly 300–500 MB.

With `mailserver_webmail_enabled: true` (the default) the role also deploys
[Roundcube](https://roundcube.net) webmail at `https://<mailserver_hostname>/`.

Requirements
------------

- Docker and Docker Compose v2 installed on the target host (`docker_setup` role)
- The `community.docker` Ansible collection (see `requirements.yml`)
- `passlib` on the Ansible controller (used to hash mailbox passwords)
- Traefik deployed on the same host (`traefik_setup` role); it issues the
  mail certificate
- `main_domain` and `project_dir` set in `inventory/group_vars/all/general.yml`
- Inbound TCP 25, 465, 587 and 993 open in the host firewall. With the
  `preparing_server` role, add them to `tcp_port_access`
- Outbound TCP 25 allowed by the hosting provider (many block it by default)

How TLS works
-------------

Mail ports are published directly and do not pass through Traefik. The
Roundcube container carries a Traefik router for `mailserver_hostname`, so
Traefik issues and renews that certificate. With webmail off, a small
`traefik/whoami` container carries the router instead. The mailserver mounts Traefik's
`acme.json` read-only and reloads when the certificate changes.

The mailserver refuses to start without its certificate. On first deploy the
role starts the router container, waits for the certificate to appear in
`acme.json`, and only then starts the mailserver.

Role Variables
--------------

See `defaults/main/main.yml` for all configurable variables.

| Variable | Default | Description |
|---|---|---|
| `mailserver_image_tag` | `16.0.1` | docker-mailserver image tag |
| `mailserver_whoami_image_tag` | `v1.12.0` | Certificate router image tag |
| `restart_policy` | `always` | Container restart policy |
| `service_dir` | `{{ project_dir }}/mailserver` | Service directory on the remote host |
| `mailserver_domain` | `k8sforfun.com` | Mail domain (the part after `@`) |
| `mailserver_hostname` | `mail.{{ mailserver_domain }}` | Server FQDN, MX target and certificate name |
| `mailserver_postmaster_address` | `postmaster@{{ mailserver_domain }}` | Receives bounces and reports |
| `mailserver_timezone` | `Asia/Tehran` | Container timezone |
| `mailserver_ports` | `25, 465, 587, 993` | Published ports (`host:container`) |
| `mailserver_host_mta_services` | `exim4, postfix` | Host mail services stopped so the container can bind port 25 |
| `mailserver_traefik_volume` | `traefik_data` | Traefik volume holding `acme.json` |
| `mailserver_cert_timeout` | `300` | Seconds to wait for the first certificate |
| `mailserver_message_size_limit` | `26214400` | Maximum message size in bytes |
| `mailserver_memory_limit` | `1g` | Container memory limit |
| `mailserver_webmail_enabled` | `true` | Deploy Roundcube webmail at `https://<mailserver_hostname>/` |
| `mailserver_webmail_image_tag` | `1.7.4-apache` | Roundcube image tag |
| `mailserver_webmail_memory_limit` | `256m` | Roundcube memory limit |
| `mailserver_webmail_subnet` | `10.253.25.0/28` | Private network between webmail and mailserver |
| `mailserver_webmail_ip` | `10.253.25.10` | Fixed webmail IP inside that subnet |
| `mailserver_dkim_selector` | `mail` | DKIM selector |
| `mailserver_dkim_key_size` | `2048` | DKIM RSA key size |
| `mailserver_accounts` | `admin@{{ mailserver_domain }}` | Mailboxes (`address`, `password`) |
| `mailserver_aliases` | `postmaster@ -> admin@` | Aliases (`address`, `destination`) |
| `mailserver_admin_password` | *(vault)* | Password of the default admin mailbox |
| `mailserver_webmail_des_key` | *(vault)* | Roundcube session encryption key (24 characters) |

Manage mailboxes and aliases only through `mailserver_accounts` and
`mailserver_aliases`. The role rewrites `postfix-accounts.cf` and
`postfix-virtual.cf` on every run, so accounts added with `setup email add` are
lost. The mailserver picks up changes to these files without a restart.

Webmail
-------

Users sign in with their mailbox name alone (`admin`) or the full address. The
role keeps these properties:

- Roundcube reaches the mailserver over a private network, using the public
  hostname, so the certificate matches. It uses IMAPS (993) and SMTPS (465)
  with the user's own credentials.
- Every webmail login reaches the mailserver from the webmail container's
  fixed IP. That IP is excluded from Fail2Ban (`config/fail2ban-jail.cf`), so
  one user's wrong passwords cannot ban webmail for everyone. Roundcube limits
  failed logins itself (3 per minute).
- Settings and contacts live in the `mailserver_webmail_db` volume (SQLite).

Secrets (vault)
---------------

`defaults/main/vault.yml` is encrypted and holds a generated
`mailserver_admin_password` and `mailserver_webmail_des_key`. View or change it with:

    ansible-vault view defaults/main/vault.yml
    ansible-vault edit defaults/main/vault.yml

Add a vault variable for each extra mailbox and reference it from
`mailserver_accounts`.

DNS
---

At the end of a run the role prints the records to create: A, MX, SPF, DMARC,
DKIM and PTR. The DKIM key is generated once, on first deploy, under
`{{ service_dir }}/config`. Reverse DNS (PTR) is set at the hosting provider.
Without matching PTR, SPF and DKIM records, other servers will reject or
spam-folder your mail.

Tags
----

| Tag | Runs |
|---|---|
| `preparing` | Validation, networks, directories and templates |
| `accounts` | Only the accounts and aliases files |
| `pull` | Image pull |
| `deploy` | Certificate, stack deployment, health wait and DKIM |
| `dns` | Print the DNS records again |

Dependencies
------------

- docker_setup (Docker must be installed on the target host)
- traefik_setup (issues the TLS certificate)

Example Playbook
----------------

    ansible-playbook playbooks/mailserver.yml --limit <host>

License
-------

MIT

Author Information
------------------

https://github.com/amati-sh
