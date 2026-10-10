# Terraform Docker Practice: WordPress (Basic)

A beginner-friendly, straightforward implementation of WordPress on Docker using Terraform. No modules, no dynamic loops, just direct understandable resources.

## Prerequisites

- Terraform >= 1.7
- Docker running locally (`unix:///var/run/docker.sock`)

## Practice Lifecycle

Run commands from `/root/mygit/Devops-Certification/terraform/docker-provider/wordpress/basic`.

Since this requires a sensitive database password, provide it securely as an environment variable rather than hardcoding it in a file.

```bash
# 1. Format and initialize
terraform fmt -recursive
terraform init

# 2. Set the password securely (type your practice password and press Enter)
read -s TF_VAR_db_password
export TF_VAR_db_password

# 3. Validate configuration locally
terraform validate
terraform test

# 4. Plan and review (requires Docker daemon)
terraform plan -out=wordpress.tfplan

# 5. Apply only after reviewing the plan
terraform apply wordpress.tfplan

# Output check
terraform output wordpress_url
docker ps --filter name=tf-docker-basic-wp
curl -I http://localhost:8083/wp-admin/install.php
```

## How the files work

- `providers.tf`: connects Terraform to Docker.
- `variables.tf`: simple inputs, including a password with no committed default.
- `main.tf`: network, two persistent volumes, two images, and two containers.
- `outputs.tf`: prints the access URL and database container name.

Docker DNS resolves the database container name on the dedicated network. Only
WordPress publishes a host port; the database stays internal. `depends_on` sets
creation order, not database readiness. Wait a minute on first startup and retry
the URL if the database is still initializing. Finish the WordPress installer
in your browser; no WordPress admin user is pre-created.

Basic defaults to port 8083; advanced uses 8080. Both can run independently.
This is a local practice lab, not a production deployment. Image tags can change;
pin digests when exact reproducibility is needed. Mock tests validate configuration
only, not image pulls, Docker availability, or HTTP/database readiness.

## Security & State Warnings

- **Passwords**: `db_password` will be visible in plain text inside your `terraform.tfstate` file after applying. Never commit `.tfstate` files to version control.
- **Persistence**: Container restarts/replacements retain data in the managed Docker volumes. Running `terraform destroy` deletes these managed volumes (and all WordPress files/database data) along with the containers and network.
- **Root Password**: MariaDB generates a root password on first startup and prints it in its logs. Treat those logs as sensitive. Keep using the same `db_password` with existing volumes: changing this input does not rotate the stored database account password.
- Protect saved plan files too: marking an input sensitive only hides display, not the secrets in state or plans.

## Cleanup

```bash
terraform plan -destroy -out=destroy.tfplan
# Review carefully: applying this permanently deletes the application, network, and ALL persistent data volumes.
terraform apply destroy.tfplan
```
