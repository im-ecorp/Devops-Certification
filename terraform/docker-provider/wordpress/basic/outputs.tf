output "wordpress_url" {
  value       = "http://localhost:${var.wordpress_port}"
  description = "Access URL for WordPress."
}

output "database_container_name" {
  value       = docker_container.mysql.name
  description = "The database container name."
}
