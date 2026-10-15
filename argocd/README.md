# Argo CD — GitOps for Kubernetes

Learn what Argo CD is, why teams use it, and how to run it with **Kind** for hands-on practice. This guide starts with the core concepts, then walks through deploying an application from Git and managing changes to it.

The examples are intended for anyone learning Kubernetes application delivery. Basic familiarity with Git, containers, and Kubernetes Deployments and Services will help; no previous Argo CD experience is required.

## Contents

- [1. What is Argo CD?](#1-what-is-argo-cd)
- [2. Why use Argo CD?](#2-why-use-argo-cd)
- [3. Run Argo CD with Kind: prerequisites](#3-run-argo-cd-with-kind-prerequisites)
- [4. Create the Kind cluster](#4-create-the-kind-cluster)
- [5. Install and access Argo CD](#5-install-and-access-argo-cd)
- [6. Deploy an application from Git](#6-deploy-an-application-from-git)
- [7. Practice GitOps](#7-practice-gitops)
- [8. Troubleshooting](#8-troubleshooting)
- [9. Cleanup and next steps](#9-cleanup-and-next-steps)

## 1. What is Argo CD?

**Argo CD is a declarative, GitOps continuous-delivery tool for Kubernetes.** You describe how an application should run in Git, and Argo CD compares that configuration with what is actually running in the cluster. Git becomes the source of truth for the application's desired state.

Argo CD is part of the broader **Argo** project. Other Argo tools solve different problems: Argo Workflows orchestrates container-based jobs, Argo Events handles event-driven automation, and Argo Rollouts supports progressive delivery such as canary deployments. This guide focuses on **Argo CD**, not the entire Argo toolset.

It reads Kubernetes YAML, renders Helm charts or Kustomize configurations when used, compares the result with live resources, and reconciles them when a sync runs.

```text
Developer commits and pushes Kubernetes configuration
                    |
                    v
             Remote Git repository
                    |
             Argo CD reads Git
                    |
           compares desired/live state
                    |
            manual or automatic sync
                    |
                    v
             Kubernetes resources
```

CI builds/tests an application and publishes its container image. Argo CD handles deployment after the desired image/configuration is updated in Git. It does not build images, run Docker Compose files, or provision the Kubernetes cluster itself.

## 2. Why use Argo CD?

Without a deployment controller, teams often apply manifests manually or run deployment commands from CI. Those approaches can work, but it becomes harder to see whether a cluster still matches the reviewed configuration after an emergency change or an incomplete deployment.

Argo CD provides a continuous comparison between Git and Kubernetes:

| Benefit | What it means in practice |
|---|---|
| Reviewed, traceable changes | Pull requests and commits record what changed and why |
| Repeatable configuration | The same versioned manifests can be reviewed and applied again; runtime dependencies still need to be available |
| Drift detection | Unexpected differences between Git and the cluster are visible |
| Controlled automation | Start with manual sync, then enable automated sync and self-healing when appropriate |
| Deployment visibility | Inspect application resources, diffs, sync history, and health in one UI |
| Git-based rollback | Revert a configuration commit to restore an earlier desired state; database/data rollback requires separate planning |

**Example:** CI publishes a new application image, then a pull request updates its image tag in Git. After review and merge, Argo CD detects the configuration change and deploys it through a manual or automated sync. The cluster does not need to be updated by an operator copying commands from a terminal.

Argo CD is useful when applications run on Kubernetes and their deployment configuration is maintained in Git. It does not replace CI, application tests, secret management, or cluster provisioning. It is not a general-purpose deployment tool for standalone VMs or Docker Compose services.

### Learn the workflow with Kind

**Kind (Kubernetes in Docker)** runs Kubernetes nodes as local Docker containers. It lets you practice with a real Kubernetes API without renting a cloud cluster or changing a shared environment. Argo CD runs **inside** that cluster; Kind supplies the cluster, while Argo CD manages the sample application.

The following lab creates one disposable node, installs Argo CD, and deploys Nginx from a Git repository. You will first inspect and sync changes manually, then practice drift detection, self-healing, and rollback. The UI and sample app are accessed through loopback-only port forwarding. No cloud account, public domain, or Ingress controller is required.

This is an independent training environment, not a production installation or a deployment to this repository's Ansible inventory or Vagrant machines.

### Key concepts and lab files

| Term | Meaning in this lab |
|---|---|
| Application | Argo CD custom resource linking a Git repository/path/revision to a destination cluster/namespace |
| Desired state | Deployment and Service YAML in the remote Git branch |
| Live state | Resources currently running in Kubernetes |
| Sync | Apply desired resources to the destination |
| `OutOfSync` | Desired and live configuration differ; this does not necessarily mean an outage |
| `Synced` | Compared configuration matches; this alone does not prove the app is healthy |
| `Healthy` | Argo CD's resource health checks pass |
| Self-heal | Automatically correct live drift when enabled with automated sync |
| Prune | Delete managed resources no longer declared in Git; disabled here |

The installation includes an API server/UI, application controller, repository server, Redis, and supporting components such as ApplicationSet and Dex. You do not need to configure SSO or multiple clusters for this exercise.

```text
argocd/
├── README.md
├── .gitignore
├── kind-config.yaml             # One local Kubernetes node
├── application.yaml             # Git source and deployment destination
└── apps/
    └── web-demo/
        ├── deployment.yaml      # Nginx, one replica, probes and resource limits
        └── service.yaml         # ClusterIP; no public listener
```

Only `apps/web-demo/` contains workload manifests. Pointing the Application at the entire repository would mix unrelated labs into the deployment.

## 3. Run Argo CD with Kind: prerequisites

Use a Linux workstation or Linux VM with internet access. macOS/Windows users can use Docker Desktop and equivalent CLI installation instructions. The commands below use Bash.

- **Docker Engine or Docker Desktop**, running and accessible to your user. Docker socket access is effectively privileged; do not make the socket world-writable.
- **Kind** to create Kubernetes inside Docker. Use a current stable release.
- **kubectl** compatible with the Kubernetes version bundled by your Kind release (within one minor version of the API server).
- **Git** and **curl**.
- Optional **argocd CLI**, matching the Argo CD server version below, for CLI login/sync instead of UI actions.
- A practical starting budget of **4 CPU cores, 6 GiB RAM, and 10 GiB free disk** for Docker and the lab. This is a learning budget, not an official minimum.
- Free local ports **8080** (Argo CD UI) and **8081** (sample app).

Install missing tools using their official guides: [Docker Engine](https://docs.docker.com/engine/install/), [Kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation), [kubectl](https://kubernetes.io/docs/tasks/tools/), and optionally [Argo CD CLI](https://argo-cd.readthedocs.io/en/stable/cli_installation/). Do not reinstall or replace existing tools blindly. This lab does not require Helm.

Check before continuing:

```bash
docker version
kind version
kubectl version --client
git --version
curl --version
```

The lab pins **Argo CD v3.5.5** rather than the moving `stable` branch. Its documented Kubernetes test matrix includes **1.33–1.36**; choose a Kind release/node image in that range and verify the created cluster version. Review current security advisories and compatibility before changing pins. The sample Nginx tag is a teaching pin, not a production security baseline.

## 4. Create the Kind cluster

1. Clone the repository if you do not already have a checkout:

   ```bash
   git clone https://github.com/im-ecorp/Devops-Certification.git
   cd Devops-Certification/argocd
   ```

   If you already have a checkout, open its `argocd/` directory instead of cloning again. All subsequent relative paths assume this directory. Use your own fork URL if you plan to publish exercise changes there.

2. Check for a name collision, then create a **new** cluster. If `argocd-lab` already exists, inspect it rather than deleting/replacing it.

   ```bash
   kind get clusters
   kind create cluster --name argocd-lab --config kind-config.yaml --wait 120s
   ```

   Kind creates a Docker node container and updates your kubeconfig/current context. It does not reuse the Ansible remote inventory. The API listener binds to loopback; app access will also use loopback-only port forwarding.

3. Use the explicit lab context in every Kubernetes command:

   ```bash
   kubectl --context kind-argocd-lab cluster-info
   kubectl --context kind-argocd-lab version
   kubectl --context kind-argocd-lab wait --for=condition=Ready nodes --all --timeout=180s
   kubectl --context kind-argocd-lab get nodes -o wide
   ```

   Expected: one `Ready` node. Stop if the context or cluster version is not the one you intended. Installation below grants Argo CD broad permissions **inside this disposable cluster**.

## 5. Install and access Argo CD

1. Install the pinned upstream non-HA manifests:

   ```bash
   kubectl --context kind-argocd-lab create namespace argocd
   kubectl --context kind-argocd-lab apply --server-side -n argocd \
     -f https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.5/manifests/install.yaml
   kubectl --context kind-argocd-lab -n argocd wait \
     --for=condition=Established crd/applications.argoproj.io --timeout=120s
   kubectl --context kind-argocd-lab -n argocd rollout status \
     deployment/argocd-server --timeout=300s
   kubectl --context kind-argocd-lab -n argocd rollout status \
     deployment/argocd-repo-server --timeout=300s
   kubectl --context kind-argocd-lab -n argocd rollout status \
     statefulset/argocd-application-controller --timeout=300s
   kubectl --context kind-argocd-lab -n argocd get pods
   ```

   Server-side apply avoids large CRD annotation limits. Do not add `--force-conflicts` to resolve an ownership conflict without investigating it; this guide is for a fresh cluster, not an in-place Argo CD upgrade. The standard non-HA installation is for learning, not production resilience.

2. In a separate terminal, start UI access and leave it running:

   ```bash
   kubectl --context kind-argocd-lab -n argocd port-forward \
     --address 127.0.0.1 svc/argocd-server 8080:443
   ```

   Open **https://localhost:8080**. Expect a self-signed certificate warning for this local lab only. Do not expose the UI with `--address 0.0.0.0`.

   On a remote VM, keep port-forward running there and tunnel from your workstation: `ssh -N -L 8080:127.0.0.1:8080 YOUR_SSH_HOST`. Replace `YOUR_SSH_HOST` with your configured SSH host. Your workstation browser then uses the same URL; no public UI port is needed.

3. Retrieve the initial password in your **own local terminal**, not a shared log or Git file:

   ```bash
   kubectl --context kind-argocd-lab -n argocd get secret argocd-initial-admin-secret \
     -o jsonpath='{.data.password}' | base64 --decode
   printf '\n'
   ```

   Log in with username **admin**, then change the password in **User Info**. Do not commit passwords, kubeconfig, tokens, or private repository credentials. Once login with the new password works, the initial secret can be removed using the reviewed cleanup command in section 9.

4. Optional CLI access, with the same UI port-forward still running:

   ```bash
   argocd version --client
   argocd login localhost:8080 --username admin --insecure
   ```

   Enter your password at the prompt. `--insecure` skips TLS verification only for this local self-signed endpoint; it is not a production TLS recommendation.

## 6. Deploy an application from Git

**Argo CD reads remote Git, not uncommitted files on your workstation.** This repository's local files must be committed and pushed to an accessible branch before the Application can fetch them. Creating these files alone does not publish them.

1. Use your own fork/branch if you cannot push to the upstream repository. In `application.yaml`, edit:

   - `spec.source.repoURL`: the HTTPS clone URL of your repository/fork.
   - `spec.source.targetRevision`: the branch you will publish, for example `argocd-training`.
   - Keep `spec.source.path: argocd/apps/web-demo`.

   The checked-in Application references this repository's `main` branch. For the exercises, use a fork or branch you can push changes to, and confirm the lab files exist on that remote branch. A public fork is simplest for learning. For a private repository, register read-only credentials through Argo CD's repository settings; never embed credentials in a URL or committed manifest.

2. Review and publish **only this lab**, using your normal Git workflow. These commands intentionally do not choose a remote or push on your behalf:

   ```bash
   git status --short
   git diff -- apps/web-demo application.yaml kind-config.yaml README.md
   git remote -v
   git branch --show-current
   ```

   From this directory, stage exact intended files such as `git add README.md .gitignore kind-config.yaml application.yaml apps/web-demo/`, inspect `git diff --cached`, commit, then push the reviewed branch to your chosen remote. Avoid `git add .` at repository root if unrelated work is present. Check the remote branch contains both sample YAML files before continuing.

3. Create only the Argo CD Application. **Do not apply `apps/web-demo/` directly**; Argo CD should own the deployment exercise.

   ```bash
   kubectl --context kind-argocd-lab apply -f application.yaml
   kubectl --context kind-argocd-lab -n argocd get applications
   ```

   Open **Applications → web-demo**. Refresh if necessary. Before the first sync, expect `OutOfSync` and missing workload resources. A `ComparisonError` means the source could not be rendered/read; fix it before syncing.

   `CreateNamespace=true` creates `web-demo` during sync. `https://kubernetes.default.svc` means the same cluster Argo CD runs in; no `argocd cluster add` is needed. This introductory lab uses the broad `default` project; restrict AppProjects and RBAC before any shared environment.

4. Inspect **Diff**, then choose **Sync → Synchronize** in the UI. Leave **Prune** unchecked. Optional equivalent CLI commands:

   ```bash
   argocd app get web-demo --refresh
   argocd app sync web-demo
   argocd app wait web-demo --sync --health --timeout 180
   ```

   Expected after image download/startup: **Synced / Healthy**. Verify independently:

   ```bash
   kubectl --context kind-argocd-lab -n web-demo rollout status deployment/web-demo --timeout=180s
   kubectl --context kind-argocd-lab -n web-demo get deployment,pods,service
   ```

5. Start app access in another terminal, then send a request from a separate terminal:

   ```bash
   kubectl --context kind-argocd-lab -n web-demo port-forward \
     --address 127.0.0.1 svc/web-demo 8081:80
   ```

   ```bash
   curl --noproxy '*' -i http://127.0.0.1:8081/
   ```

   Expected: **HTTP 200** and the Nginx welcome page. On a remote VM, add a separate SSH tunnel for port 8081 using the same pattern as the UI tunnel. Port forwarding is temporary, not an Ingress or load balancer.

## 7. Practice GitOps

Finish these in order. Work only on the disposable cluster and your training Git branch. Record the commit, sync status, health status, and observed replica count after each exercise.

### A. Deploy a Git change manually

1. Change `spec.replicas` in `apps/web-demo/deployment.yaml` from `1` to `2`.
2. Commit and push that file to the branch configured in the Application.
3. Refresh the Application; polling may take a few minutes. Expect `OutOfSync` while the cluster still runs one replica.
4. Inspect Diff, sync with pruning disabled, and check two replicas become ready:

   ```bash
   kubectl --context kind-argocd-lab -n web-demo get deployment/web-demo
   kubectl --context kind-argocd-lab -n web-demo get pods -l app=web-demo
   ```

**Lesson:** a local edit is not a deployment; Git publication and an Argo CD sync are separate steps.

### B. Observe live drift

Manually scale **only this lab's** Deployment, leaving Git at two replicas:

```bash
kubectl --context kind-argocd-lab -n web-demo scale deployment/web-demo --replicas=3
```

Refresh Argo CD and inspect Diff. Expect `OutOfSync`; the app can remain healthy because health and configuration agreement are different checks. With manual sync, Argo CD reports drift rather than immediately fixing it. Sync again and verify the replica count returns to the value in Git.

### C. Enable automated sync and self-healing

In `application.yaml`, add `automated` beside the existing `syncOptions`:

```yaml
  syncPolicy:
    automated:
      enabled: true
      selfHeal: true
      prune: false
      allowEmpty: false
    syncOptions:
      - CreateNamespace=true
```

Commit/push the Application change for reproducibility, then apply it locally:

```bash
kubectl --context kind-argocd-lab apply -f application.yaml
```

**Why apply it?** This Application watches only `apps/web-demo/`; it does not manage its own `application.yaml`. Changing that file in Git alone does not update the live Application.

Repeat the manual scale to three replicas. Argo CD should correct the drift back to Git without a manual sync. Next, change the replica count in Git, commit/push, refresh, and observe automatic deployment. `prune: false` still prevents automatic deletion of removed manifests; it does not prevent updates or scale-downs of existing resources.

To return to manual mode, set `automated.enabled: false` in the file, commit/push, and apply the Application again. Merely disabling self-heal leaves automatic Git-change deployment enabled.

### D. Roll back through Git

Review the commit that changed the desired replica count and revert **that specific lab commit** on your training branch. Inspect the diff before publishing; do not revert a commit containing unrelated changes. Push the revert and sync, or observe auto-sync if still enabled.

**Lesson:** with GitOps, a Git revert makes the rollback the new desired state. A live `kubectl rollout undo` alone leaves Git unchanged and self-heal may undo it.

### E. Understand pruning before enabling it

Read the Application diff and explain what would happen if `service.yaml` disappeared from the remote branch:

- With pruning disabled, the existing Service remains and Argo CD reports the extra managed resource.
- A sync with pruning enabled can delete it and break service access.
- `allowEmpty: false` protects against automated pruning of an entirely empty application, not all dangerous partial deletions.

This lab intentionally does not automate a deletion exercise. Review exact resource names and impact before enabling pruning. Do not use the entire repository as the Application path.

**Completion check:** explain `Synced` versus `Healthy`, deploy a Git change, show live drift, demonstrate self-heal, and restore a previous desired state through Git.

## 8. Troubleshooting

| Symptom | Check / action |
|---|---|
| Docker unavailable | Start the intended daemon; confirm `docker version` has a server response and your user has authorized access |
| Kind cluster creation fails | Check Docker capacity, image-registry access, proxy settings, and `kind get clusters`; do not delete an existing cluster blindly |
| Argo CD pod Pending | Inspect node resources and pod events; increase the learning VM/Docker budget if needed |
| `ImagePullBackOff` | Inspect pod events for registry, DNS, proxy, authentication, or tag issues; Argo CD cannot fix a blocked registry |
| UI connection refused | Keep the port-forward running; check port 8080 and the correct context; use SSH tunneling for a remote host |
| Self-signed certificate warning | Expected only for this local install; use proper TLS for shared/production access |
| Repository/path/branch error | Verify `repoURL`, `targetRevision`, remote published files, and repo-server Git/network access |
| Commit not detected immediately | Refresh the UI, or use `argocd app get web-demo --hard-refresh`; confirm the tracked branch |
| App stays `OutOfSync` | Review Diff and whether manual sync is still enabled; Git and live values may differ |
| App `Synced` but not `Healthy` | Check rollout, probes, image pulls, and Kubernetes events; sync is not a health test |
| App disappears but pods remain | Expected for this manifest without a deletion finalizer; Application deletion does not cascade here |

Useful read-only diagnostics:

```bash
kubectl --context kind-argocd-lab -n argocd get pods
kubectl --context kind-argocd-lab -n argocd logs deployment/argocd-repo-server --tail=80
kubectl --context kind-argocd-lab -n argocd logs statefulset/argocd-application-controller --tail=80
kubectl --context kind-argocd-lab -n argocd describe application web-demo
kubectl --context kind-argocd-lab -n web-demo get events --sort-by=.metadata.creationTimestamp
kubectl --context kind-argocd-lab -n web-demo describe deployment web-demo
```

Do not share unredacted logs, repository credentials, or secret values.

## 9. Cleanup and next steps

Stop port-forwards and SSH tunnels with **Ctrl+C**. This stops access only; it does not remove resources.

After changing the admin password and verifying the new login, optionally remove the obsolete initial password secret. Review the context and exact secret first. This deletes only the stored initial password, not the admin account:

```bash
kubectl --context kind-argocd-lab -n argocd delete secret argocd-initial-admin-secret
```

**Destructive cluster cleanup — run only when you explicitly intend to discard this lab.** This removes the named Kind cluster, all its namespaces, workloads, and cluster-local data. It does not remove repository files or pushed commits. First verify `argocd-lab` is the disposable cluster you created, not someone else's existing cluster.

```bash
kind get clusters
kubectl --context kind-argocd-lab get namespaces
kind delete cluster --name argocd-lab
```

Never substitute a production context or delete persistent volumes as routine troubleshooting. No cleanup command is executed by reading this guide.

After this lab, practice Kustomize dev/prod overlays, Helm values, restricted AppProjects/RBAC, and ApplicationSets. For production, plan HA, trusted TLS, SSO, least-privilege repository/cluster access, secret management, monitoring, backup/restore, and a reviewed upgrade procedure. Installing Helm is an alternative way to package Argo CD, not a replacement for Kubernetes.

---

References: [Getting started](https://argo-cd.readthedocs.io/en/stable/getting_started/) · [Installation and Kubernetes compatibility](https://argo-cd.readthedocs.io/en/stable/operator-manual/installation/) · [Automated sync/self-heal/pruning](https://argo-cd.readthedocs.io/en/stable/user-guide/auto_sync/) · [Argo CD v3.5.5](https://github.com/argoproj/argo-cd/releases/tag/v3.5.5) · [Kind quick start](https://kind.sigs.k8s.io/docs/user/quick-start/)
