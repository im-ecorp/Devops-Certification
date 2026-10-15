"""Render real configurations; never provision containers or contact a cluster."""
import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import textwrap
import unittest

import yaml
from jinja2 import Environment, StrictUndefined

ROLE = Path(__file__).resolve().parents[1]
ENV = Environment(undefined=StrictUndefined)


def render(name, **overrides):
    values = yaml.safe_load((ROLE / 'defaults/main/main.yml').read_text())
    values.update(service_dir='/tmp/argocd-test', argocd_domain='cd.example.test',
                  argocd_backend_host='argocd-control-plane',
                  argocd_resolved_version='v3.5.5', ansible_managed='Ansible managed')
    values.update(overrides)
    return ENV.from_string((ROLE / 'templates' / name).read_text()).render(**values)


class RenderTests(unittest.TestCase):
    def test_compose_domain_networks_and_no_public_backend_ports(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p / '.env').write_text(render('.env.j2', argocd_domain='other.example.test',
                                         argocd_proxy_port=8181))
            (p / 'docker-compose.yml').write_text(render('docker-compose.yml.j2'))
            config = json.loads(subprocess.check_output(
                ['docker', 'compose', '--project-directory', directory,
                 'config', '--format', 'json'], text=True))
        proxy = config['services']['argocd-proxy']
        self.assertFalse(proxy.get('ports'))
        self.assertEqual(set(proxy['networks']), {'web_net', 'cluster_net'})
        self.assertEqual(config['networks']['cluster_net']['name'], 'kind')
        labels = proxy['labels']
        self.assertEqual(labels['traefik.http.routers.argocd.rule'], 'Host(`other.example.test`)')
        self.assertEqual(labels['traefik.http.services.argocd.loadBalancer.server.port'], '8181')
        self.assertNotIn('traefik.http.routers.argocd.middlewares', labels)
        self.assertIn('${argocd_proxy_port}', proxy['healthcheck']['test'][1])

    def test_nginx_preserves_request_variables_for_runtime(self):
        config = render('nginx.conf.template.j2')
        # Official image only substitutes variables selected by this filter.
        compose = yaml.safe_load(render('docker-compose.yml.j2'))
        self.assertEqual(compose['services']['argocd-proxy']['environment']['NGINX_ENVSUBST_FILTER'], '^argocd_')
        for key, value in {'argocd_proxy_port': '8181', 'argocd_backend_host': 'node',
                           'argocd_node_port': '30443'}.items():
            config = config.replace('${' + key + '}', value)
        self.assertIn('listen 8181;', config)
        self.assertIn('"node:30443"', config)
        self.assertIn('proxy_set_header Host $http_host;', config)
        self.assertIn('proxy_pass https://$argocd_backend;', config)
        self.assertIn('resolver 127.0.0.11', config)

    @unittest.skipUnless(os.environ.get('KUBECTL') or shutil.which('kubectl'), 'Set KUBECTL for offline Kustomize validation')
    def test_kustomize_nodeport_merge_and_disabled_routing(self):
        # A realistic Service fixture catches incorrect ServicePort merge keys.
        fixture = """apiVersion: v1
kind: Service
metadata:
  name: argocd-server
spec:
  type: ClusterIP
  selector:
    app.kubernetes.io/name: argocd-server
  ports:
    - name: http
      port: 80
      targetPort: 8080
    - name: https
      port: 443
      targetPort: 8080
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
data: {}
"""
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p / 'install-v3.5.5.yml').write_text(fixture)
            for enabled in (True, False):
                with self.subTest(enabled=enabled):
                    (p / 'kustomization.yaml').write_text(render(
                        'kustomization.yml.j2', argocd_traefik_enabled=enabled,
                        argocd_node_port=31443))
                    docs = list(yaml.safe_load_all(subprocess.check_output(
                        [os.environ.get('KUBECTL') or 'kubectl', 'kustomize', directory], text=True)))
                    service = next(d for d in docs if d['kind'] == 'Service')
                    cm = next(d for d in docs if d['kind'] == 'ConfigMap')
                    self.assertEqual(service['spec']['selector'], {'app.kubernetes.io/name': 'argocd-server'})
                    if enabled:
                        self.assertEqual(service['spec']['type'], 'NodePort')
                        self.assertEqual(service['spec']['ports'], [{
                            'name': 'https', 'port': 443, 'targetPort': 8080,
                            'protocol': 'TCP', 'nodePort': 31443}])
                        self.assertEqual(cm['data']['url'], 'https://cd.example.test')
                    else:
                        self.assertEqual(service['spec']['type'], 'ClusterIP')
                        self.assertEqual(len(service['spec']['ports']), 2)
                        self.assertFalse(cm.get('data'))


@unittest.skipUnless(shutil.which('ansible-playbook'), 'ansible-playbook is required')
class RoleBehaviorTests(unittest.TestCase):
    """Run the actual role locally; kubectl only records calls and returns fixtures."""

    def run_role(self, *, tag='deploy', check=False, fresh=False, diff_rc=0, client_minor='36',
                 server_minor='36', corrupt=False, prepared_release='v3.5.5', **overrides):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p / 'ansible.cfg').write_text('[defaults]\nretry_files_enabled = False\n')
            service = p / 'argocd'
            service.mkdir()
            binary = p / 'bin'
            binary.mkdir()
            log = p / 'kubectl-calls.jsonl'
            fake = binary / 'kubectl'
            fake.write_text(textwrap.dedent("""\
                #!/usr/bin/env python3
                import json, os, sys
                args = sys.argv[1:]
                with open(os.environ['ARGOCD_TEST_LOG'], 'a') as f:
                    f.write(json.dumps(args) + '\\n')
                if '--raw=/readyz' in args:
                    print('ok')
                elif 'version' in args:
                    print(json.dumps({
                        'clientVersion': {'major': '1', 'minor': os.environ['ARGOCD_TEST_CLIENT_MINOR']},
                        'serverVersion': {'major': '1', 'minor': os.environ['ARGOCD_TEST_SERVER_MINOR']}}))
                elif 'diff' in args:
                    sys.exit(int(os.environ['ARGOCD_TEST_DIFF_RC']))
                elif 'apply' in args:
                    print('unchanged')
                elif 'kustomize' in args or 'rollout' in args:
                    pass
                else:
                    sys.exit('Unexpected kubectl call: ' + repr(args))
                """))
            fake.chmod(0o755)
            kubeconfig = p / 'kubeconfig'
            kubeconfig.write_text('test fixture only')
            manifest = 'apiVersion: v1\nkind: ConfigMap\nmetadata:\n  name: argocd-cm\n'
            expected_hash = hashlib.sha256(manifest.encode()).hexdigest()
            (service / 'install-v3.5.5.yml').write_text(manifest + ('# tampered\n' if corrupt else ''))
            (service / 'kustomization.yaml').write_text(render(
                'kustomization.yml.j2', argocd_traefik_enabled=False,
                argocd_resolved_version=prepared_release))
            (service / 'namespace.yml').write_text(render('namespace.yml.j2'))
            variables = dict(
                service_dir=str(service), argocd_use_kind=False,
                argocd_traefik_enabled=False, argocd_kubeconfig=str(kubeconfig),
                argocd_kubectl_context='role-test', argocd_domain='cd.example.test',
                argocd_manifest_checksums={'v3.5.5': expected_hash})
            variables.update(overrides)
            if fresh:
                variables['service_dir'] = str(p / 'new-service')
            playbook = p / 'playbook.yml'
            playbook.write_text(yaml.safe_dump([dict(
                name='Validate Argo CD role without a cluster', hosts='localhost',
                connection='local', gather_facts=False, become=False,
                vars=variables, roles=[str(ROLE)])]))
            env = dict(os.environ,
                       PATH=str(binary) + os.pathsep + os.environ['PATH'],
                       ANSIBLE_CONFIG=str(p / 'ansible.cfg'), ANSIBLE_LOG_PATH=str(p / 'ansible.log'),
                       ANSIBLE_NOCOLOR='1', ANSIBLE_LOCAL_TEMP=str(p / 'ansible-tmp'),
                       ARGOCD_TEST_LOG=str(log), ARGOCD_TEST_DIFF_RC=str(diff_rc),
                       ARGOCD_TEST_CLIENT_MINOR=client_minor,
                       ARGOCD_TEST_SERVER_MINOR=server_minor)
            result = subprocess.run(
                ['ansible-playbook', '-i', 'localhost,', str(playbook), '--tags', tag] +
                (['--check'] if check else []),
                env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                timeout=60)
            calls = [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []
            return result, calls

    def test_tagged_prepare_and_pull_resolve_the_release(self):
        # --list-tasks checks selection without executing network or Docker tasks.
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory) / 'playbook.yml'
            config = p.with_suffix('.cfg')
            config.write_text('[defaults]\nretry_files_enabled = False\n')
            p.write_text(yaml.safe_dump([dict(hosts='localhost', gather_facts=False,
                                            roles=[str(ROLE)])]))
            for tag in ('preparing', 'pull', 'deploy', 'install_argocd', 'setup_argocd'):
                with self.subTest(tag=tag):
                    result = subprocess.run(
                        ['ansible-playbook', '-i', 'localhost,', str(p), '--list-tasks', '--tags', tag],
                        env=dict(os.environ, ANSIBLE_CONFIG=str(config), ANSIBLE_NOCOLOR='1'),
                        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
                    self.assertEqual(result.returncode, 0, result.stdout)
                    self.assertIn('Select the exact Argo CD release', result.stdout)
                    if tag in ('install_argocd', 'setup_argocd'):
                        self.assertIn('Deploy Docker Compose stack', result.stdout)

    def test_deploy_accepts_supported_skew_and_applies_only_a_real_diff(self):
        for diff_rc in (0, 1):
            with self.subTest(diff_rc=diff_rc):
                result, calls = self.run_role(diff_rc=diff_rc, client_minor='35+', server_minor='36')
                self.assertEqual(result.returncode, 0, result.stdout)
                self.assertTrue(any('kustomize' in call for call in calls))
                applies = [call for call in calls if 'apply' in call and '-k' in call]
                self.assertEqual(len(applies), diff_rc)
                self.assertFalse(any('--force-conflicts' in call for call in calls))

    def test_check_mode_handles_a_missing_service_directory(self):
        result, calls = self.run_role(tag='all', check=True, fresh=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertFalse(any('apply' in call for call in calls))

    def test_deploy_refuses_unknown_or_tampered_manifest_before_apply(self):
        for overrides in (dict(argocd_release='v3.5.6'), dict(corrupt=True)):
            with self.subTest(overrides=overrides):
                result, calls = self.run_role(**overrides)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertFalse(any('apply' in call for call in calls))
                self.assertIn('checksum', result.stdout.lower())

    def test_deploy_refuses_stale_customization_before_apply(self):
        result, calls = self.run_role(prepared_release='v3.5.4')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('customization targets another release', result.stdout)
        self.assertFalse(any('apply' in call for call in calls))

    def test_deploy_refuses_incompatible_kubectl_before_apply(self):
        result, calls = self.run_role(client_minor='33', server_minor='36')
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('within one minor version', result.stdout)
        self.assertFalse(any('apply' in call for call in calls))

    def test_diff_errors_never_trigger_manifest_apply(self):
        result, calls = self.run_role(diff_rc=2)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertTrue(any('diff' in call for call in calls), result.stdout)
        self.assertFalse(any('apply' in call and '-k' in call for call in calls))


if __name__ == '__main__':
    unittest.main()
