# Argo CD Setup Role

Install the complete upstream Argo CD distribution in a dedicated single-node Kind
cluster, then expose it through the existing Docker Traefik using Compose labels.
Argo CD needs Kubernetes: running only its server image in Compose does not install
its controllers, CRDs, RBAC, Redis, or repository service.

The pinned upstream manifests plus Kustomize are a supported installation method;
Helm is optional. This role is a repeatable lab bootstrap, not an HA production
installation. It preserves the project's task imports, service-prefixed defaults,
Compose environment variables, Docker-label routing, and restart handler.

## Traffic path

```text
https://argocd.<main_domain>
  -> existing Traefik (web-secure, myproduction)
  -> argocd-proxy:8080 on web_net
  -> Kind node:30443 on the kind Docker network
  -> argocd-server:8080 with upstream TLS
```

Nginx bridges the two Docker networks. It publishes no host ports, uses Docker DNS
with periodic re-resolution, and checks the real Argo CD `/healthz` backend. TLS
terminates at Traefik and Nginx re-encrypts the internal Kubernetes connection.
Only the upstream self-signed certificate is not verified. Traefik handles the
public certificate and its existing HTTP-to-HTTPS redirect.

No persistent `kubectl port-forward`, systemd unit, Traefik file-provider route,
Traefik restart, or second ingress controller is needed. The previous unit template
is preserved under `legacy/` for comparison and is never installed. No task imports
the old Argo-specific additions in `traefik_setup`; those existing files have been
left untouched. If a previous version was deployed, retire its forwarder and
file-provider route in a separately reviewed migration first. The role refuses an
existing old unit rather than stopping or removing it automatically.

## Requirements

- Linux Docker host with root/sudo and working Docker Compose v2 or newer.
- `community.docker` collection on the Ansible controller.
- Existing running Traefik container named `traefik`, connected to `web_net`,
  with Docker discovery, `web`/`web-secure` and `myproduction` configured.
- DNS pointing to that host and reachable ports 80/443. DNS is not created here.
  The existing TLS-ALPN ACME challenge must reach Traefik directly.
- Outbound access to GitHub, Kubernetes downloads and upstream container registries.
- Capacity for Kubernetes and Argo CD in addition to existing services. A lab
  starting budget is 4 CPUs, 6 GiB RAM and 20 GiB free disk; image upgrades and
  application workloads need additional space.

Kind is suitable for this single-server lab. For production, use a maintained
Kubernetes cluster and review HA, backups and upgrade procedures. The role never
recreates or deletes an existing cluster. Ordinary reruns preserve cluster state;
deleting the Kind node/cluster destroys its stored state. No automatic rollback
or cluster-version upgrade is implemented.

## Variables

Values for the proxy follow `defaults/main/main.yml` -> `.env.j2` -> `${var}` in
Compose. Jinja in Kubernetes manifests is used for Kubernetes resource values.

| Variable | Default | Purpose |
|---|---|---|
| `service_dir` | `{{ project_dir }}/argocd` | Manifests, Compose, private kubeconfig |
| `argocd_domain` | `argocd.{{ main_domain }}` | Public hostname |
| `argocd_release` | `v3.5.5` | Pinned complete upstream release |
| `argocd_version_override` | empty | Optional exact release override |
| `argocd_manifest_sha256` | empty | Override the checksum for the selected release |
| `argocd_manifest_checksums` | SHA-256 for `v3.5.5` | Reviewed release manifest checksums |
| `argocd_use_kind` | `true` | Provision/reuse the dedicated Kind cluster |
| `argocd_kind_cluster_name` | `argocd` | Dedicated cluster name |
| `argocd_kubeconfig` | `{{ service_dir }}/kind-kubeconfig` | Separate mode-0600 kubeconfig |
| `argocd_kubectl_context` | `kind-argocd` | Explicit target context |
| `argocd_traefik_enabled` | `true` | NodePort and Compose proxy |
| `argocd_cluster_network` | `kind` | Docker network containing the node |
| `argocd_backend_host` | `argocd-control-plane` | Node DNS name/address on that network |
| `argocd_node_port` | `30443` | Internal HTTPS NodePort |
| `argocd_proxy_port` | `8080` | Internal proxy listener |
| `argocd_proxy_image_tag` | `1.28.3-alpine` | Official Nginx image tag |
| `restart_policy` | `unless-stopped` | Proxy restart policy |

The current inventory has `main_domain: w.k8sforfun.com`, so the default hostname is
`argocd.w.k8sforfun.com`. To use `argocd.k8sforfun.com`, override only
`argocd_domain` in the intended host's variables. Keep the shared domain unchanged.

The default version is pinned so a routine rerun does not unexpectedly upgrade
Argo CD. Set `argocd_release: latest` to opt into newest-stable discovery on every
run; discovery or a missing reviewed checksum stops deployment. Every release
uses its matching full manifest, including CRDs and RBAC. No forced rollout or field-ownership takeover
is performed. Review upstream upgrade notes and back up cluster/application data
before changing versions. The default release's SHA-256 is recorded in defaults.
For another release, review its manifest and supply `argocd_manifest_sha256` or
add it to `argocd_manifest_checksums`. A hash detects changed downloaded content;
it is not proof of the publisher's identity or a release signature.

For an existing cluster, set `argocd_use_kind: false`, an explicit target-side
kubeconfig/context, and a node/network reachable from the proxy container. This
bridge assumes Docker connectivity; a remote cluster needs a deliberately supplied
reachable backend and network. The standard manifest uses namespace `argocd`.
With `argocd_traefik_enabled: false`, the server remains ClusterIP and no proxy is
deployed. Disabling this toggle does not remove a previously deployed proxy.

## Run

From `ansible/ansible-practice`, choose one target explicitly:

```bash
ansible-playbook playbooks/argocd.yml --list-hosts --limit play2go-cactus
ansible-playbook playbooks/argocd.yml --syntax-check --limit play2go-cactus
ansible-playbook playbooks/argocd.yml --limit play2go-cactus
```

The playbook follows neighboring roles with `hosts: all`; always specify a limit.
Use the full role for first installation. Check mode skips cluster creation,
download/apply and proxy startup. It skips templates when the target directory
does not exist yet; it is not a full preview of a fresh installation. Read-only
preflight probes still run. Main tags
are `install_argocd`, `setup_argocd`, `preparing`, `pull`, `deploy`, `route_argocd`.

After the first full run, `preparing` renders configuration, `pull` downloads the
selected manifest and pulls proxy images, and `deploy` applies the already
prepared files and checks health. Both `install_argocd` and `setup_argocd` run the
complete installation including routing. `route_argocd` only refreshes the proxy.
Version resolution runs with `preparing`, `pull` and `deploy`; when changing
versions, use a full run so the rendered customization and downloaded manifest
stay aligned. Individual lifecycle tags in Kind mode require its kubeconfig to
exist already. Existing Kind kubeconfig identity is verified even in tagged runs.

The default kubeconfig is separate from the user's default Kubernetes context.
Missing Kind/kubectl tools are downloaded with SHA-256 verification; existing tools
are preserved, and a broken existing binary stops the run. The role checks that
kubectl is within one minor version of the API server and builds Kustomize before
applying Kubernetes resources. Kind and node versions are pinned in defaults.
Changing the node image only affects new clusters, not an existing cluster's
Kubernetes version.

## Production boundary

For production, plan a separate deployment on a maintained Kubernetes cluster
with the upstream HA installation, sufficient failure domains, tested backups
and restore, reviewed upgrades, SSO/RBAC and restricted AppProjects. Setting
`argocd_use_kind: false` selects an existing cluster; it still installs the
standard non-HA manifest. Merely adding replicas on this single node does not
provide host failure tolerance.

The Nginx bridge trusts the internal upstream certificate and requires `--grpc-web`
for CLI access. Production networking should use an ingress/Gateway or explicitly
trusted backend TLS. Limit access to the NodePort when using an existing cluster;
the bridge does not configure its firewall or network policies. Cluster readiness
and public `/healthz` alone do not verify application reconciliation or recovery.

## Login and checks

Open `https://<argocd_domain>` and log in as `admin`. Retrieve the generated password
privately on the target, then change it; never commit or print it in Ansible logs:

```bash
kubectl --kubeconfig /opt/services/argocd/kind-kubeconfig --context kind-argocd \
  -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 --decode
```

Use `argocd login <argocd_domain> --grpc-web` for the CLI through Nginx. No BasicAuth
middleware is added; Argo CD manages its own login and bearer tokens. Native HTTP/2
gRPC is not configured through this HTTP/1.1 bridge. Register repositories and
Applications separately. `/healthz` proves reachability, not login or Git sync.

Local validation:

```bash
python3 scripts/check-conventions.py argocd_setup
python3 -m unittest discover -s roles/argocd_setup/tests -v
ansible-playbook -i localhost, playbooks/argocd.yml --syntax-check --limit localhost
```

Tests need PyYAML, Jinja2 and Docker Compose. Set `KUBECTL` to a local kubectl binary
to also test the actual Kustomize merge without contacting Kubernetes. These checks
do not prove live cluster readiness, reboot recovery, public TLS or login.
Behavioral tests also use `ansible-playbook` with a temporary fake kubectl; they
exercise tagged runs, checksum refusal, version compatibility and apply failures
without contacting a cluster or starting containers.

References: [Argo CD installation](https://argo-cd.readthedocs.io/en/stable/getting_started/),
[installation methods and HA](https://argo-cd.readthedocs.io/en/stable/operator-manual/installation/),
[upgrades](https://argo-cd.readthedocs.io/en/stable/operator-manual/upgrading/overview/),
[Kind networking](https://kind.sigs.k8s.io/docs/user/configuration/).
