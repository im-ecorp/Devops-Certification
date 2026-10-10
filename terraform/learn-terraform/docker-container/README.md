# Docker Container Practice

Requires Terraform and a running Docker daemon; port **8000** must be available.

Run these commands one at a time, reviewing each result:

```bash
cd /root/mygit/Devops-Certification/terraform/learn-terraform/docker-container
docker info
```

```bash
# 1. Format configuration files to standard style
terraform fmt

# 2. Download and configure the Docker provider plugin
terraform init

# 3. Check for syntax errors and internal consistency
terraform validate

# 4. Review actions Terraform will take before changing infrastructure
terraform plan

# 5. Create the image and run the container
terraform apply

# 6. List resources tracked in local state
terraform state list

# 7. Print all current output values
terraform output

# 8. Verify Nginx
docker ps
curl http://localhost:8000

# 9. Confirm a second plan needs no changes
terraform plan
```

`terraform apply` changes Docker resources; review its plan before typing `yes`.

After editing `.tf` files, repeat `fmt`, `validate`, `plan`, then `apply`. Run `init` again when provider requirements change.

**Optional cleanup:** removes the managed container and image. Only run when finished, and review before confirming:

```bash
terraform plan -destroy
terraform destroy
```

Keep state files out of Git; do not delete them manually. Commit `.terraform.lock.hcl`.
