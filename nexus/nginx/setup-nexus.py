#!/usr/bin/env python3
"""Idempotent standalone setup helper for Nexus repositories and access control.

Reads settings from nexus-config.json and applies them via the Nexus REST API.
Default operation is DRY RUN. Use --apply to execute changes.
Existing repositories are preserved unless --update-existing is passed.
Does not delete repositories unless --delete-default-repos is passed.
Admin password is read from NEXUS_ADMIN_PASSWORD env or prompted securely.
"""

from __future__ import annotations

import argparse
import base64
import getpass
import json
import os
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Configure Nexus via REST API (dry run by default)"
    )
    parser.add_argument("--url", default="http://localhost:8081", help="Nexus base URL")
    parser.add_argument("--user", default="admin", help="Admin username")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).parent / "nexus-config.json",
        help="Path to nexus-config.json",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to the running Nexus instance (default is dry-run)",
    )
    parser.add_argument(
        "--update-existing",
        action="store_true",
        help="Update existing repositories with config values (default preserves existing)",
    )
    parser.add_argument(
        "--delete-default-repos",
        action="store_true",
        help="Delete unneeded default repositories listed in config (opt-in)",
    )
    parser.add_argument(
        "--deploy-user-password-env",
        default="NEXUS_DEPLOY_USER_PASSWORD",
        help="Environment variable name for the deploy user password",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=0,
        help="Wait up to N seconds for Nexus status endpoint before applying",
    )
    return parser.parse_args()


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise RuntimeError(f"Refusing redirect with credentials to: {newurl}")


class NexusClient:
    def __init__(self, base_url: str, user: str, password: str):
        parsed = urllib.parse.urlsplit(base_url)
        if parsed.scheme not in ("http", "https"):
            raise ValueError(f"Invalid URL scheme: {base_url}")
        if parsed.scheme == "http":
            host = (parsed.hostname or "").lower()
            if host not in ("localhost", "127.0.0.1", "::1"):
                raise ValueError(
                    f"Refusing Basic Auth credentials over unencrypted HTTP to non-local host: {host}"
                )
        self.base_url = base_url.rstrip("/")
        self.user = user
        self.password = password
        self.opener = urllib.request.build_opener(NoRedirectHandler)

    def request(
        self,
        method: str,
        path: str,
        data: dict | list | None = None,
        expected_status: tuple[int, ...] = (200,),
    ) -> tuple[int, str]:
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode("utf-8") if data is not None else None
        headers = {"Accept": "application/json"}
        if data is not None:
            headers["Content-Type"] = "application/json"

        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        auth_raw = f"{self.user}:{self.password}".encode("utf-8")
        auth = base64.b64encode(auth_raw).decode("ascii")
        req.add_header("Authorization", f"Basic {auth}")

        try:
            with self.opener.open(req, timeout=30) as resp:
                resp_text = resp.read().decode("utf-8")
                if resp.status not in expected_status:
                    raise RuntimeError(
                        f"{method} {path} returned status {resp.status}, expected {expected_status}. Response: {resp_text}"
                    )
                return resp.status, resp_text
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            if exc.code in expected_status:
                return exc.code, err_body
            raise RuntimeError(
                f"{method} {path} failed with HTTP {exc.code}: {err_body}"
            ) from exc

    def wait_until_ready(self, timeout_s: int) -> bool:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            try:
                status, _ = self.request("GET", "/service/rest/v1/status", expected_status=(200,))
                if status == 200:
                    return True
            except Exception:
                pass
            time.sleep(5)
        return False


def apply_config(
    client: NexusClient,
    config: dict,
    delete_defaults: bool,
    deploy_pass: str,
    update_existing: bool = False,
) -> None:
    if delete_defaults:
        for repo_name in config.get("delete_repositories_opt_in", []):
            st, _ = client.request("GET", f"/service/rest/v1/repositories/{repo_name}", expected_status=(200, 404))
            if st == 200:
                print(f"Deleting repository: {repo_name}")
                client.request("DELETE", f"/service/rest/v1/repositories/{repo_name}", expected_status=(204,))

    for bs in config.get("blob_stores", []):
        name = bs["name"]
        st, _ = client.request("GET", f"/service/rest/v1/blobstores/file/{name}", expected_status=(200, 404))
        if st == 404:
            print(f"Creating file blob store: {name}")
            client.request("POST", "/service/rest/v1/blobstores/file", data=bs, expected_status=(204,))

    for policy in config.get("cleanup_policies", []):
        name = policy["name"]
        st, _ = client.request("GET", f"/service/rest/internal/cleanup-policies/{name}", expected_status=(200, 404))
        if st == 404:
            print(f"Creating cleanup policy: {name}")
            client.request("POST", "/service/rest/internal/cleanup-policies", data=policy, expected_status=(200, 201))

    for item in config.get("repositories", []):
        fmt = item["format"]
        body = item["body"]
        name = body["name"]
        endpoint = f"/service/rest/v1/repositories/{fmt}/proxy"
        st, _ = client.request("GET", f"/service/rest/v1/repositories/{name}", expected_status=(200, 404))
        if st == 404:
            print(f"Creating repository: {name} ({fmt})")
            client.request("POST", endpoint, data=body, expected_status=(201,))
        elif update_existing:
            print(f"Updating repository: {name} ({fmt})")
            client.request("PUT", f"{endpoint}/{name}", data=body, expected_status=(204,))

    anon = config.get("anonymous")
    if anon:
        st, text = client.request("GET", "/service/rest/v1/security/anonymous", expected_status=(200,))
        current = json.loads(text) if text else {}
        if not current.get("enabled"):
            print("Enabling anonymous access")
            client.request("PUT", "/service/rest/v1/security/anonymous", data=anon, expected_status=(200,))

    realms = config.get("realms", [])
    if realms:
        st, text = client.request("GET", "/service/rest/v1/security/realms/active", expected_status=(200,))
        active = json.loads(text) if text else []
        needed = list(dict.fromkeys(active + realms))
        if needed != active:
            print(f"Activating realms: {needed}")
            client.request("PUT", "/service/rest/v1/security/realms/active", data=needed, expected_status=(204,))

    role = config.get("role")
    if role:
        st, text = client.request("GET", "/service/rest/v1/security/roles", expected_status=(200,))
        roles = json.loads(text) if text else []
        role_ids = [r.get("id") for r in roles]
        if role["id"] not in role_ids:
            print(f"Creating custom role: {role['id']}")
            client.request("POST", "/service/rest/v1/security/roles", data=role, expected_status=(200,))

    user = config.get("user")
    if user and deploy_pass:
        st, text = client.request("GET", "/service/rest/v1/security/users", expected_status=(200,))
        users = json.loads(text) if text else []
        user_ids = [u.get("userId") for u in users]
        if user["userId"] not in user_ids:
            print(f"Creating deploy user: {user['userId']}")
            user_payload = dict(user)
            user_payload["password"] = deploy_pass
            client.request("POST", "/service/rest/v1/security/users", data=user_payload, expected_status=(200,))


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text())

    if not args.apply:
        print("=== DRY RUN (No network changes made) ===")
        print(f"Target URL: {args.url}")
        print(f"Config path: {args.config}")
        print(f"Plan: 3 blob stores, 4 cleanup policies, {len(config.get('repositories', []))} proxy repositories.")
        print(f"Repositories: {', '.join(r['body']['name'] for r in config.get('repositories', []))}")
        print("Safety guarantees:")
        print("  - Existing repositories are preserved unless --update-existing is passed.")
        print("  - Default repositories are never deleted unless --delete-default-repos is passed.")
        print("To apply, run with --apply and set NEXUS_ADMIN_PASSWORD in the environment.")
        return 0

    password = os.environ.get("NEXUS_ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Enter Nexus admin password: ")

    client = NexusClient(args.url, args.user, password)
    if args.delete_default_repos:
        names = config.get("delete_repositories_opt_in", [])
        print("WARNING: These repositories and their contents may be deleted:")
        print("  " + ", ".join(names))
        if input("After verifying a backup, type DELETE DEFAULT REPOSITORIES: ") != "DELETE DEFAULT REPOSITORIES":
            print("Deletion cancelled; no changes made.", file=sys.stderr)
            return 1
    if args.wait > 0:
        print(f"Waiting up to {args.wait}s for {args.url} to report status 200...")
        if not client.wait_until_ready(args.wait):
            print("Timed out waiting for Nexus readiness.", file=sys.stderr)
            return 1

    deploy_pass = os.environ.get(args.deploy_user_password_env, "")
    if not deploy_pass and config.get("user"):
        deploy_pass = getpass.getpass("Deploy user password (empty skips user creation): ")
    apply_config(
        client,
        config,
        args.delete_default_repos,
        deploy_pass,
        update_existing=args.update_existing,
    )
    print("Nexus standalone configuration finished successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
