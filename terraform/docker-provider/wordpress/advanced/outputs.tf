output "wordpress_url" {
  value = module.wordpress.wordpress_url
}
output "wordpress_container" {
  value = "${var.project_name}-wordpress-app"
}
output "database_container" {
  value = "${var.project_name}-wordpress-db"
}
