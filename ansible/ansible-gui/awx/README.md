# AWX Test Environment with Kind and AWX Operator

This guide deploys a **temporary AWX environment** using Docker, Kind, and the AWX Operator.

It is intended for testing AWX functionality before building a production deployment.

## Architecture

```text
Docker
└── Kind cluster: awx
    └── Namespace: awx
        ├── AWX Operator
        ├── AWX web
        ├── AWX task
        ├── PostgreSQL
        └── Redis
```

For this disposable environment:

- Use Kind on Docker.
- Install AWX through the AWX Operator.
- Let the Operator create the internal PostgreSQL instance.
- Expose AWX through a local NodePort.
- Bind the exposed port to `127.0.0.1`.
- Skip TLS, high availability, external PostgreSQL, backups, and persistent project storage.
- Delete the complete environment with one command.

This approach is preferable to the raw AWX Docker Compose development environment because it tests the same Operator-based deployment model commonly used for Kubernetes installations.

> AWX's direct Docker development environment is intended for development and testing and does not have an officially published production release.

## Server Requirements

Recommended test server resources:

```text
CPU:     4 vCPU minimum
RAM:     6 GB minimum; 8 GB recommended
Disk:    30–40 GB
OS:      Ubuntu 22.04/24.04 or Debian
Docker:  Installed and running
```

The official AWX testing documentation uses four CPUs and 6 GB of RAM as a starting point.

## Prerequisites

Before starting, confirm that:

- You have root access or equivalent `sudo` privileges.
- Docker is installed and running.
- TCP port `32000` is not already in use.
- The server can access GitHub, Quay, Docker registries, and Kubernetes download endpoints.

---

## 1. Verify Docker

```bash
docker version
docker info
```

Confirm that the Docker daemon is running:

```bash
systemctl is-active docker
```

Expected result:

```text
active
```

---

## 2. Install kubectl

Detect the system architecture:

```bash
ARCH="$(uname -m)"

case "$ARCH" in
  x86_64)
    KUBECTL_ARCH="amd64"
    ;;
  aarch64|arm64)
    KUBECTL_ARCH="arm64"
    ;;
  *)
    echo "Unsupported architecture: $ARCH"
    exit 1
    ;;
esac
```

Download and install the latest stable `kubectl`:

```bash
KUBECTL_VERSION="$(curl -L -s https://dl.k8s.io/release/stable.txt)"

curl -fLO \
  "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/${KUBECTL_ARCH}/kubectl"

install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm -f kubectl
```

Verify the installation:

```bash
kubectl version --client
```

---

## 3. Install Kind

Detect the system architecture and latest Kind release:

```bash
ARCH="$(uname -m)"

case "$ARCH" in
  x86_64)
    KIND_ARCH="amd64"
    ;;
  aarch64|arm64)
    KIND_ARCH="arm64"
    ;;
  *)
    echo "Unsupported architecture: $ARCH"
    exit 1
    ;;
esac

KIND_VERSION="$(
  curl -fsSL https://api.github.com/repos/kubernetes-sigs/kind/releases/latest |
  sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p' |
  head -n1
)"
```

Make sure a version was detected:

```bash
if [ -z "$KIND_VERSION" ]; then
  echo "Unable to determine the latest Kind version."
  exit 1
fi
```

Download and install Kind:

```bash
curl -fLo /usr/local/bin/kind \
  "https://kind.sigs.k8s.io/dl/${KIND_VERSION}/kind-linux-${KIND_ARCH}"

chmod +x /usr/local/bin/kind
```

Verify the installation:

```bash
kind version
```

---

## 4. Create the Kind Cluster

Create the project directory:

```bash
mkdir -p /opt/awx
cd /opt/awx
```

Create the Kind configuration:

```bash
cat >kind-config.yaml <<'EOF'
apiVersion: kind.x-k8s.io/v1alpha4
kind: Cluster

nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 32000
        hostPort: 32000
        listenAddress: "127.0.0.1"
        protocol: TCP
EOF
```

The `listenAddress` setting ensures that AWX is accessible only from the server itself. It is not exposed directly to the public network.

Create the cluster:

```bash
kind create cluster \
  --name awx \
  --config kind-config.yaml
```

Verify the cluster:

```bash
kubectl cluster-info --context kind-awx
kubectl get nodes
kubectl get pods -A
```

Expected node status:

```text
NAME                STATUS   ROLES           AGE   VERSION
awx-control-plane   Ready    control-plane   ...   ...
```

Confirm the active context:

```bash
kubectl config current-context
```

Expected result:

```text
kind-awx
```

---

## 5. Install the AWX Operator

Change to the project directory:

```bash
cd /opt/awx
```

Set the AWX Operator version:

```bash
export AWX_OPERATOR_VERSION="2.19.1"
```

Create `kustomization.yaml`:

```bash
cat >kustomization.yaml <<EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - github.com/ansible/awx-operator/config/default?ref=${AWX_OPERATOR_VERSION}

images:
  - name: quay.io/ansible/awx-operator
    newTag: ${AWX_OPERATOR_VERSION}

namespace: awx
EOF
```

Apply the AWX Operator:

```bash
kubectl apply -k .
```

Wait for the Operator deployment:

```bash
kubectl rollout status \
  deployment/awx-operator-controller-manager \
  -n awx \
  --timeout=300s
```

Verify the Operator pod:

```bash
kubectl get pods -n awx
```

Expected output should include a pod similar to:

```text
awx-operator-controller-manager-...
```

### Confirm Operator Container Images

```bash
OPERATOR_POD="$(
  kubectl get pod \
    -n awx \
    -l control-plane=controller-manager \
    -o jsonpath='{.items[0].metadata.name}'
)"

kubectl get pod "$OPERATOR_POD" \
  -n awx \
  -o jsonpath='{range .status.containerStatuses[*]}{.name}{"\t"}{.image}{"\t"}{.ready}{"\t"}{.state.waiting.reason}{"\n"}{end}'
```

---

## 6. Create the AWX Instance

Create `/opt/awx/awx.yaml`:

```bash
cat >/opt/awx/awx.yaml <<'EOF'
apiVersion: awx.ansible.com/v1beta1
kind: AWX

metadata:
  name: awx
  namespace: awx

spec:
  service_type: nodeport
  nodeport_port: 32000

  projects_persistence: false

  web_replicas: 1
  task_replicas: 1

  web_resource_requirements:
    requests:
      cpu: 250m
      memory: 512Mi
    limits:
      cpu: "1"
      memory: 2Gi

  task_resource_requirements:
    requests:
      cpu: 500m
      memory: 1Gi
    limits:
      cpu: "2"
      memory: 3Gi
EOF
```

Apply the AWX custom resource:

```bash
kubectl apply -f /opt/awx/awx.yaml
```

Verify that the AWX resource exists:

```bash
kubectl get awx -n awx
```

For this test deployment, the Operator automatically creates resources for:

```text
AWX web and task services
PostgreSQL
Redis
AWX NodePort service
Admin password secret
AWX secret key
Persistent PostgreSQL storage
```

---

## 7. Monitor the Installation

Watch the AWX pods:

```bash
kubectl get pods -n awx -w
```

Press `Ctrl+C` to stop watching.

After deployment, you should see pods similar to:

```text
awx-operator-controller-manager-...
awx-postgres-15-0
awx-task-...
awx-web-...
```

Follow the Operator logs:

```bash
kubectl logs -f \
  deployment/awx-operator-controller-manager \
  -n awx \
  -c awx-manager
```

Check the AWX resource status:

```bash
kubectl get awx awx -n awx -o yaml
```

AWX is ready when its main pods are running and all expected containers show as ready:

```bash
kubectl get pods -n awx
```

Example:

```text
NAME                                               READY   STATUS    RESTARTS   AGE
awx-operator-controller-manager-...                2/2     Running   0          ...
awx-postgres-15-0                                  1/1     Running   0          ...
awx-task-...                                       4/4     Running   0          ...
awx-web-...                                        3/3     Running   0          ...
```

---

## 8. Retrieve the Admin Password

The default username is:

```text
admin
```

Retrieve the generated password:

```bash
kubectl get secret awx-admin-password \
  -n awx \
  -o jsonpath='{.data.password}' |
  base64 --decode

echo
```

Store the password temporarily in a shell variable when needed:

```bash
AWX_ADMIN_PASSWORD="$(
  kubectl get secret awx-admin-password \
    -n awx \
    -o jsonpath='{.data.password}' |
    base64 --decode
)"

printf '%s\n' "$AWX_ADMIN_PASSWORD"
```

Do not commit generated passwords or Kubernetes secrets to Git.

---

## 9. Access AWX

Confirm the service:

```bash
kubectl get service awx-service -n awx
```

Test the local endpoint from the server:

```bash
curl -I http://127.0.0.1:32000
```

Because the NodePort is bound to `127.0.0.1`, create an SSH tunnel from your local computer:

```bash
ssh -L 32000:127.0.0.1:32000 root@YOUR_SERVER_IP
```

Keep the SSH session open, then visit:

```text
http://127.0.0.1:32000
```

Login credentials:

```text
Username: admin
Password: generated password from the previous step
```

To run the SSH tunnel in the background:

```bash
ssh -fNT \
  -L 32000:127.0.0.1:32000 \
  root@YOUR_SERVER_IP
```


---

## References

- [AWX Installation Documentation](https://github.com/ansible/awx/blob/devel/INSTALL.md)
- [Creating a Minikube Cluster for Testing](https://ansible.readthedocs.io/projects/awx-operator/en/latest/installation/creating-a-minikube-cluster-for-testing.html)
- [AWX Operator on Kind](https://ansible.readthedocs.io/projects/awx-operator/en/latest/installation/kind-install.html)
- [AWX Operator Releases](https://github.com/ansible/awx-operator/releases)
- [AWX Operator Basic Installation](https://ansible.readthedocs.io/projects/awx-operator/en/latest/installation/basic-install.html)
- [Kind Documentation](https://kind.sigs.k8s.io/)
- [kubectl Installation Documentation](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)