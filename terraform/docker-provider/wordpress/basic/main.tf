# 1. A dedicated network so containers can talk to each other
resource "docker_network" "wp_network" {
  name = "${var.project_name}-network"
}

# 2. Volumes to persist data when containers are recreated or stopped
resource "docker_volume" "db_data" {
  name = "${var.project_name}-db-data"
}

resource "docker_volume" "wp_data" {
  name = "${var.project_name}-app-data"
}

# 3. Pull images; keep them cached after terraform destroy
resource "docker_image" "mysql" {
  name         = "mariadb:11.4"
  keep_locally = true
}

resource "docker_image" "wordpress" {
  name         = "wordpress:php8.3-apache"
  keep_locally = true
}

# 4. The database container
resource "docker_container" "mysql" {
  name  = "${var.project_name}-db"
  image = docker_image.mysql.image_id

  env = [
    "MARIADB_RANDOM_ROOT_PASSWORD=yes",
    "MARIADB_DATABASE=wordpress",
    "MARIADB_USER=wordpress",
    "MARIADB_PASSWORD=${var.db_password}"
  ]

  networks_advanced {
    name = docker_network.wp_network.name
  }

  volumes {
    volume_name    = docker_volume.db_data.name
    container_path = "/var/lib/mysql"
  }

  restart = "unless-stopped"
}

# 5. The WordPress container
resource "docker_container" "wordpress" {
  name  = "${var.project_name}-app"
  image = docker_image.wordpress.image_id

  env = [
    "WORDPRESS_DB_HOST=${var.project_name}-db:3306",
    "WORDPRESS_DB_NAME=wordpress",
    "WORDPRESS_DB_USER=wordpress",
    "WORDPRESS_DB_PASSWORD=${var.db_password}"
  ]

  networks_advanced {
    name = docker_network.wp_network.name
  }

  ports {
    internal = 80
    external = var.wordpress_port
    ip       = "127.0.0.1" # Listen only on localhost for security
  }

  volumes {
    volume_name    = docker_volume.wp_data.name
    container_path = "/var/www/html"
  }

  restart = "unless-stopped"

  # Creation order only; MariaDB may take time to become ready.
  depends_on = [
    docker_container.mysql
  ]
}
