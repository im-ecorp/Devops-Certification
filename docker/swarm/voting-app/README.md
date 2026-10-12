# Voting App on Docker Swarm

A five-service Swarm learning stack using the maintained [Voting Compose source](../../scenario/voting-app/UPSTREAM.md). This is a **local/private-network educational deployment**, not a production voting system. Read the [Swarm setup guide](../README.md) first. A single-node Swarm is enough to learn stacks; two nodes demonstrate routing and placement.

## Architecture and constraints

```text
trusted browser -> any node:8095 -> vote x2 (Python/Flask) -> Redis list
trusted browser -> any node:8096 -> result x1 (Node/Socket.IO) -> PostgreSQL
                                                        worker x1 (C#) <- Redis list
PostgreSQL x1 -> node-local db-data on labeled node
```

The services communicate through an internal, encrypted `backend` overlay. Only
`vote` and `result` publish HTTP through ingress. Redis and PostgreSQL have no
published ports. The `frontend` overlay joins browser-facing services (it is not
a firewall). `vote` has two replicas; `result`, `worker`, `redis` and `db` have
one each. Swarm service-name DNS (`redis`, `db`) matches the existing source.
There is **no Compose `depends_on` in Swarm**: the worker retries Redis/DB
connections; the result retries its DB query. Watch startup logs until ready.

`stack.yaml` is a Swarm stack file, not a substitute for the existing Compose
`compose.yaml`: Docker's `stack deploy` does **not** build images and does not
support modern Compose features uniformly. The script builds the three existing
Dockerfiles from `../../scenario/voting-app/upstream/` (no duplicate app copy).
Both reference images are pulled from Docker Hub. The worker Dockerfile uses
multi-platform build arguments, but the documented build targets Linux amd64.

**Security and reliability boundary:** Upstream result and worker code embed the
**public demo** `postgres/postgres` credential; changing only the stack's DB
environment breaks them. Do not reuse this configuration on a public network.
Swarm ingress publishes `8095`/`8096` on *all nodes/interfaces*, not only on
`127.0.0.1`; restrict access with trusted network/firewall/load balancer before
deployment. HTTP has no TLS/auth. Browser voter cookies are not identity.
Result Socket.IO holds client state in process and runs one replica. Redis is
ephemeral, and the worker pops before writing: DB errors/restarts can lose
votes. PostgreSQL's local volume is **not** shared or backed up by Swarm.

## Prerequisites

1. Docker Engine with Swarm mode enabled on your private Linux hosts; check
   `docker node ls` **on a manager**. For a multi-node cluster, allow Swarm
   control/data ports between trusted hosts, including ESP for encrypted overlay
   as described in the [Swarm guide](../README.md#prepare-hosts).
2. Registry that every node can reach, credentials for pushing/pulling, Docker
   Buildx, and appropriate architecture. Authenticate securely (`docker login`)
   on the builder and nodes; **never put registry tokens in shell history or Git**.
   Private registries can use `docker stack deploy --with-registry-auth`; the
   registry access token is distributed to Swarm agents, so restrict access.
3. A Linux amd64 node with sufficient memory/disk for PostgreSQL. **Choose a
   dedicated data node with no existing votes.** Do not repurpose a node-local
   volume from another stack. Assign its label on the manager:

   ```bash
   docker node ls
   docker node update --label-add voting-db=true 'DATA_NODE_HOSTNAME'
   docker node inspect 'DATA_NODE_HOSTNAME' --pretty
   ```

   Use the actual hostname shown by `docker node ls`. The label pins only the
   **database**. Local Docker volume `voting_db-data` remains on that node; if
   the node fails, DB tasks stay pending until it returns. Do not label a second
   node with this key unless you also implement storage replication and restore.
4. Ensure TCP 8095/8096 are free and permitted **only from trusted lab clients**
   on every participating node. Check any existing firewall/routing policy first.
   The data node and other nodes must reach your registry.

## Build and distribute images

From **this** directory on a builder with access to the full repository, choose
an image repository prefix you own and a unique immutable version tag (for
example, an inspected Git revision). Do not use `latest` as a deployment
rollback strategy. Replace the example registry path:

```bash
export IMAGE_PREFIX='ghcr.io/YOUR_ACCOUNT/swarm-voting'
export IMAGE_TAG="$(git rev-parse --short=12 HEAD)"
export PLATFORM='linux/amd64'
sh ./build-images.sh
```

The script uses `docker buildx build --push` for `vote`, `result`, and `worker`.
It needs registry access and a Buildx builder able to push; image builds may
take time and send source to the selected builder. **Inspect the registry tags
and image architecture before deployment.** `IMAGE_PREFIX-vote:IMAGE_TAG`,
`-result`, and `-worker` must all be pullable by workers. A failed build/push
must be fixed before proceeding. Redis/Postgres use versioned upstream tags;
for reproducible releases, pin verified digests for **all five** images.

On the manager, in this directory, map the three image variables. If you build
on another host, transfer the `stack.yaml` and use the exact same image names.
Do not put credentials in these variables:

```bash
export VOTE_IMAGE="${IMAGE_PREFIX}-vote:${IMAGE_TAG}"
export RESULT_IMAGE="${IMAGE_PREFIX}-result:${IMAGE_TAG}"
export WORKER_IMAGE="${IMAGE_PREFIX}-worker:${IMAGE_TAG}"
docker stack config -c stack.yaml > /dev/null
```

`docker stack config` renders the stack; it does not build or start containers.
`stack deploy` uses your shell environment for variable substitution. There is
no auto-loaded `.env` like many Compose workflows. Use a registry tag tied to
this source version; update all three variables together. Redis and Postgres
use family tags in the example; pin their tested digests when repeatability matters.

## Deploy and inspect

These commands **change** a running Swarm and may publish ports on every node.
Run only on a private lab cluster where you have approved the placement, registry
images, and reachable client networks:

```bash
docker stack deploy --with-registry-auth -c stack.yaml voting
docker stack services voting
docker stack ps voting --no-trunc
docker service ps voting_db --no-trunc
docker service logs --tail 100 voting_worker
docker service logs --tail 100 voting_result
```

If images are public, omit `--with-registry-auth`. Swarm image pulls, network
setup and DB initialization are asynchronous. `REPLICAS` should eventually
show `vote 2/2`, each other service `1/1`. Check task errors if they remain
`0/1`. Inspect the result logs if the worker creates the table after the result
starts. A healthy web response does not prove data-path correctness.

On a trusted client **inside your private network**, replace the IP with any
node's reachable address. The ingress routing mesh forwards to available tasks
regardless of which node receives the request:

```bash
curl -fsS http://192.168.50.10:8095/ > /dev/null
curl -fsS http://192.168.50.11:8096/ > /dev/null
```

Open the vote page at `http://192.168.50.10:8095/` and the results at
`http://192.168.50.10:8096/`. Cast a **disposable test vote**. The result should
update after polling; a repeat from the same browser changes that cookie's vote.
Inspect the DB from its currently running task **on the data node** (find it
with `docker service ps voting_db`, then `docker ps` on that node):

```bash
# On the labeled data node, substitute the real running container ID:
docker exec -it 'DB_CONTAINER_ID' psql -U postgres -d postgres \
  -c 'SELECT vote, COUNT(*) FROM votes GROUP BY vote;'
```

This query verifies persisted rows but does not prove backup/recovery. Do not
cast real votes; this app has no authentication or reliable queue semantics.

## Explore scheduling and updates safely

1. Inspect placement with `docker service ps voting_vote` and
   `docker service ps voting_db`. To test routing while a stateless node is
   unavailable, drain only a node **without PostgreSQL and without the only
   viable Redis/data task**. Verify alternate capacity first. Swarm reschedules
   eligible stateless replicas; the label-pinned DB cannot move safely.
2. `docker service scale voting_vote=3` demonstrates a temporary third vote
   replica. Restore with `docker service scale voting_vote=2`. `docker stack
   deploy` re-applies the desired count in `stack.yaml`.
3. To update, publish a **tested** new image tag, change `VOTE_IMAGE`,
   `RESULT_IMAGE`, and `WORKER_IMAGE` to matching version tags, then re-run
   `docker stack config` and `docker stack deploy`. Vote tasks update one at a
   time with `failure_action: rollback`; singletons use stop-first to avoid
   concurrent writers or socket-server instances. Observe
   `docker service ps voting_vote --no-trunc` and app logs. A rollback returns
   service image settings, **not** DB rows or votes. Do not test update behavior
   using a live election or a shared production cluster.

## Stop, data and cleanup

Swarm has no `docker compose stop`. `docker stack rm voting` removes **all five
services and their overlay networks**; it interrupts the app immediately.
Use it only after deliberately finishing this lab:

```bash
docker stack rm voting
docker stack services voting   # eventually empty
```

The local named volume may remain on the labeled node, but it is not portable
and cannot be relied on after rescheduling or reprovisioning. **Do not delete
volumes or regenerate credentials to 'reset' the app.** Back up Postgres and
verify a restore independently before any intentional cleanup, host replacement,
or migration. Removing a worker/cluster is separate from removing this stack;
see the [Swarm guide](../README.md#operations). To keep data, prefer leaving
the stack deployed and restricting ingress, or plan a maintenance window rather
than assuming `stack rm` is a reversible stop.

[Validation record](VALIDATION.md) distinguishes checks made here from tests
that require a real Docker Engine and registry.
