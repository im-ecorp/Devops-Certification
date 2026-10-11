# Nexus with a regular Nginx configuration

## Files and prerequisites

- `docker-compose.yml`: Nexus plus `nginx:1.28-alpine` reverse proxy.
- `conf.d/nexus.conf`: explicit upstreams and HTTP/HTTPS virtual hosts; no Ansible templates.
- `.env.example`: Nexus image, restart policy and initial-password setting.
- `certs/`: supply `fullchain.pem` and `privkey.pem` here.
- `nexus-config.json` / `setup-nexus.py`: independent repository and security bootstrap.

Requires Docker Engine with Compose v2, Python 3, DNS for all seven hostnames, and a
trusted TLS certificate covering every name. Nginx publishes ports 80 and 443; Nexus
ports remain private. Both containers join the role's external `app_net`.
No Traefik network, labels, or service is needed for this version.

## Start a new installation

1. Review the parent README's volume warnings. Confirm ports 80/443 are free before
   starting this stack. Do not stop an existing proxy or Nexus instance without an
   approved migration plan. If using different domains, edit **every** `server_name`
   in `conf.d/nexus.conf`; `.env` does not substitute Nginx configuration values.
2. Create `.env` without overwriting an existing file and edit the initial-password
   setting:

   ```bash
   test -e .env || (umask 077; cp .env.example .env)
   chmod 600 .env
   ${EDITOR:-vi} .env
   ${EDITOR:-vi} conf.d/nexus.conf
   ```

3. Install your certificate and private key at `certs/fullchain.pem` and
   `certs/privkey.pem`. Protect the key. Certificate issuance and renewal are external;
   this stack does not run an ACME client.
4. Create the network only if absent, validate, and start Nexus first:

   ```bash
   docker network inspect app_net >/dev/null 2>&1 || docker network create --opt com.docker.network.bridge.name=app_net app_net
   docker compose config --quiet
   docker compose up -d nexus
   docker compose logs -f nexus
   ```

5. Once Nexus is healthy, validate the proxy configuration without binding host ports,
   then start Nginx:

   ```bash
   docker compose run --rm --no-deps nginx nginx -t
   docker compose up -d nginx
   ```

6. Complete Nexus onboarding at the main hostname and use the actual administrator
   password for bootstrap. The preserved initial-password variables do not reset
   existing credentials and are not guaranteed by the upstream image.

## Configure repositories and access

Inspect `nexus-config.json` before applying. It contains the role's exact REST payloads.
The reverse proxy alone does not create Docker connector listeners; bootstrap or an
existing configured volume must create those repositories first.

```bash
# Offline preview; no credentials or network needed.
python3 setup-nexus.py --url https://repo.w.k8sforfun.com

# Creates missing objects, enables anonymous access and DockerToken, creates nx-deploy.
# Prompts securely for the actual admin password and deploy user password.
# Empty deploy password skips user creation.
python3 setup-nexus.py --url https://repo.w.k8sforfun.com --wait 300 --apply
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
curl --fail https://repo.w.k8sforfun.com/service/rest/v1/status
curl -i https://hub.w.k8sforfun.com/v2/
```

A registry may return `200` or an authentication challenge (`401`); neither proves
upstream image retrieval. Test an actual pull after bootstrap:

```bash
docker pull hub.w.k8sforfun.com/library/alpine:3.22
```

After approving an image update, validate Compose, pull, and use `docker compose up -d`.
Do not delete the data volume. Allow Nexus sufficient startup time; logs and health
output distinguish application failures from healthcheck failures.

## Nginx notes

TLS terminates at Nginx; the Nexus upstreams remain HTTP. The configuration preserves
request paths and Host, forwards the HTTPS scheme, streams requests/responses, allows
unlimited request bodies, and uses 300-second transfer timeouts. Forwarded client IP
is derived from the immediate peer, not blindly trusted incoming headers. If a CDN
is added, configure trusted proxy IP ranges separately.

After changing configuration or renewing the certificate:

```bash
docker compose exec nginx nginx -t
docker compose exec nginx nginx -s reload
```

These regular upstreams resolve `nexus` at Nginx startup/reload. If Nexus is recreated
with a new container IP, reload Nginx after Nexus becomes healthy.

For an existing Dockerized Nginx, mount this config and certificates there instead of
starting the bundled proxy, and join `app_net`. For a **host-installed** Nginx, Docker
DNS `nexus` is not available: deliberately publish loopback-only ports for 8081 and
9091–9096, change every upstream to `127.0.0.1:<port>`, and adjust certificate paths.
That host-Nginx adaptation is not the default configuration supplied here.
