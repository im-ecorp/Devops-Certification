# Core configuration using built-in language features
terraform {
  required_version = ">= 1.6.0, < 2.0.0"
}

# Local values compute reusable expressions
locals {
  full_name = "${var.environment}-${var.project_name}"

  # A for expression to generate a list of names
  server_names = [
    for i in range(1, var.instance_count + 1) :
    "${local.full_name}-${i}"
  ]

  # Common metadata tags
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Built-in resource to simulate state without external providers
resource "terraform_data" "service" {
  input = {
    name    = local.full_name
    servers = local.server_names
    tags    = local.common_tags
  }
}
