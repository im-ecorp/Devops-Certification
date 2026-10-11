#!/usr/bin/env python3
"""Exercise the actual lab configs using a local Nginx binary and HTTP origins.

No system service changes. Each lab gets its own scratch prefix and free ports.
Scratch evidence is retained; only child processes started here are stopped.
"""
import argparse
import collections
import http.client
import http.server
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
LABS = {
    "reverse-proxy/basic": 8081,
    "reverse-proxy/advanced": 8082,
    "forward-proxy": 8083,
    "caching-server/basic": 8084,
    "caching-server/advanced": 8085,
    "load-balancer/basic": 8086,
    "load-balancer/advanced": 8087,
}
BINARY = "nginx"


class Origin(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.requests += 1
        body = json.dumps({
            "origin": self.server.identity,
            "request": self.server.requests,
            "path": self.path,
            "host": self.headers.get("Host"),
            "forwarded_proto": self.headers.get("X-Forwarded-Proto"),
            "upgrade": self.headers.get("Upgrade"),
            "connection": self.headers.get("Connection"),
        }).encode()
        if self.headers.get("Upgrade", "").lower() == "websocket":
            # Only a handshake fixture, not a full WebSocket application.
            self.send_response(101)
            self.send_header("Upgrade", "websocket")
            self.send_header("Connection", "Upgrade")
            self.end_headers()
            return
        self.send_response(200)
        if self.path.startswith("/no-store"):
            self.send_header("Cache-Control", "no-store")
        if self.path.startswith("/set-cookie"):
            self.send_header("Set-Cookie", "session=lab; HttpOnly")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


class LabTests(unittest.TestCase):
    def setUp(self):
        self.origins = []
        self.process = None
        self.output = None
        self.scratch = Path(tempfile.mkdtemp(prefix="nginx-lab-"))
        self.addCleanup(self.stop_children)
        for identity in ("A", "B"):
            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Origin)
            server.identity = identity
            server.requests = 0
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.origins.append(server)
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            self.port = sock.getsockname()[1]

    def stop_children(self):
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        if self.output is not None:
            self.output.close()
        for server in self.origins:
            server.shutdown()
            server.server_close()

    def start_lab(self, lab):
        text = (ROOT / lab / "nginx.conf").read_text()
        for old, server in zip((9001, 9002), self.origins):
            text = text.replace(f"127.0.0.1:{old}", f"127.0.0.1:{server.server_port}")
        text = text.replace(f"127.0.0.1:{LABS[lab]}", f"127.0.0.1:{self.port}")
        (self.scratch / "nginx.conf").write_text(text)
        for folder in ("logs", "temp/client", "temp/proxy", "temp/fastcgi",
                       "temp/uwsgi", "temp/scgi", "cache/basic", "cache/advanced"):
            (self.scratch / folder).mkdir(parents=True, exist_ok=True)
        # Nginx started as root otherwise drops workers to nobody, which cannot
        # traverse mkdtemp's mode-0700 prefix. This isolated test uses root only
        # when the invoking user is already root; all listeners are loopback.
        global_flags = "daemon off;" + (" user root;" if os.geteuid() == 0 else "")
        args = [BINARY, "-p", str(self.scratch) + "/", "-c", "nginx.conf"]
        check = subprocess.run(args + ["-t"], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.output = (self.scratch / "startup.log").open("w")
        self.process = subprocess.Popen(
            args + ["-g", global_flags], stdout=self.output, stderr=self.output)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            self.assertIsNone(self.process.poll(), f"Startup failed: {self.scratch}")
            try:
                with socket.create_connection(("127.0.0.1", self.port), timeout=0.1):
                    return
            except OSError:
                time.sleep(0.05)
        self.fail(f"Nginx did not start: {self.scratch}")

    def request(self, path="/", headers=None, method="GET"):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            conn.request(method, path, headers=headers or {})
            response = conn.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            conn.close()

    def test_reverse_basic(self):
        self.start_lab("reverse-proxy/basic")
        code, _, body = self.request("/learning?value=1")
        self.assertEqual(code, 200)
        data = json.loads(body)
        self.assertEqual(data["origin"], "A")
        self.assertEqual(data["path"], "/learning?value=1")
        self.assertEqual(data["forwarded_proto"], "http")

    def test_reverse_advanced(self):
        self.start_lab("reverse-proxy/advanced")
        self.assertEqual(self.request()[0], 200)
        code, headers, _ = self.request("/ws", {
            "Upgrade": "websocket", "Connection": "Upgrade"})
        self.assertEqual(code, 101)
        self.assertEqual(headers["Upgrade"].lower(), "websocket")

    def test_forward(self):
        self.start_lab("forward-proxy")
        origin = self.origins[0].server_port
        code, _, body = self.request(f"http://127.0.0.1:{origin}/learning?q=1")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(body)["path"], "/learning?q=1")
        self.assertEqual(self.request("http://example.invalid/")[0], 403)
        # Core Nginx may reject CONNECT during parsing before the location.
        self.assertIn(self.request("example.invalid:443", method="CONNECT")[0], (400, 405))

    def assert_cache(self, lab):
        self.start_lab(lab)
        first = self.request("/cache")
        second = self.request("/cache")
        self.assertEqual(first[0], 200)
        self.assertEqual(first[1]["X-Cache-Status"], "MISS")
        self.assertEqual(second[1]["X-Cache-Status"], "HIT")
        self.assertEqual(first[2], second[2])
        for path in ("/no-store", "/set-cookie"):
            one, two = self.request(path), self.request(path)
            self.assertNotEqual(one[2], two[2])
            self.assertNotEqual(two[1].get("X-Cache-Status"), "HIT")

    def test_cache_basic(self):
        self.assert_cache("caching-server/basic")

    def test_cache_advanced(self):
        self.assert_cache("caching-server/advanced")
        for headers in ({"Cookie": "session=student"},
                        {"Authorization": "Bearer practice-only"}):
            one = self.request("/personal", headers)
            two = self.request("/personal", headers)
            self.assertEqual(two[1]["X-Cache-Status"], "BYPASS")
            self.assertNotEqual(one[2], two[2])
        one, two = self.request("/private/profile"), self.request("/private/profile")
        self.assertEqual(two[1]["X-Cache-Status"], "BYPASS")
        self.assertNotEqual(one[2], two[2])
        # Warm cache, stop origin, wait beyond TTL, then prove stale availability.
        cached = self.request("/stale")[2]
        self.origins[0].shutdown()
        self.origins[0].server_close()
        time.sleep(11)
        code, headers, body = self.request("/stale")
        self.assertEqual(code, 200)
        self.assertIn(headers["X-Cache-Status"], ("STALE", "UPDATING"))
        self.assertEqual(body, cached)

    def test_balancer_basic(self):
        self.start_lab("load-balancer/basic")
        counts = collections.Counter(json.loads(self.request()[2])["origin"] for _ in range(8))
        self.assertEqual(counts, {"A": 4, "B": 4})

    def test_balancer_advanced(self):
        self.start_lab("load-balancer/advanced")
        identities = {json.loads(self.request()[2])["origin"] for _ in range(4)}
        self.assertEqual(identities, {"A", "B"})
        self.origins[0].shutdown()
        self.origins[0].server_close()
        for _ in range(4):
            code, _, body = self.request()
            self.assertEqual(code, 200)
            self.assertEqual(json.loads(body)["origin"], "B")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nginx", default=shutil.which("nginx"))
    parser.add_argument("tests", nargs="*", help="Optional unittest method names")
    options = parser.parse_args()
    if not options.nginx:
        parser.error("Nginx not found. Install Nginx or pass --nginx /path/to/nginx.")
    BINARY = str(Path(options.nginx).resolve())
    # Do not create bytecode in the repository or change system Nginx state.
    unittest.main(argv=[__file__] + options.tests, verbosity=2)
