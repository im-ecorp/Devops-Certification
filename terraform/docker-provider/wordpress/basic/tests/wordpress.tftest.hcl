mock_provider "docker" {}

variables {
  # Fake credentials required to run the test plan without prompting
  db_password    = "test-password-only"
  wordpress_port = 8083
  project_name   = "test-project"
}

run "validate_basic_deployment" {
  command = plan

  assert {
    condition     = docker_network.wp_network.name == "test-project-network"
    error_message = "Network name must use the project prefix."
  }

  assert {
    condition     = length(docker_container.wordpress.ports) > 0 && one(docker_container.wordpress.ports).ip == "127.0.0.1"
    error_message = "WordPress should only listen on localhost."
  }

  assert {
    condition     = length(docker_container.mysql.ports) == 0 && docker_volume.db_data.name == "test-project-db-data" && docker_volume.wp_data.name == "test-project-app-data"
    error_message = "Database must be internal, and both applications must have persistent volumes."
  }

  assert {
    condition     = output.wordpress_url == "http://localhost:8083"
    error_message = "URL must match the port variable."
  }
}
