# Terraform Fundamentals

Start here before the application labs. These are independent Terraform projects, not one combined configuration.

| Lab | What it teaches | Requirements |
| --- | --- | --- |
| [Terraform language](terraform-language/README.md) | Inputs, validation, locals, expressions, outputs, and built-in `terraform_data` | Terraform >= 1.6 and < 2.0; no external provider or credentials |
| [Docker container](docker-container/README.md) | Provider initialization, an Nginx image/container, state, and resource changes | Terraform, Docker daemon, free port 8000 |

1. Start with the language lab; its generated server names are strings, not real servers.
2. Continue with Docker to see Terraform manage real resources.
3. Follow each lab's lifecycle checklist from that lab's directory. Do not run Terraform in this parent directory.

The Nginx example publishes port 8000 without a localhost-only bind; use an isolated practice host and restrict access. Review plans before applying or destroying resources.

[Back to Terraform practice](../README.md)
