mock_provider "docker" {}
mock_provider "random" {}
variables {
  network_name = "test-network"
  name_prefix  = "test-wordpress"
}
run "persistent_local_wordpress" {
  command = plan
  assert {
    condition     = one(docker_container.wordpress.ports).ip == "127.0.0.1"
    error_message = "WordPress must bind only to localhost."
  }
  assert {
    condition     = one(docker_container.wordpress.ports).external == 8080 && length(docker_container.mysql.ports) == 0
    error_message = "Only WordPress may publish a host port."
  }
  assert {
    condition     = docker_volume.db_data.name == "test-wordpress-db-data" && docker_volume.wp_data.name == "test-wordpress-data"
    error_message = "Database and WordPress must have persistent volumes."
  }
  assert {
    condition     = docker_image.mysql.name == "mariadb:11.4" && docker_image.wordpress.name == "wordpress:php8.3-apache"
    error_message = "Expected supported database and PHP images."
  }
}
