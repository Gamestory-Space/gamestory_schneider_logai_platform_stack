#!/usr/bin/env python3
"""Render the transfer fragment against a synthetic captured-state fixture, never remote values."""
import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--helm', default='helm')
args = parser.parse_args()
source = ROOT / 'handover/schneider-argocd'
with tempfile.TemporaryDirectory() as directory:
    chart = Path(directory)
    shutil.copytree(source / 'templates', chart / 'templates')
    shutil.copytree(source / 'files', chart / 'files')
    (chart / 'Chart.yaml').write_text('apiVersion: v2\nname: transfer-contract-fixture\nversion: 0.0.0\n')
    values = yaml.safe_load((source / 'values-transfer.yaml').read_text())
    values.update(namespace='fixture-logai', hosts={k: k + '.fixture.invalid' for k in ['ui', 'api', 'identity', 'auth']},
                  database={'host': 'db.fixture.invalid'}, keycloak={'enabled': True, 'secretName': 'logai-keycloak'}, imagePullSecret='registry-fixture')
    values['identityApi']['image'].update(repository='docker.io/chrismdgs/gamestory_logai_schneider', pullPolicy='IfNotPresent')
    (chart / 'values.yaml').write_text(yaml.safe_dump(values))
    def render(*overrides, success=True):
        result = subprocess.run([args.helm, 'template', 'fixture', str(chart), *overrides], capture_output=True, text=True)
        assert (result.returncode == 0) == success, result.stderr
        return list(yaml.safe_load_all(result.stdout)) if success else []
    resources = render()
    job = next(r for r in resources if r['kind'] == 'Job')
    config = next(r for r in resources if r['kind'] == 'ConfigMap')
    assert len(resources) == 2
    assert job['metadata']['namespace'] == 'fixture-logai'
    assert job['metadata']['annotations'] == {'argocd.argoproj.io/hook': 'PostSync', 'argocd.argoproj.io/hook-delete-policy': 'BeforeHookCreation,HookSucceeded'}
    assert 'ttlSecondsAfterFinished' not in job['spec']
    pod = job['spec']['template']['spec']
    container = pod['containers'][0]
    assert container['image'].endswith(':identity-api-v0.1.7')
    assert container['command'] == ['python', '-c', 'from app.bootstrap import main; main()']
    env = {item['name']: item['value'] for item in container['env']}
    assert env['KEYCLOAK_BOOTSTRAP_URL'] == 'http://keycloak:80'
    assert env['KEYCLOAK_BOOTSTRAP_HEALTH_URL'] == 'http://keycloak:9000/health/ready'
    assert env['LOGAI_PUBLIC_URL'] == 'https://ui.fixture.invalid'
    assert env['KEYCLOAK_PUBLIC_URL'] == 'https://auth.fixture.invalid'
    assert pod['imagePullSecrets'] == [{'name': 'registry-fixture'}]
    assert not pod['automountServiceAccountToken']
    assert container['securityContext']['readOnlyRootFilesystem']
    admin = next(v['secret'] for v in pod['volumes'] if v['name'] == 'admin-secret')
    assert admin['secretName'] == 'logai-keycloak'
    assert {i['key'] for i in admin['items']} == {'admin-username', 'admin-password'}
    realm = json.loads(config['data']['realm.json'])
    ui = next(c for c in realm['clients'] if c['clientId'] == 'logai-ui')
    assert ui['redirectUris'] == ['https://ui.fixture.invalid/auth/callback']
    assert ui['webOrigins'] == ['https://ui.fixture.invalid']
    for filename in ['gamestory-sso-realm.json', 'bootstrap-groups.json']:
        assert (source / 'files' / filename).read_bytes() == (ROOT / 'helm/gamestory-schneider-platform/files' / filename).read_bytes()
    shared = render('--set', 'identityBootstrap.passwordMode=shared')
    job = next(r for r in shared if r['kind'] == 'Job')
    assert sum('secret' in v for v in job['spec']['template']['spec']['volumes']) == 2
    assert not render('--set', 'identityBootstrap.enabled=false')
    for setting in ['hosts.ui=', 'hosts.auth=', 'hosts.api=', 'hosts.identity=', 'hosts.ui=https://bad.invalid', 'database.host=', 'keycloak.secretName=', 'keycloak.enabled=false', 'identity.authMode=none', 'identity.clientId=gamestory-ui', 'identityBootstrap.passwordMode=invalid']:
        render('--set', setting, success=False)
print('PASS: Schneider transfer rendering, hooks, URLs, Secret projections, shared mode, canonical file parity and missing-input rejection')
