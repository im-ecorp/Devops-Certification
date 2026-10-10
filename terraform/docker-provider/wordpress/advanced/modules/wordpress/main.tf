resource "random_password" "database" {
  length  = 24
  special = false
}
resource "random_password" "root" {
  length  = 32
  special = false
}
resource "docker_volume" "db_data" {
  name = "${var.name_prefix}-db-data"
}

resource "docker_volume" "wp_data" {
  name = "${var.name_prefix}-data"
}

resource "docker_image" "mysql" {
  name         = var.database_image
  keep_locally = true
}

resource "docker_image" "wordpress" {
  name         = var.wordpress_image
  keep_locally = true
}

resource "docker_container" "mysql" {
  name  = "${var.name_prefix}-db"
  image = docker_image.mysql.image_id

  env = [
    "MARIADB_ROOT_PASSWORD=${random_password.root.result}",
    "MARIADB_DATABASE=wordpress",
    "MARIADB_USER=wordpress",
    "MARIADB_PASSWORD=${random_password.database.result}"
  ]

  networks_advanced {
    name = var.network_name
  }

  volumes {
    volume_name    = docker_volume.db_data.name
    container_path = "/var/lib/mysql"
  }

  healthcheck {
    test         = ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
    interval     = "10s"
    timeout      = "5s"
    retries      = 12
    start_period = "30s"
  }
  memory  = 512
  restart = "unless-stopped"
}

resource "docker_container" "wordpress" {
  name  = "${var.name_prefix}-app"
  image = docker_image.wordpress.image_id

  env = [
    "WORDPRESS_DB_HOST=${var.name_prefix}-db:3306",
    "WORDPRESS_DB_NAME=wordpress",
    "WORDPRESS_DB_USER=wordpress",
    "WORDPRESS_DB_PASSWORD=${random_password.database.result}"
  ]

  networks_advanced {
    name = var.network_name
  }

  ports {
    internal = 80
    external = var.port
    ip       = "127.0.0.1"
  }

  volumes {
    volume_name    = docker_volume.wp_data.name
    container_path = "/var/www/html"
  }

  restart = "unless-stopped"

  healthcheck {
    test         = ["CMD-SHELL", "curl -fsS http://127.0.0.1/wp-admin/install.php >/dev/null || exit 1"]
    interval     = "15s"
    timeout      = "5s"
    retries      = 20
    start_period = "30s"
  }
  memory = 512
  depends_on = [
    docker_container.mysql
  ]
}
