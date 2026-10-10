# Terraform Docker Practice: WordPress (Advanced)

A modular Terraform practice environment deploying WordPress and MariaDB via the Docker provider. Built for extensibility to add Nginx or other services later.

## Prerequisites

- Terraform >= 1.7
- Docker running locally (`unix:///var/run/docker.sock`)

## Practice Lifecycle

Run these commands in order from `/root/mygit/Devops-Certification/terraform/docker-provider/wordpress/advanced`:

```bash
# 1. Format and initialize
terraform fmt -recursive
terraform init

# 2. Validate configuration locally
terraform validate
terraform test

# 3. Plan and review (requires a running Docker daemon)
terraform plan -out=wordpress.tfplan

# 4. Apply only after reviewing the plan
terraform apply wordpress.tfplan
terraform output wordpress_url
docker ps --filter name=tf-docker-practice-wordpress
curl -I http://localhost:8080/wp-admin/install.php

# Access WordPress at http://localhost:8080 (or custom port)
```

## Optional inputs

Defaults work without a tfvars file. Copy the example only if needed:

```bash
cp -n terraform.tfvars.example terraform.tfvars
# Edit project_name, wordpress_port, or image tags in terraform.tfvars.
```

Image tags receive updates; pin image digests in the input variables for exact reproducibility.
First startup may take a minute while MariaDB initializes. Finish the WordPress installer in the browser; no admin account is pre-created.
On a remote Docker host, localhost refers to that host. Use an SSH tunnel rather than exposing this lab publicly.

## Module tests

Root tests cover module wiring and input validation. Resource tests are separate:

```bash
terraform -chdir=modules/wordpress init -backend=false
terraform -chdir=modules/wordpress validate
terraform -chdir=modules/wordpress test
```

All tests use mocked providers with plan-only runs; they do not verify Docker API behavior, image pulls, or HTTP readiness.

## Cleanup (destructive; run only when ready)

```bash
terraform plan -destroy -out=destroy.tfplan
# Review: applying this removes both containers, images from the daemon state,
# both managed volumes (all WordPress/database data), and the practice network.
terraform apply destroy.tfplan
```

Images have keep_locally enabled, so downloaded images remain cached.

## Security & State Warnings

- **Passwords**: MariaDB passwords are generated using `random_password`. They will be visible in plain text inside your `terraform.tfstate` file. Never commit `.tfstate` files.
- **Persistence**: Container restarts/replacements retain data in `tf-docker-practice-wordpress-data` and `tf-docker-practice-wordpress-db-data`. `terraform destroy` deletes these managed volumes and all lab data. Back up data before destroying. Deleting the state file is not a cleanup method.

## Independent future applications

Add unrelated application labs beside `wordpress/` (for example `../../nginx/basic/`
and `../../nginx/advanced/`), not inside this lab. Each has its own Terraform state.
The reusable module below is retained for learning how modules compose resources;
only WordPress and its database are implemented here.

## Module practice

This project uses a modular design. To add a new service (like Nginx):
1. Create `modules/nginx`.
2. Call it in `main.tf`.
3. Pass `network_name = docker_network.practice_network.name` so all containers share the same network.
