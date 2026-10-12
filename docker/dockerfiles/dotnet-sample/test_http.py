import os
import subprocess
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


class ApiTests(unittest.TestCase):
    def test_greeting_and_health(self):
        root = Path(__file__).parent
        project = root / "DockerLearningApi.csproj"
        self.assertTrue(project.is_file(), "DockerLearningApi.csproj must exist")
        dotnet = os.environ.get("DOTNET", "dotnet")
        # A free local port avoids colliding with other developer services.
        import socket
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        process = subprocess.Popen(
            [dotnet, "run", "--no-launch-profile", "--project", str(project), "--no-build"],
            cwd=root, env={**os.environ, "ASPNETCORE_URLS": f"http://127.0.0.1:{port}"},
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
        )
        try:
            for _ in range(80):
                try:
                    with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                        self.assertEqual(response.read(), b'{"status":"ok"}')
                    break
                except (urllib.error.URLError, TimeoutError):
                    if process.poll() is not None:
                        self.fail(f"Application exited early: {process.stderr.read()}")
                    time.sleep(0.1)
            else:
                self.fail("Application did not start")
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=2) as response:
                self.assertEqual(response.read(), b'{"message":"Hello from .NET in Docker!"}')
            with self.assertRaises(urllib.error.HTTPError) as failure:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/missing", timeout=2)
            self.assertEqual(failure.exception.code, 404)
        finally:
            process.terminate()
            try:
                process.wait(timeout=4)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            process.stderr.close()


if __name__ == "__main__":
    unittest.main()
