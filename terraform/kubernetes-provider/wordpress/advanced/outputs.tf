output "namespace" {
  description = "Namespace containing the practice lab."
  value       = module.wordpress.namespace
}

output "deployments" {
  description = "Deployment names, replicas, and rollout strategies."
  value       = module.wordpress.deployments
}

output "persistent_volume_claims" {
  description = "PVC names and requested storage (no passwords)."
  value       = module.wordpress.persistent_volume_claims
}

output "services" {
  description = "Internal service names, types, and ports."
  value       = module.wordpress.services
}

output "port_forward_command" {
  description = "Local-only access command; run separately with kubectl."
  value       = "kubectl --kubeconfig=${pathexpand(var.kube_config_path)} --context=${var.kube_context} --namespace=${module.wordpress.namespace} port-forward service/wordpress 8081:80"
}
