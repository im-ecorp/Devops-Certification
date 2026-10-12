# Docker Swarm: first cluster and practical lab

Swarm mode is the cluster orchestrator built into Docker Engine. You describe a
**desired state** (image, replica count, networks, resources); Swarm schedules
containers across nodes and replaces failed tasks. Compose normally runs an app
on one Engine. Swarm adds multi-node scheduling, service discovery, rolling
updates and a cluster control plane.

**Navigate:** [Concepts](#concepts) · [Prepare hosts](#prepare-hosts) · [Create and join](#create-and-join) · [First service](#first-service) · [Operations](#operations) · [Voting lab](voting-app/README.md)

## Concepts

| Term | Meaning |
| --- | --- |
| Node | A Docker Engine host in the cluster. |
| Manager | Stores cluster state in Raft, schedules tasks and accepts management commands. Managers can also run workloads by default. |
| Worker | Runs assigned tasks; does not manage the cluster. |
| Service/task | A service defines desired state; a task is one scheduled container instance. |
| Replicated/global | A fixed replica count, or one task per eligible node. |
| Stack | Related services/networks deployed from a legacy Compose v3 file. |
| Overlay network | Connects containers across hosts with service-name DNS. |
| Routing mesh | Accepts a published service port on any node and routes to a task. |
| Secret/config | Swarm distributes a secret only to granted tasks; configs carry non-sensitive files. Apps must explicitly read mounted secrets. |

One manager is fine for learning, but has no manager redundancy. A production
control plane normally uses **3 or 5 managers**: a majority is required for Raft
quorum. Three managers tolerate one unavailable manager; two do not. Adding
workers does not improve quorum. Losing quorum prevents scheduling/updates even
if existing tasks continue running. Replicas alone do not replicate a database.

## Prepare hosts

Use dedicated Linux VMs with current Docker Engine installed ([installation](../README.md#installation)).
For this guide: `manager1` at `192.168.50.10`, `worker1` at `192.168.50.11`, and
optionally `worker2` at `192.168.50.12`. **Replace these example addresses** with
stable private IPs assigned to your hosts. A single-node lab can use one host;
it cannot demonstrate cross-node placement or node failover. The voting lab
assumes Linux amd64 by default; use compatible images on every node.

On each host, confirm daemon access, addresses and routes:

```bash
docker version
docker info --format '{{.Swarm.LocalNodeState}}'
ip -br address
ip route
```

Do not initialize or join a node already serving an unrelated Swarm. Commands
assume authorized Docker access; prefix with `sudo` where required. Node clocks
should be synchronized, and every node must reach the registry used for images.
Allow these **only between trusted cluster hosts**:

| Traffic | Purpose |
| --- | --- |
| TCP 2377 to managers | Cluster management/join. |
| TCP and UDP 7946 between nodes | Node discovery. |
| UDP 4789 between nodes | VXLAN overlay/ingress traffic; never expose publicly. |
| IP protocol 50 (ESP) when using encrypted overlays | Encrypted overlay data plane, used by the voting lab. |

Allow application ports only from trusted clients/load balancers. Swarm ingress
publication is **not a loopback-only binding**: it can be reachable on every
node's addresses. Use a private lab network and verified firewall rules. Docker
port publication may bypass some host firewall policies; do not rely on a UFW
rule alone. Control-plane mutual TLS does not encrypt ordinary overlay traffic;
`--opt encrypted` enables overlay encryption with some performance cost.

## Create and join

**On manager1** (changes this Engine into a Swarm manager):

```bash
docker swarm init --advertise-addr 192.168.50.10
docker node ls
docker swarm join-token worker
```

The last command prints a complete worker join command. Use **that actual command**
on worker1; the shell form below is illustrative, not a usable token:

```bash
# worker1: replace the placeholder with the token printed by the manager.
docker swarm join --token 'WORKER_JOIN_TOKEN' 192.168.50.10:2377
```

Verify on the manager:

```bash
docker node ls
docker node inspect worker1 --pretty
```

Expected: both nodes `Ready` and `Active`; manager1 shows `Leader`, while worker1
has no manager status. Join tokens are credentials: do not commit or share them.
To invalidate a leaked worker join token, run `docker swarm join-token --rotate worker`
on the manager; this does not remove already joined nodes. Adding another manager
uses `docker swarm join-token manager`, with stricter access control. Do not
force-create a new cluster as a routine repair for a lost manager.

## First service

Run management commands on a manager. This publishes HTTP on **all nodes** at
port 8088; first restrict access to your private lab clients and check for conflicts.

```bash
docker service create --name swarm-web --replicas 2 \
  --publish published=8088,target=80,mode=ingress nginx:1.28-alpine
docker service ls
docker service ps swarm-web
docker service inspect swarm-web --pretty
curl -fsS http://192.168.50.10:8088/ > /dev/null
```

`REPLICAS` should eventually show `2/2`. Two replicas do not guarantee two
hosts: placement and resource availability determine where tasks run. Inspect
`docker service ps` rather than assuming distribution. Scale and observe:

```bash
docker service scale swarm-web=3
docker service ps swarm-web
docker service logs --tail 30 swarm-web
```

This creates disposable lab resources, not a production ingress service. To
remove **only this example**, after you finish:

```bash
docker service rm swarm-web
```

## Operations

- **Desired state:** failed tasks are replaced, but health checks do not guarantee
  application correctness. Use logs, request tests and data checks together.
- **Updates:** `docker service update --image 'REGISTRY/APP:NEW_TAG' SERVICE` rolls
  tasks according to update policy; `docker service rollback SERVICE` restores
  the previous service specification, not database contents.
- **Placement:** node labels and constraints choose eligible hosts. An impossible
  constraint leaves tasks pending; replicas cannot override it.
- **Draining:** first check the tasks and data on the node. Drain a **stateless**
  worker from the manager, then restore scheduling:

  ```bash
  docker node ps worker1
  docker node update --availability drain worker1
  docker service ps swarm-web
  docker node update --availability active worker1
  ```

  Drain moves eligible tasks; it does not transfer node-local volumes. Do not
  drain the voting database node as a generic failover exercise.
- **Leaving:** on an idle worker run `docker swarm leave`, then remove its stale
  membership with `docker node rm worker1` on the manager. Schedule this after
  workloads/data are handled. Do not use `docker swarm leave --force` on a manager
  casually: it can destroy quorum. Manager Raft backups and application backups
  are different operations; neither is provided by a replica count.

## Practical example

Continue with [Voting App on Swarm](voting-app/README.md). It reuses the maintained
[Compose app source](../scenario/voting-app/UPSTREAM.md), builds/pushes three
images, deploys five services, scales the stateless frontend, and demonstrates
updates, routing mesh and the limits of node-local state.

The example is runnable on your Docker hosts; no cluster is initialized by
reading this guide. See its [validation record](voting-app/VALIDATION.md) for
checks performed and runtime checks still required.

**Official references:** [Swarm tutorial](https://docs.docker.com/engine/swarm/swarm-tutorial/) · [Stack deployment](https://docs.docker.com/engine/swarm/stack-deploy/) · [Routing mesh](https://docs.docker.com/engine/swarm/ingress/) · [Node administration](https://docs.docker.com/engine/swarm/manage-nodes/) · [Secrets](https://docs.docker.com/engine/swarm/secrets/)
