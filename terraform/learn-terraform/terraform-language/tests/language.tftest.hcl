# Plan-only tests: these do not apply resources.
run "default_values" {
  command = plan

  assert {
    condition     = output.full_name == "dev-terraform-practice"
    error_message = "The default name should combine environment and project name."
  }

  assert {
    condition     = output.server_names == ["dev-terraform-practice-1", "dev-terraform-practice-2"]
    error_message = "The default configuration should generate two server names."
  }
}

run "custom_values" {
  command = plan

  variables {
    project_name   = "api"
    environment    = "stage"
    instance_count = 3
  }

  assert {
    condition     = output.full_name == "stage-api"
    error_message = "The name should reflect variable overrides."
  }

  assert {
    condition     = output.server_names == ["stage-api-1", "stage-api-2", "stage-api-3"]
    error_message = "Server names should reflect the requested count."
  }
}

run "reject_zero_instances" {
  command = plan

  variables {
    instance_count = 0
  }

  expect_failures = [var.instance_count]
}
