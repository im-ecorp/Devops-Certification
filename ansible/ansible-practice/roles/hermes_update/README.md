Hermes Agent Update
===================

Updates an existing official Hermes Agent git installation without creating a
pre-update backup, then restarts and verifies the Hermes gateway. The gateway
may be installed as a system service or as root's systemd user service; the
role detects which.

The role first runs `hermes update --check`. If no update is available and no
gateway restart is pending, it does not modify Hermes or restart the gateway.

Requirements
------------

- Hermes Agent installed with the official root-mode installer
- `/usr/local/bin/hermes` available on the target
- `hermes-gateway.service` installed as a system service
  (`hermes gateway install --system`) or as root's user service with linger
  enabled (`hermes gateway install`)

Role Variables
--------------

| Variable | Default | Description |
|---|---|---|
| `hermes_update_binary` | `/usr/local/bin/hermes` | Hermes launcher on the target host |
| `hermes_update_gateway_scope` | `auto` | `system`, `user`, or `auto` (system if `/etc/systemd/system/hermes-gateway.service` exists, else user) |

Update Sequence
---------------

1. Detect the gateway service scope.
2. Check for an available update and for a pending gateway restart.
3. Run `hermes update --yes --no-backup --no-gateway-restart`.
4. Restart the gateway with `hermes gateway restart` (plus `--system` for a
   system service) when an update was installed or `hermes gateway status`
   reports that earlier-pulled code is still waiting for a restart.
5. Verify `hermes-gateway.service` is active and print the installed version.

The `--no-gateway-restart` flag keeps the update and restart as separate,
observable Ansible steps. `--no-backup` skips both the quick state snapshot and
full archive, regardless of the configured backup setting. This update creates
no pre-update recovery backup; existing backups are not deleted.

Example
-------

    ansible-playbook playbooks/hermes-update.yml --limit hetzner-cactus

Preview the selected host and tasks first:

    ansible-playbook playbooks/hermes-update.yml --limit hetzner-cactus --list-hosts --list-tasks

Tags
----

- `hermes_update`
