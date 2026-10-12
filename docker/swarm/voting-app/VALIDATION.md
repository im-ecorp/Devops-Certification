# Validation and runtime checklist

## Checks performed (2026-10-12)

- Real Docker CLI **28.5.1** from Docker's official static download, isolated in scratch space, parsed `stack.yaml` with `docker stack config`. No Docker daemon is available in the authoring environment.
- `validate.py` checks the parsed model: five services, no build/dependency/container-name settings, vote replicas=2, other replicas=1, ingress TCP ports 8095/8096, encrypted internal backend overlay, node-local database volume and label placement, and stop-first database updates. It also checks sibling source paths, local documentation links and shell-block syntax.
- `sh -n build-images.sh` passed. A command-capture harness checks all three Buildx commands, vote's `final` target, correct sibling contexts, image tags and fail-fast behavior. This is a script test with a substitute Docker executable, **not an image build or registry push**.
- Shell documentation blocks, local links and YAML/Python syntax checked. Existing Compose source files were not edited or copied.

## Repeat static checks

With Docker CLI (no daemon needed for stack rendering), Python 3 and PyYAML installed, run from this directory:

```bash
python3 validate.py
sh -n build-images.sh
```

`validate.py` requires PyYAML (`python3 -m pip install PyYAML` in a virtual environment). You can pass a Docker CLI path as its first argument. It uses synthetic image names **only for parser checks**, never for deployment. The actual deploy requires your successfully built/pushed images.

## Not verified here

No images were built or pushed. No Swarm was initialized, nodes joined, tasks scheduled, cluster/firewall settings changed, ports published, database accessed, vote written, update rolled back or volume restored. A valid parsed stack does not prove encrypted overlay traffic, resource budgets, image architecture, registry authentication or application data-path behavior.

On dedicated Docker hosts, follow [README.md](README.md) and verify:

1. All nodes Ready; correct private addresses, architecture, trusted inter-node ports and application ingress restrictions.
2. Exactly one database-labeled node; registry images pull successfully on each node.
3. All replicas running; DB/worker/result logs show successful processing, not repeated connection errors.
4. A disposable browser vote appears in results and the PostgreSQL row query. Check each node's ingress path.
5. Stateless drain/scaling exercises behave as expected; never drain/move node-local PostgreSQL as an HA test.
6. Tested new images update according to policy; rollback returns image settings, not database state.
7. Data still exists on the designated node after a controlled task restart. Independently verify a DB backup/restore before any volume or node cleanup.

Public demo credentials, legacy AngularJS result UI, HTTP-only ingress, in-memory Socket.IO state, ephemeral Redis and non-transactional dequeue/write remain explicit limitations. Swarm does not repair these application-level design issues.
