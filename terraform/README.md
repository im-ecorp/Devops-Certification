# Terraform Practice

<p align="center">
  <a href="https://developer.hashicorp.com/terraform">
    <img src="https://www.vectorlogo.zone/logos/terraformio/terraformio-ar21.svg" alt="Terraform — infrastructure as code" width="420">
  </a>
</p>

<p align="center"><strong>Infrastructure as code · Hands-on learning</strong></p>

Terraform describes the infrastructure you want in HCL (`.tf` files). It compares your configuration with state and the real environment, then plans the changes needed to match it.

This directory contains independent practice labs, from language basics to Docker, Kubernetes, and Cloudflare. Start with the language lab, then follow the README in each runnable directory.

## Table of Contents

1. [Installing Terraform](#1-installing-terraform)
2. [Adding Terraform Auto-Completion](#2-adding-terraform-auto-completion)
3. [Practice Labs](#3-practice-labs)
4. [Core Concepts and Files](#4-core-concepts-and-files)
5. [Everyday Workflow](#5-everyday-workflow)

---

## 1. Installing Terraform

HashiCorp distributes Terraform as a binary package. On Debian/Ubuntu systems, install it from the official HashiCorp APT repository.[1]

Run these commands on the machine where you will use Terraform. If you are already root, omit `sudo`. Before proceeding, back up any existing HashiCorp keyring or repository file: the commands below replace those two files.

```bash
# 1. Install prerequisites
sudo apt-get update
sudo apt-get install -y ca-certificates gnupg wget lsb-release

# 2. Install the HashiCorp GPG key
wget -O- https://apt.releases.hashicorp.com/gpg | \
gpg --dearmor | \
sudo tee /usr/share/keyrings/hashicorp-archive-keyring.gpg > /dev/null

# Verify the key fingerprint against the official HashiCorp installation guide
gpg --show-keys --fingerprint /usr/share/keyrings/hashicorp-archive-keyring.gpg

# 3. Add the HashiCorp repository
. /etc/os-release
codename="${UBUNTU_CODENAME:-$VERSION_CODENAME}"
printf 'deb [arch=%s signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com %s main\n' \
  "$(dpkg --print-architecture)" "$codename" | \
  sudo tee /etc/apt/sources.list.d/hashicorp.list

# 4. Update apt and install Terraform
sudo apt-get update
sudo apt-get install terraform

# 5. Verify installation
terraform version
terraform -help
```

---

## 2. Adding Terraform Auto-Completion

Terraform supports tab completion for command names and some command arguments in Bash and Zsh.[2]

Run completion setup as your normal user, **without `sudo`**, so it updates your own shell configuration. Back up existing `~/.bashrc` and `~/.zshrc` files first.

Ensure your shell configuration files exist first:

```bash
touch ~/.bashrc
touch ~/.zshrc
```

Run the built-in install command:

```bash
terraform -install-autocomplete
```

With both configuration files present, the installer adds completion hooks for Bash and Zsh. Restart your shell to activate them.[2]

**Bash:**

```bash
exec bash
```

**Zsh:**

```zsh
exec zsh
```

Type `terraform pl` and press **Tab** to check that it completes to `terraform plan`.

If Zsh completion does not work, ensure its completion system is initialized before the Terraform hook. Oh My Zsh normally handles this; for plain Zsh, place these lines before the generated `bashcompinit` and `complete` lines in `~/.zshrc`:

```zsh
autoload -Uz compinit
compinit
```

## 3. Practice Labs

Use Terraform **1.7 or newer (1.x)** for the provider labs and their mock tests. Docker and Kubernetes labs need their respective runtime; Cloudflare needs a token only for live plans and changes.

| Lab | What you learn | Prerequisites for live practice |
| --- | --- | --- |
| [Terraform language](learn-terraform/terraform-language/README.md) | Variables, validation, locals, `for` expressions, outputs, and state | Terraform only; no real servers |
| [Docker container](learn-terraform/docker-container/README.md) | Manage one Nginx image and container | Docker daemon; free port 8000 |
| [Docker WordPress](docker-provider/wordpress/README.md) | Networks, volumes, dependencies; direct resources versus modules | Docker daemon; basic port 8083 / advanced port 8080 |
| [Kubernetes WordPress](kubernetes-provider/wordpress/README.md) | Namespaces, Secrets, PVCs, Deployments, Services, and modules | Existing practice cluster, explicit context, StorageClass, kubectl |
| [Cloudflare DNS](cloudflare-provider/README.md) | Manage A, CNAME, TXT, and MX records | Existing zone and scoped DNS API token |

Each lab has its own state. Run Terraform inside a directory containing `.tf` files, **not** in this directory or the category directories. For WordPress, start with `basic/`, then compare `advanced/`; these are separate projects, not upgrade steps.

## 4. Core Concepts and Files

- **Provider:** a plugin that talks to an API, such as Docker, Kubernetes, or Cloudflare.
- **Resource:** an object Terraform manages, such as a container or DNS record.
- **Variable / local / output:** inputs you supply, values calculated inside the configuration, and results exposed by it.
- **Module:** reusable Terraform configuration called by another configuration. The directory where you run Terraform is the root module.
- **State:** Terraform's mapping between resource addresses and real objects. Do not delete it to clean up infrastructure.

| File | Purpose |
| --- | --- |
| `main.tf` | Resources, calculations, and module calls |
| `providers.tf` / `versions.tf` | Provider configuration and version requirements; some labs put these in `main.tf` |
| `variables.tf` / `outputs.tf` | Input definitions and exported results |
| `terraform.tfvars` | Local input values; copy an example only if present and needed |
| `.terraform.lock.hcl` | Selected provider versions and checksums; commit it |
| `terraform.tfstate` | Managed-resource state; protect it and keep it out of Git |
| `tests/*.tftest.hcl` | Automated assertions where provided |

All `.tf` files in a directory are loaded together; their filenames do not determine execution order. Resource references establish dependencies.

## 5. Everyday Workflow

Follow the selected lab's prerequisites and inputs first. From its runnable directory:

1. Format, initialize providers/modules, and validate configuration.
   ```bash
   terraform fmt -check -recursive
   terraform init
   terraform validate
   ```
   If formatting fails, run `terraform fmt -recursive`, then check again.
2. Run tests **where provided** and review the live plan.
   ```bash
   terraform test
   terraform plan
   ```
   Existing provider tests use mock providers and plan-only runs: they do not create infrastructure or prove API access/readiness. Live `plan` usually needs the real runtime or credentials.
3. Apply only after reviewing the changes, then inspect results.
   ```bash
   terraform apply
   terraform output
   terraform state list
   terraform plan
   ```
   `apply` generates a fresh plan and asks for approval. With unchanged inputs and no drift, the final plan should report no changes. Applying a saved plan (`terraform apply FILE.tfplan`) does **not** ask again.
4. Clean up only when finished and after backing up required data.
   ```bash
   terraform plan -destroy
   terraform destroy
   ```
   **Destroy removes this lab's managed resources. WordPress cleanup can delete database and application data.** Review the destruction plan before confirming.

Keep state, state backups, saved plans, local tfvars, and `.terraform/` out of Git. `sensitive = true` hides values in normal output; it does not encrypt secrets in state or saved plans. Never commit API tokens or passwords.

*Image: [Vector Logo Zone](https://www.vectorlogo.zone/logos/terraformio/).*

Sources:

[1] https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli
[2] https://developer.hashicorp.com/terraform/cli/commands
