# Terraform Practice

<p align="center">
  <a href="https://developer.hashicorp.com/terraform">
    <img src="https://www.vectorlogo.zone/logos/terraformio/terraformio-ar21.svg" alt="Terraform — infrastructure as code" width="420">
  </a>
</p>

<p align="center"><strong>Infrastructure as code · Hands-on learning</strong></p>

This directory contains practice labs for learning Terraform.

## Table of Contents

1. [Installing Terraform](#1-installing-terraform)
2. [Adding Terraform Auto-Completion](#2-adding-terraform-auto-completion)

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

*Image: [Vector Logo Zone](https://www.vectorlogo.zone/logos/terraformio/).*

Sources:

[1] https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli
[2] https://developer.hashicorp.com/terraform/cli/commands
