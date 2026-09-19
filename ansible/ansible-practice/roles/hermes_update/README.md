Hermes Agent Update
===================

Updates an existing official Hermes Agent git installation without creating a
pre-update backup, then restarts and verifies the system-level Hermes gateway.

The role first runs `hermes update --check`. If no update is available, it does
not modify Hermes or restart the gateway.

Requirements
------------

- Hermes Agent installed with the official root-mode installer
- `/usr/local/bin/hermes` available on the target
- `hermes-gateway.service` installed as a system service

Role Variables
--------------

| Variable | Default | Description |
|---|---|---|
| `hermes_update_binary` | `/usr/local/bin/hermes` | Hermes launcher on the target host |

Update Sequence
---------------

1. Check for an available update.
2. Run `hermes update --yes --no-backup --no-gateway-restart`.
3. Restart the system gateway with `hermes gateway restart --system`.
4. Verify `hermes-gateway.service` is active and print the installed version.

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
