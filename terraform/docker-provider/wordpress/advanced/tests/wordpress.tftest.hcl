mock_provider "docker" {}
mock_provider "random" {}
run "default_lab" {
  command = plan
  assert {
    condition     = output.wordpress_url == "http://localhost:8080"
    error_message = "WordPress must use the default local port."
  }
  assert {
    condition     = docker_network.practice_network.name == "tf-docker-practice-network"
    error_message = "The practice network must use the project prefix."
  }
}
run "custom_port" {
  command = plan
  variables { wordpress_port = 8090 }
  assert {
    condition     = output.wordpress_url == "http://localhost:8090"
    error_message = "Custom port must reach the module."
  }
}
run "invalid_port" {
  command = plan
  variables { wordpress_port = 80 }
  expect_failures = [var.wordpress_port]
}
