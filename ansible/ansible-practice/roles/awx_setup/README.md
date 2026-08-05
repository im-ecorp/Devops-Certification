# AWX Setup Role

Deploy a disposable AWX test environment on a single-node Kind cluster through
the AWX Operator, expose NodePort `32000` only on host loopback, and configure
host Nginx with Certbot-managed HTTPS.

This role is for testing and evaluation, not production AWX.

## Network design

```text
Internet
   |
host Nginx :80/:443
   |
127.0.0.1:32000
   |
Kind control-plane NodePort
   |
AWX Kubernetes Service
```

Kind maps only NodePort `32000` to `127.0.0.1`. Nginx owns public ports 80 and
443. The role does not install a Kubernetes ingress controller.

## Requirements

- Ubuntu or Debian target
- Docker installed and active
- Root or sudo access
- Public DNS for `awx_hostname` resolving to the target host
- Inbound ports 80 and 443 reachable for Nginx and the initial ACME challenge
- Outbound access to GitHub, Kubernetes, Quay, Docker Hub, and Let's Encrypt

The preflight checks require at least four vCPUs, 6000 MB RAM, 30 GiB free
disk, and a supported `amd64` or `arm64` architecture.

## Important variables

See `defaults/main/main.yml` for the complete list.

| Variable | Default | Description |
|----------|---------|-------------|
| `awx_operator_version` | `2.19.1` | AWX Operator release |
| `awx_cluster_name` | `awx` | Kind cluster and AWX resource name |
| `awx_kubectl_context` | `kind-awx` | Explicit kubectl context |
| `awx_namespace` | `awx` | Kubernetes namespace |
| `awx_nodeport_port` | `32000` | AWX NodePort and host port |
| `awx_nodeport_listen_address` | `127.0.0.1` | Loopback-only Kind mapping |
| `awx_nginx_enabled` | `true` | Configure host Nginx and SSL |
| `awx_hostname` | `awx.k8sforfun.com` | Public AWX hostname |
| `awx_nginx_site_name` | `awx` | Nginx site filename |
| `awx_certbot_email` | Configured in defaults | ACME account email |
| `awx_projects_persistence` | `false` | Disable project persistence |
| `awx_display_admin_password` | `false` | Print the decoded admin password |

## Nginx and certificate workflow

The role:

1. checks whether `nginx` is installed and installs it only when missing;
2. installs Certbot and the Nginx plugin;
3. checks for `/etc/letsencrypt/live/{{ awx_hostname }}/fullchain.pem`;
4. when the certificate is absent, enables a temporary HTTP-only site and runs
   `certbot --nginx` non-interactively;
5. verifies the certificate and Certbot support files;
6. installs the final site in `/etc/nginx/sites-available/awx`;
7. creates `/etc/nginx/sites-enabled/awx` as a symbolic link;
8. runs `nginx -t` before reloading Nginx.

The final site uses the requested long proxy timeouts, disabled buffering, and
WebSocket headers. A separate file under `/etc/nginx/conf.d` defines the
`$connection_upgrade` map required by that configuration.

## Administrator credentials

When `awx_admin_password` is empty, the Operator generates the password in the
`awx-admin-password` Secret. The role does not print it by default.

```bash
kubectl --context kind-awx get secret awx-admin-password \
  -n awx -o jsonpath='{.data.password}' | base64 --decode
echo
```

## Run and tags

```bash
ansible-playbook -i inventory/hosts.yml playbooks/awx.yml --limit <target-host>
```

The current playbook targets `all`, so keep an explicit `--limit` until it is
changed to a dedicated AWX inventory group.

| Tag | Description |
|-----|-------------|
| `preflight_awx` | Validate host prerequisites |
| `create_cluster` | Create or validate the Kind cluster and NodePort mapping |
| `install_operator` | Install the AWX Operator |
| `create_awx` | Apply the AWX custom resource |
| `wait_awx` | Wait for workloads and local HTTP readiness |
| `configure_nginx` | Install/configure Nginx and request SSL when needed |
| `get_password` | Show safe access and password-retrieval information |
| `setup_awx` | Run the complete role |

Kind port mappings are immutable. If an existing cluster does not have the
required `127.0.0.1:32000` mapping, the role stops and does not recreate or
delete the cluster automatically.
