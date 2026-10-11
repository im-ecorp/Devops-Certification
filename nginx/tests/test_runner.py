"""CLI acceptance test: runner starts both origins and serves a chosen lab."""
import os
import shutil
from pathlib import Path
import socket
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RunnerTest(unittest.TestCase):
    def test_runner_serves_and_stops(self):
        with socket.socket() as sock:
            result = sock.connect_ex(("127.0.0.1", 8081))
            if result == 0:
                self.skipTest("Lab port 8081 is occupied")
        process = subprocess.Popen(
            [sys.executable, str(ROOT / "scripts" / "run_lab.py"),
             "reverse-proxy/basic", "--nginx", os.environ.get("NGINX_BINARY", shutil.which("nginx") or "nginx")],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    self.fail("Runner exited before serving requests: " + process.communicate()[1])
                try:
                    import urllib.request
                    with urllib.request.urlopen("http://127.0.0.1:8081/", timeout=0.5) as response:
                        self.assertIn(b"Origin A", response.read())
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                self.fail("Runner did not start")
        finally:
            process.terminate()
            process.communicate(timeout=5)
        with socket.socket() as sock:
            self.assertNotEqual(sock.connect_ex(("127.0.0.1", 8081)), 0)


if __name__ == "__main__":
    unittest.main()
