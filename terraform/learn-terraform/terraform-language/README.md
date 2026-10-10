# Language Example Practice

This lab shows core Terraform language features without external providers or cloud credentials. `server_names` are calculated strings, **not real servers**. The `terraform_data` resource is built into Terraform and only stores practice data in Terraform state.

## Files

- `variables.tf`: Input variables and validation logic.
- `main.tf`: Local calculations (string interpolation, `for` expressions) and a built-in `terraform_data` resource.
- `outputs.tf`: Exported data values.

## How to practice

Requires Terraform **1.6 or newer (1.x)**. Run these commands from this directory:

```bash
cd /root/mygit/Devops-Certification/terraform/learn-terraform/terraform-language
```

```bash
terraform fmt

# Initialize the working directory
terraform init

# Validate configuration syntax
terraform validate


# Optional: run automated plan-only checks
terraform test

# View proposed changes without applying
terraform plan

# Apply the changes (type 'yes' when prompted)
terraform apply

# Inspect the current state
terraform show
terraform output
terraform state list
```

Try passing different variables to see how `locals` compute the results:

```bash
terraform plan -var="environment=stage" -var="instance_count=5"
```

`-var` only applies to that command. Pass the same overrides to `terraform apply` if you want to store those values.

## Exercises

1. Predict the default `full_name` and `server_names` before running `plan`.
2. Set `project_name` to `api` and `environment` to `stage`. Compare the plan.
3. Change `instance_count` to `3`. Read the `for` expression in `main.tf`.
4. Try `-var="environment=test"` and `-var="instance_count=0"`. Explain the validation errors.
5. Run `terraform console`, evaluate `local.full_name` and `local.common_tags["Environment"]`, then type `exit`.
6. After an apply, run `terraform plan` again. With unchanged inputs, expect no changes.

Optional cleanup, only when you want to remove this lab's tracked state object:

```bash
terraform plan -destroy
terraform destroy
```

Review the destruction plan before confirming. Do not delete the state file manually.
