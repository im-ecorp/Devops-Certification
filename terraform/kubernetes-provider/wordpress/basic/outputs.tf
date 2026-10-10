output "wordpress_url" {
  value       = "http://localhost:8082"
  description = "Access WordPress after starting kubectl port-forward."
}

output "namespace" {
  value = kubernetes_namespace.wp_namespace.metadata[0].name
}
