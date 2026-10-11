# Nexus with Traefik labels

## Files and prerequisites

- `docker-compose.yml`: Nexus and explicit routes for UI plus six Docker proxies.
- `.env.example`: image, restart policy, initial-password setting, resolver, hostnames.
- `nexus-config.json` / `setup-nexus.py`: standalone repository and security bootstrap.

Requires Docker Engine with Compose v2, Python 3, and an **existing Traefik** configured
with the Docker provider, entrypoints `web` (:80) and `web-secure` (:443), and certificate
resolver `myproduction`. Set `TRAEFIK_CERTRESOLVER` to your existing resolver name.
Traefik must join `web_net`; Nexus joins both `web_net` and `app_net`, matching the role.
Nexus ports are not published on the host. This directory does not deploy Traefik itself.

## Start a new installation

1. Review the parent README's volume and migration warnings. Ensure no other `nexus`
   container is running and DNS for all seven names points to this proxy. Check the
   resolver's ACME prerequisites; TLS-ALPN requires direct public port 443 access.
2. Create `.env` without overwriting an existing file, protect it, and edit the password,
   hostnames and resolver:

   ```bash
   test -e .env || (umask 077; cp .env.example .env)
   chmod 600 .env
   ${EDITOR:-vi} .env
   ```

3. Create only networks that are absent, validate, and start:

   ```bash
   docker network inspect web_net >/dev/null 2>&1 || docker network create --opt com.docker.network.bridge.name=web_net web_net
   docker network inspect app_net >/dev/null 2>&1 || docker network create --opt com.docker.network.bridge.name=app_net app_net
   docker compose config --quiet
   docker compose up -d
   docker compose logs -f nexus
   ```

4. Complete Nexus onboarding at your main hostname. Use the actual admin password;
   preserved initial-password variables are not guaranteed by the upstream image.
   Confirm the in-container readiness command works:

   ```bash
   docker compose exec nexus curl -sf http://localhost:8081/service/rest/v1/status
   ```

## Configure repositories and access

Inspect `nexus-config.json` before applying. It contains the role's exact REST payloads.
The reverse proxy alone does not create Docker connector listeners; bootstrap or an
existing configured volume must create those repositories first.

```bash
# Offline preview; no credentials or network needed.
python3 setup-nexus.py --url https://repo.example.com

# Creates missing objects, enables anonymous access and DockerToken, creates nx-deploy.
# Prompts securely for the actual admin password and deploy user password.
# Empty deploy password skips user creation.
python3 setup-nexus.py --url https://repo.example.com --wait 300 --apply
```

Use the hostname configured for your deployment, with a trusted certificate.
The helper does not read `.env`; it prompts or accepts `NEXUS_ADMIN_PASSWORD` and
`NEXUS_DEPLOY_USER_PASSWORD` from the process environment. Avoid passwords in shell history.
Existing user passwords are never reset. Anonymous access and broad deployment
permissions match the source role; review them before applying.

For an approved settings update, add `--update-existing` to `--apply`; it PUTs all
14 repository definitions. Review differences and back up first.

The seven default Maven/NuGet repositories listed in the JSON are not deleted normally.
If you deliberately want the role's deletion behavior after checking their contents and
verifying a backup, add `--delete-default-repos` to `--apply`. It lists the names and
requires typing `DELETE DEFAULT REPOSITORIES` before making changes.

If the internal cleanup-policy API rejects the request, create the four policies in
the Nexus UI using the JSON values, then rerun. Read the limitations and migration
warnings in the parent README before using an existing volume.

## Verify and operate

```bash
docker compose ps
docker compose logs -f nexus
curl --fail https://repo.example.com/service/rest/v1/status
curl -i https://hub.example.com/v2/
```

A registry may return `200` or an authentication challenge (`401`); neither proves
upstream image retrieval. Test an actual pull after bootstrap:

```bash
docker pull hub.example.com/library/alpine:3.22
```

After approving an image update, validate Compose, pull, and use `docker compose up -d`.
Do not delete the data volume. Allow Nexus sufficient startup time; logs and health
output distinguish application failures from healthcheck failures.
