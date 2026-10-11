# Kubernetes Provider Labs

The Kubernetes provider manages API resources in an existing cluster. These labs do not create a cluster or install Kubernetes.

## WordPress

Both versions create WordPress and MariaDB in a dedicated namespace with a Secret, two PVCs, two Deployments, and internal Services. Access is through local `kubectl port-forward`, not a public endpoint.

| Lab | Design | Default namespace | Local port |
| --- | --- | --- | --- |
| [Basic](wordpress/basic/README.md) | Direct resources and a supplied database password | `tf-k8s-basic-wordpress` | 8082 |
| [Advanced](wordpress/advanced/README.md) | Reusable module, generated passwords, probes, and resource limits | `tf-k8s-practice` | 8081 |

1. Use Terraform >= 1.7 and < 2.0, kubectl, and a reachable practice cluster with persistent storage.
2. Choose an explicit kubeconfig context and inspect its nodes and StorageClass before a live plan.
3. Start with basic, then compare advanced. Run Terraform inside the chosen version directory; each has independent state.

Mock tests need no live cluster and do not verify scheduling, storage provisioning, or readiness. State and saved plans contain secrets. Destroy deletes the namespace and PVCs; the reclaim policy may also delete underlying disks. Use dedicated practice namespaces and back up data first.

[Back to Terraform practice](../README.md)
