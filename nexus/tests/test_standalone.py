"""Standalone configuration regression checks; no Docker daemon required."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PYYAML_BIN = Path(sys.executable)


class ConfigurationTests(unittest.TestCase):
    def test_preserved_repository_settings(self):
        for variant in ('traefik', 'nginx'):
            path = ROOT / variant / 'nexus-config.json'
            self.assertTrue(path.is_file(), f'Missing standalone settings: {path}')
            config = json.loads(path.read_text())
            self.assertEqual(len(config['repositories']), 14)
            docker = [r for r in config['repositories'] if r['format'] == 'docker']
            self.assertEqual([r['body']['docker']['httpPort'] for r in docker], list(range(9091, 9097)))
            self.assertEqual(docker[0]['body']['proxy']['remoteUrl'], 'https://hub.hamdocker.ir')
            self.assertEqual(config['anonymous']['enabled'], True)
            self.assertEqual(config['realms'], ['DockerToken'])
            self.assertEqual(config['role']['privileges'], ['nx-repository-view-*-*-*'])
            self.assertEqual(config['user']['roles'], ['nx-deploy'])
            self.assertNotIn('password', config['user'])

    def test_compose_structure(self):
        code = '''
import json, yaml, sys
for path in sys.argv[1:]:
    with open(path) as f:
        data = yaml.safe_load(f)
    services = data['services']
    assert 'nexus' in services, f'nexus missing in {path}'
    nexus = services['nexus']
    assert nexus['image'] == 'sonatype/nexus3:${NEXUS_IMAGE_TAG:-3.94.1}'
    assert nexus['container_name'] == 'nexus'
    assert nexus['restart'] == '${RESTART_POLICY:-always}'
    assert 'nexus_data:/nexus-data' in nexus['volumes']
    assert nexus['environment']['NEXUS_SECURITY_RANDOMPASSWORD'] == 'false'
    assert nexus['environment']['NEXUS_SECURITY_INITIAL_PASSWORD'] == '${NEXUS_ADMIN_PASSWORD}'
    assert 'service/rest/v1/status' in ' '.join(nexus['healthcheck']['test'])
    assert 'nexus_data' in data.get('volumes', {})
print("COMPOSE_OK")
'''
        proc = subprocess.run(
            [str(PYYAML_BIN), '-c', code, str(ROOT / 'traefik' / 'docker-compose.yml'), str(ROOT / 'nginx' / 'docker-compose.yml')],
            capture_output=True,
            text=True,
            check=False
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("COMPOSE_OK", proc.stdout)

    def test_traefik_labels(self):
        code = '''
import yaml, sys
with open(sys.argv[1]) as f:
    data = yaml.safe_load(f)
labels = data['services']['nexus']['labels']
assert 'traefik.enable=true' in labels
assert 'traefik.http.routers.repo.rule=Host(`${NEXUS_MAIN_DOMAIN:-repo.w.k8sforfun.com}`)' in labels
assert 'traefik.http.services.repo.loadBalancer.server.port=8081' in labels
assert 'traefik.http.routers.hub.rule=Host(`${NEXUS_HUB_DOMAIN:-hub.w.k8sforfun.com}`)' in labels
assert 'traefik.http.services.hub.loadBalancer.server.port=9091' in labels
assert 'traefik.http.routers.github.rule=Host(`${NEXUS_GITHUB_DOMAIN:-github.w.k8sforfun.com}`)' in labels
assert 'traefik.http.services.github.loadBalancer.server.port=9096' in labels
print("TRAEFIK_LABELS_OK")
'''
        proc = subprocess.run(
            [str(PYYAML_BIN), '-c', code, str(ROOT / 'traefik' / 'docker-compose.yml')],
            capture_output=True,
            text=True,
            check=False
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("TRAEFIK_LABELS_OK", proc.stdout)

    def test_nginx_standalone_config(self):
        conf_text = (ROOT / 'nginx' / 'conf.d' / 'nexus.conf').read_text()
        self.assertIn('upstream nexus_web {', conf_text)
        self.assertIn('server nexus:8081;', conf_text)
        self.assertIn('upstream docker_hub {', conf_text)
        self.assertIn('server nexus:9091;', conf_text)
        self.assertIn('upstream docker_github {', conf_text)
        self.assertIn('server nexus:9096;', conf_text)
        self.assertIn('client_max_body_size 0;', conf_text)
        self.assertIn('proxy_set_header X-Forwarded-Proto $scheme;', conf_text)
        self.assertIn('ssl_certificate', conf_text)


if __name__ == '__main__':
    unittest.main()
