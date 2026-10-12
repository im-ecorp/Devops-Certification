#!/usr/bin/env python3
"""Daemon-free static checks; pass a standalone Compose executable if needed."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
cli = sys.argv[1:] or ["docker", "compose"]
model = json.loads(subprocess.check_output(
    cli + ["-f", str(root / "compose.yaml"), "config", "--format", "json"], text=True))
services = model["services"]
assert set(services) == {"vote", "result", "worker", "redis", "db"}
ports = [(name, port) for name, service in services.items() for port in service.get("ports", [])]
assert len(ports) == 2
assert {(n, p["host_ip"], p["published"], p["target"]) for n, p in ports} == {
    ("vote", "127.0.0.1", "8093", 80), ("result", "127.0.0.1", "8094", 80)}
assert model["networks"]["back-tier"]["internal"] is True
assert "db-data" in model["volumes"]
for name in ["vote", "result", "redis", "db"]:
    assert "healthcheck" in services[name]
for name, targets in {"vote": ["redis"], "result": ["db"], "worker": ["redis", "db"]}.items():
    for target in targets:
        assert services[name]["depends_on"][target]["condition"] == "service_healthy"
assert services["db"]["environment"]["POSTGRES_PASSWORD"] == "postgres"
worker = (root / "upstream/worker/Program.cs").read_text()
result = (root / "upstream/result/server.js").read_text()
assert "Server=db;Username=postgres;Password=postgres;" in worker
assert "postgres://postgres:postgres@db/postgres" in result
assert ET.parse(root / "upstream/worker/Worker.csproj").find(".//TargetFramework").text == "net10.0"
assert not list((root / "upstream").rglob(".git"))
baseline = json.loads((root / "upstream-sha256.json").read_text())
changed = []
for filename, expected in baseline.items():
    actual = hashlib.sha256((root / "upstream" / filename).read_bytes()).hexdigest()
    if actual != expected:
        changed.append(filename)
        assert hashlib.sha256((root / "originals" / filename).read_bytes()).hexdigest() == expected
assert set(changed) == {"worker/Dockerfile", "worker/Worker.csproj", "result/Dockerfile", "result/package-lock.json"}
blocks = 0
for name in ["README.md", "UPSTREAM.md", "VALIDATION.md"]:
    text = (root / name).read_text()
    for link in re.findall(r"\]\(([^)]+)\)", text):
        if "://" not in link and not link.startswith("#"):
            assert (root / link.split("#")[0]).exists(), (name, link)
    for block in re.findall(r"```bash\n(.*?)```", text, re.S):
        subprocess.run(["bash", "-n"], input=block, text=True, check=True)
        blocks += 1
print(f"PASS: {len(services)} services; loopback-only 8093/8094; internal DB/cache; readiness and volume")
print(f"PASS: {len(baseline)} baseline files retained; {len(changed)} changes backed up; no nested .git")
print(f"PASS: client/database credentials match; net10.0; local document links; {blocks} Bash blocks")
print("Static checks only. No container build or runtime integration was performed.")
