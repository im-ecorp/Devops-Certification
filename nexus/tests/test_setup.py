"""REST contract tests against an explicitly simulated local Nexus server."""
import contextlib
import importlib.util
import io
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import subprocess
import sys
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_setup():
    spec = importlib.util.spec_from_file_location('setup_nexus', ROOT / 'traefik/setup-nexus.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SetupTests(unittest.TestCase):
    def test_dry_run_is_default_and_offline(self):
        result = subprocess.run([sys.executable, str(ROOT / 'traefik/setup-nexus.py'), '--url', 'http://127.0.0.1:1'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('DRY RUN', result.stdout)
        self.assertIn('14 proxy repositories', result.stdout)

    def test_password_never_needed_as_command_argument(self):
        result = subprocess.run([sys.executable, str(ROOT / 'traefik/setup-nexus.py'), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertNotIn('--password', result.stdout)
        self.assertIn('--apply', result.stdout)
        self.assertIn('--update-existing', result.stdout)

    def test_create_and_rerun_preserve_existing_repositories(self):
        module = load_setup()
        config = json.loads((ROOT / 'traefik/nexus-config.json').read_text())
        requests = []
        exists = set()
        realms = ['NexusAuthenticatingRealm', 'NexusAuthorizingRealm']
        security = {'anonymous': {'enabled': False}, 'roles': [], 'users': []}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.dispatch('GET')

            def do_POST(self):
                self.dispatch('POST')

            def do_PUT(self):
                self.dispatch('PUT')

            def dispatch(self, method):
                payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or 'null')
                path = self.path
                requests.append((method, path, payload))
                result = None
                status = 200
                if method == 'GET':
                    if path.endswith('/realms/active'):
                        result = realms[:]
                    elif path.startswith('/service/rest/v1/security/'):
                        result = security[path.rsplit('/', 1)[1]]
                    elif path == '/service/rest/v1/status':
                        result = None
                    else:
                        status = 200 if path in exists else 404
                elif path.endswith('/realms/active'):
                    realms[:] = payload
                    status = 204
                elif path.endswith('/anonymous'):
                    security['anonymous'] = payload
                elif path.endswith('/security/roles'):
                    security['roles'].append(payload)
                elif path.endswith('/security/users'):
                    security['users'].append(payload)
                elif path.endswith('/blobstores/file'):
                    exists.add(path + '/' + payload['name'])
                    status = 204
                elif path.endswith('/cleanup-policies'):
                    exists.add(path + '/' + payload['name'])
                    status = 201
                elif path.endswith('/proxy'):
                    exists.add('/service/rest/v1/repositories/' + payload['name'])
                    status = 201
                else:
                    status = 204
                self.send_response(status)
                self.end_headers()
                if result is not None:
                    self.wfile.write(json.dumps(result).encode())

        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = module.NexusClient(f'http://127.0.0.1:{server.server_port}', 'admin', 'test-only')
            with contextlib.redirect_stdout(io.StringIO()):
                module.apply_config(client, config, False, 'test-only')
            self.assertEqual(sum(m == 'POST' and p.endswith('/proxy') for m, p, b in requests), 14)
            requests.clear()
            with contextlib.redirect_stdout(io.StringIO()):
                module.apply_config(client, config, False, 'test-only')
            self.assertTrue(all(m == 'GET' for m, p, b in requests), requests)
            self.assertEqual(realms, ['NexusAuthenticatingRealm', 'NexusAuthorizingRealm', 'DockerToken'])
            self.assertEqual(len(security['users']), 1)
            requests.clear()
            with contextlib.redirect_stdout(io.StringIO()):
                module.apply_config(client, config, False, 'test-only', update_existing=True)
            self.assertEqual(sum(m == 'PUT' and '/repositories/' in p for m, p, b in requests), 14)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_refuses_credentials_over_public_http(self):
        module = load_setup()
        with self.assertRaises(ValueError):
            module.NexusClient('http://repo.example.com', 'admin', 'test-only')

    def test_refuses_redirect_with_credentials(self):
        module = load_setup()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                self.send_response(302)
                self.send_header('Location', 'http://127.0.0.1:1/unsafe')
                self.end_headers()
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = module.NexusClient(f'http://127.0.0.1:{server.server_port}', 'admin', 'test-only')
            with self.assertRaises(RuntimeError):
                client.request('GET', '/service/rest/v1/status')
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
