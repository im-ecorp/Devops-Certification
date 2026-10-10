# Kubernetes WordPress practice lab (Advanced)

Terraform root calls `./modules/wordpress`. It creates only WordPress and its
MariaDB dependency: one dedicated namespace, two PVCs, two single-replica
`Recreate` Deployments, two ClusterIP services, and a generated-password Secret.
Images: `mariadb:11.4` and `wordpress:php8.3-apache`. Both workloads have startup,
readiness, and liveness probes plus CPU/memory requests and limits.

## Prerequisites

- Terraform >= 1.7 and < 2.0, kubectl, and an existing reachable Kubernetes cluster.
- A **dedicated practice context** with permissions to create namespace resources.
- A default StorageClass, or supply `-var='storage_class_name=YOUR_CLASS'` on plan.
  The default is `null`; both PVCs request `5Gi` and `ReadWriteOnce`.
- `kube_context` is required with no default; `kube_config_path` defaults to
  `~/.kube/config`. This project does not create a cluster or install tools.

## Lifecycle checklist

1. Select and inspect the explicit target; Terraform never silently selects a context.
   ```bash
   cd /root/mygit/Devops-Certification/terraform/kubernetes-provider/wordpress/advanced
   kubectl config get-contexts
   export TF_VAR_kube_context='YOUR_PRACTICE_CONTEXT'
   export TF_VAR_kube_config_path="$HOME/.kube/config"
   kubectl --kubeconfig="$TF_VAR_kube_config_path" --context="$TF_VAR_kube_context" get nodes
   kubectl --kubeconfig="$TF_VAR_kube_config_path" --context="$TF_VAR_kube_context" get storageclass
   ```
2. Format, initialize, and validate; keep `.terraform.lock.hcl` tracked.
   ```bash
   terraform fmt -check -recursive
   terraform init -backend=false
   terraform validate
   terraform test
   ```
   Tests use mocked Kubernetes/random providers and plan only: no kubeconfig,
   cluster, credentials, or live apply. They do not verify scheduling or API behavior.
3. Review the live plan before applying it to your practice cluster.
   ```bash
   terraform plan -out=lab.tfplan
   terraform apply lab.tfplan
   kubectl --kubeconfig="$TF_VAR_kube_config_path" --context="$TF_VAR_kube_context" -n tf-k8s-practice rollout status deployment/mariadb
   kubectl --kubeconfig="$TF_VAR_kube_config_path" --context="$TF_VAR_kube_context" -n tf-k8s-practice rollout status deployment/wordpress
   ```
4. Access WordPress locally; no Ingress, NodePort, or LoadBalancer is created.
   ```bash
   kubectl --kubeconfig="$TF_VAR_kube_config_path" --context="$TF_VAR_kube_context" --namespace=tf-k8s-practice port-forward service/wordpress 8081:80
   ```
   Open http://localhost:8081 and finish WordPress setup. Keep port-forward bound
   to its default localhost address. Stop with Ctrl+C. If overriding `namespace`,
   replace `tf-k8s-practice` in these commands. `terraform output port_forward_command`
   prints the configured access command.
5. Destroy only after checking the context and backing up required data.
   ```bash
   terraform plan -destroy -out=destroy.tfplan
   terraform apply destroy.tfplan
   ```

## Persistence and safety

- WordPress files persist at `/var/www/html`; MariaDB data persists at
  `/var/lib/mysql`. PVCs survive pod restarts and Deployment replacements.
  `Recreate` prevents overlapping replicas sharing a ReadWriteOnce volume, but
  causes downtime during updates. PVC binding does not block before pod creation,
  supporting StorageClasses using `WaitForFirstConsumer`.
- **Destroy deletes the dedicated namespace and both PVCs. Treat this as data
  loss.** A StorageClass/PV reclaim policy may also delete the underlying disks.
  Do not use an existing shared namespace. Back up files and the database first.
- **Generated database and root passwords are stored in Terraform state**, even
  when marked sensitive; plan files can contain secrets too. Protect state,
  backups, and plan files. They and local tfvars are ignored by Git, not encrypted.
  Kubernetes Secrets also need appropriate RBAC and cluster encryption at rest.
- Passwords are generated once per resource; replacing password resources does
  not reset credentials inside an already initialized MariaDB volume. Avoid
  password replacement unless performing a coordinated database rotation.

## Independent future applications

Add unrelated application labs beside `wordpress/` (for example `../../nginx/basic/`
and `../../nginx/advanced/`), not inside this lab. Each has its own Terraform state.
The reusable module below is retained for learning how modules compose resources;
only WordPress and its database are implemented here.

## Module practice

1. Add a sibling `modules/APP/` with separate provider requirements, variables,
   resources, outputs, and mock plan tests; do not add unrelated resources here.
2. Add a root module block using `source = "./modules/APP"` and pass the existing
   provider configurations explicitly. Keep context configuration in the root.
3. Give the new app its own namespace/storage ownership, expose only deliberate
   outputs, and run fmt/init/validate/test before reviewing a live plan.

No other application modules are implemented in this lab.
