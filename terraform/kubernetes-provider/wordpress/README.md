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

Basic uses namespace `tf-k8s-basic-wordpress` and port-forward 8082; advanced uses `tf-k8s-practice` and port-forward 8081. Neither creates a cluster. Both require an explicit practice kube context and persistent storage.
