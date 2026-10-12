#!/usr/bin/env python3
"""Read-only Swarm stack validation using the real Docker CLI; no daemon required.
Run: python3 validate.py /path/to/docker
"""
import os
from pathlib import Path
import re
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parent
cli = sys.argv[1] if len(sys.argv) > 1 else "docker"
env = dict(os.environ, VOTE_IMAGE="example.invalid/vote:test",
           RESULT_IMAGE="example.invalid/result:test", WORKER_IMAGE="example.invalid/worker:test")
render = subprocess.check_output([cli, "stack", "config", "-c", str(ROOT / "stack.yaml")], env=env, text=True)
model = yaml.safe_load(render)
services = model["services"]
assert set(services) == {"vote", "result", "worker", "redis", "db"}
for service in services.values():
    assert not set(service) & {"build", "depends_on", "container_name", "restart"}
    assert "image" in service and "restart_policy" in service["deploy"]
assert services["vote"]["deploy"]["replicas"] == 2
assert all(services[n]["deploy"]["replicas"] == 1 for n in ("result", "worker", "redis", "db"))
assert services["db"]["deploy"]["placement"]["constraints"] == ["node.labels.voting-db == true"]
assert services["db"]["deploy"]["update_config"]["order"] == "stop-first"
assert services["vote"]["deploy"]["update_config"]["failure_action"] == "rollback"
ports = [(name, port["published"], port["target"], port["mode"], port["protocol"])
         for name, service in services.items() for port in service.get("ports", [])]
assert len(ports) == 2
assert set(ports) == {("vote", 8095, 80, "ingress", "tcp"),
                      ("result", 8096, 80, "ingress", "tcp")}
assert model["networks"]["frontend"]["driver"] == "overlay"
assert model["networks"]["backend"]["driver"] == "overlay"
assert model["networks"]["backend"]["internal"] is True
assert "encrypted" in model["networks"]["backend"]["driver_opts"]
assert model["volumes"]["db-data"]["driver"] == "local"
assert services["db"]["volumes"] == [{"type": "volume", "source": "db-data",
                                    "target": "/var/lib/postgresql/data"}]
for component in ("vote", "result", "worker"):
    assert (ROOT / "../../scenario/voting-app/upstream" / component / "Dockerfile").resolve().is_file()
for document in (ROOT / "README.md", ROOT.parent / "README.md"):
    text = document.read_text()
    for link in re.findall(r"\]\(([^)]+)\)", text):
        if "://" not in link and not link.startswith("#"):
            assert (document.parent / link.split("#")[0]).exists(), (document, link)
    for block in re.findall(r"^ *```(?:bash|sh) *\n(.*?)^ *```", text, re.M | re.S):
        subprocess.run(["bash", "-n"], input=block, text=True, check=True)
print("PASS: real Docker stack parser; 5 services; ingress 8095/8096; no Compose-only settings")
print("PASS: database pinned, stop-first; encrypted internal overlay; source paths and docs")
print("Not tested: registry pushes, image builds, Swarm scheduling, traffic, failover or data persistence")
