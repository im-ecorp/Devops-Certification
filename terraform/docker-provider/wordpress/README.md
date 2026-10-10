# WordPress practice labs

Start with `basic/`, then compare with `advanced/`.

| Version | Design | Terraform state |
| --- | --- | --- |
| `basic/` | Direct resources; no modules, loops, or dynamic blocks | Independent |
| `advanced/` | Existing modular implementation with reusable WordPress module | Independent |

Each directory is a standalone Terraform project. Run init/plan/apply from that
version's directory and follow its README. Do not run Terraform in this parent.
Only WordPress and its MariaDB dependency are included.

Future unrelated applications should be siblings of `wordpress/`, for example
`../nginx/basic/` and `../nginx/advanced/`, with their own configuration and state.

Basic binds to localhost:8083; advanced to localhost:8080. Network, volume, and container names differ, so both can run independently.
