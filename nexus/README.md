# Standalone Nexus Repository

Two alternatives extracted from `ansible/ansible-practice/roles/nexus_setup`.
Neither version needs Ansible, Jinja, a vault, or files outside its own directory.

- [Traefik](traefik/README.md): Nexus Compose service with Docker labels; uses an existing Traefik proxy.
- [Nginx](nginx/README.md): Nexus and Nginx Compose services; regular `conf.d/nexus.conf` file.

Each directory includes `docker-compose.yml`, `.env.example`, `nexus-config.json`,
`setup-nexus.py`, and its own instructions. Copy either directory by itself.

## Preserved configuration

- Nexus `sonatype/nexus3:3.94.1`, container/hostname `nexus`, restart policy `always`.
- Named volume `nexus_data` mounted at `/nexus-data`; original readiness check and timings.
- Main domain from inventory: `w.k8sforfun.com`. Change hostnames for another deployment.
- Three file blob stores: `apt`, `docker`, `raw`.
- Four cleanup policies: `apt`, `docker`, `raw`, `pypi`, with 30-day last-update and 90-day last-download criteria.
- Six APT proxies: `ubuntu`, `ubuntu-security`, `ubuntu-docker`, `debian`, `debian-security`, `debian-docker`.
- Six Docker proxies with their original upstreams and connector ports.
- Raw `kube` proxy (`https://files.m.daocloud.io`) and PyPI proxy (`https://pypi.org/`, using the `raw` blob store).
- Anonymous access, Docker Bearer Token realm, `nx-deploy` role and `deploy` user.
- Cache ages/TTL remain 1440; APT distribution strings and Docker v1/basic-auth flags remain as defined in the role.

| Public hostname | Nexus port | Purpose |
| --- | ---: | --- |
| `repo.w.k8sforfun.com` | 8081 | UI, REST API, APT, Raw, PyPI |
| `hub.w.k8sforfun.com` | 9091 | `https://hub.hamdocker.ir` |
| `quay.w.k8sforfun.com` | 9092 | `https://quay.io/` |
| `k8s.w.k8sforfun.com` | 9093 | `https://registry.k8s.io` |
| `gcr.w.k8sforfun.com` | 9094 | `https://gcr.io` |
| `k8s-gcr.w.k8sforfun.com` | 9095 | `https://k8s.gcr.io` |
| `github.w.k8sforfun.com` | 9096 | `https://ghcr.io` |

## Intentional adaptations

- Plain `.env` values replace Ansible substitutions. The role references an absent `.env.j2`; no encrypted vault credentials were copied.
- Traefik explicitly selects `web_net` and assigns services to HTTP routers. A local HTTPS redirect preserves the original Traefik role's global redirect behavior.
- Nginx routes through Docker DNS, terminates TLS, forwards proxy headers, and streams large requests. It joins `app_net`; Nexus no longer needs `web_net` in this version.
- Bootstrap is an offline dry run by default. `--apply` creates missing objects; `--update-existing` explicitly enables the role's repository PUT behavior. Existing roles, users, blob stores, and cleanup policies are not overwritten.
- Default Maven/NuGet repository deletion is retained only as an opt-in operation with interactive confirmation.
- HTTPS certificates are verified by Python, unlike the role's `validate_certs: false`. Use a trusted CA; credentials are not passed as CLI arguments.

## Existing installations and safety

These are alternatives, not two concurrent Nexus installations. Both retain `container_name: nexus`
and `nexus_data` for compatibility. Never attach two running Nexus instances to the same volume.
For a genuinely separate installation, change both the container and volume names first.

Do not run either stack on the existing server until you have reviewed container ownership,
proxy ports, and the volume. Back up the current Compose/environment files and take a
consistent, verified backup of `/nexus-data` with Nexus stopped before an approved migration.
Do not use `docker compose down -v` or delete/reinitialize `nexus_data`.

The initial-password environment variables from the role are preserved, but are not a
password-reset mechanism and the image documentation does not promise that
`NEXUS_SECURITY_INITIAL_PASSWORD` sets the supplied value. On a new volume, complete
Nexus onboarding and use the actual administrator credentials. On an existing volume,
its stored credentials and repository configuration remain authoritative.

Anonymous access and the broad `nx-repository-view-*-*-*` deployment privilege are
preserved, not hardened. Review whether those permissions suit your environment.

Cleanup policies use the role's **internal** `/service/rest/internal/cleanup-policies`
API, which may change or require a UI session/CSRF token. If setup fails there, create
those four policies in the UI with the JSON's criteria, then rerun. The helper fails
rather than silently omitting policies. It does not schedule a cleanup task.
The comma-separated APT distributions are preserved; confirm their behavior against
your Nexus version before relying on multi-distribution mirroring.

## Local checks

Bootstrap needs only Python 3's standard library. Tests additionally need PyYAML:

```bash
python3 -m venv .venv
.venv/bin/pip install PyYAML
.venv/bin/python -m unittest discover -s tests -v
```

Tests exercise a **simulated local REST API**, not a live Nexus installation.
Compose rendering and Nginx syntax validation do not prove image availability,
repository creation, certificate issuance, or successful image pulls.

Sources: [Nexus image](https://github.com/sonatype/docker-nexus3),
[Traefik Docker routing](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/),
[Nginx proxy module](https://nginx.org/en/docs/http/ngx_http_proxy_module.html).
