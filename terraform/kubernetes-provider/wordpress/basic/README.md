# Terraform Kubernetes Practice: WordPress (Basic)

A beginner-friendly WordPress and MariaDB practice lab using direct Terraform resources. No modules or loops. Run commands from this directory; `../advanced/` is a separate Terraform project.

## Prerequisites

- Terraform >= 1.7
- A reachable Kubernetes cluster (e.g., kind, minikube, or Docker Desktop)
- An explicit `kube_context` pointing to your cluster
- A default StorageClass in your cluster (or supply one in variables)

## Practice Lifecycle

Since this requires a sensitive database password, provide it securely as an environment variable rather than hardcoding it in a file.

```bash
# 1. Inspect the cluster and choose an explicit practice context
kubectl config get-contexts
export TF_VAR_kube_context='YOUR_PRACTICE_CONTEXT'
kubectl --context="$TF_VAR_kube_context" get nodes
kubectl --context="$TF_VAR_kube_context" get storageclass

# 2. Set the database user's password without saving it in a tfvars file
read -s TF_VAR_db_password
export TF_VAR_db_password

# 3. Format, initialize, and validate locally
terraform fmt -recursive
terraform init
terraform validate
terraform test

# 4. Review the live plan; apply only to the chosen practice cluster
terraform plan -out=wordpress.tfplan
terraform apply wordpress.tfplan
kubectl --context="$TF_VAR_kube_context" -n tf-k8s-basic-wordpress rollout status deployment/wordpress-mysql
kubectl --context="$TF_VAR_kube_context" -n tf-k8s-basic-wordpress rollout status deployment/wordpress

# 5. Access WordPress locally (leave this command running)
kubectl --context="$TF_VAR_kube_context" -n tf-k8s-basic-wordpress port-forward service/wordpress 8082:80
```

Keep the port-forward running and open `http://localhost:8082` in your browser to finish the WordPress installation.

## Security & State Warnings

- **Passwords**: `db_password` is the WordPress database user password, not the MariaDB root password; MariaDB generates its root password on first start. The user password is stored in Terraform state and plan files even when marked sensitive. Do not commit them. Retain the same password with existing volumes: changing the input does not rotate the stored database account.
- **Persistence**: Pod restarts/replacements retain data in PVCs. Destroying the namespace deletes the PVCs; the storage reclaim policy determines whether underlying disks are deleted. Back up WordPress files and the database first.

## What the files do

- `providers.tf` selects the Kubernetes provider and an explicit context.
- `variables.tf` declares the context, password, and optional StorageClass.
- `main.tf` creates a dedicated namespace, secret, two PVCs, two internal services,
  and two single-replica Deployments. The PVCs keep data across Pod restarts.
- `outputs.tf` prints the local access URL and namespace.

No cluster, ingress, load balancer, or public endpoint is created. The mock test
checks Terraform configuration, not real cluster scheduling or readiness. If no
default StorageClass is available, pass `-var='storage_class_name=YOUR_CLASS'`
when planning. The database may need time to initialize on first startup.

## Cleanup

```bash
kubectl --context="$TF_VAR_kube_context" get namespace tf-k8s-basic-wordpress
terraform plan -destroy -out=destroy.tfplan
# Review carefully: applying this permanently deletes the application, namespace, and ALL persistent data volumes.
terraform apply destroy.tfplan
```
