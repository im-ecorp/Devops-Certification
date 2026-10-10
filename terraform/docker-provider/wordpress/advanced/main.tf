# Network for all practice applications
resource "docker_network" "practice_network" {
  name = "${var.project_name}-network"
}

# WordPress Module
module "wordpress" {
  source          = "./modules/wordpress"
  network_name    = docker_network.practice_network.name
  name_prefix     = "${var.project_name}-wordpress"
  port            = var.wordpress_port
  wordpress_image = var.wordpress_image
  database_image  = var.database_image
}

# Future services (e.g., Nginx) can be added as modules here,
# reusing `practice_network`.
