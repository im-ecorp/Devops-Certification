Role Name
=========

A brief description of the role goes here.

Business Edition License
------------------------

Set `portainer_license_key` to a Portainer Business Edition license key to
switch the deployment from `portainer/portainer-ce` to
`portainer/portainer-ee`:

- A fresh install deploys `portainer/portainer-ee` directly with the
  `PORTAINER_LICENSE_KEY` environment variable (read at container start).
- An existing `portainer-ce` container is upgraded in place via the Portainer
  API (`POST /api/system/upgrade`, admin credentials from
  `portainer_admin_user` / `portainer_admin_password`).

The tracked compose image name switches to `portainer-ee` once a key is set, so
later reconciliations never revert to Community Edition. `portainer_api_url`
(defaults to `https://{{ portainer_main_domain }}`) must be reachable from the
target host.

Requirements
------------

Any pre-requisites that may not be covered by Ansible itself or the role should be mentioned here. For instance, if the role uses the EC2 module, it may be a good idea to mention in this section that the boto package is required.

Role Variables
--------------

A description of the settable variables for this role should go here, including any variables that are in defaults/main.yml, vars/main.yml, and any variables that can/should be set via parameters to the role. Any variables that are read from other roles and/or the global scope (ie. hostvars, group vars, etc.) should be mentioned here as well.

Dependencies
------------

A list of other roles hosted on Galaxy should go here, plus any details in regards to parameters that may need to be set for other roles, or variables that are used from other roles.

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

    - hosts: servers
      roles:
         - { role: username.rolename, x: 42 }

License
-------

BSD

Author Information
------------------

An optional section for the role authors to include contact information, or a website (HTML is not allowed).
