#!/usr/bin/env python3
"""Offline validation of packaged rollout tools. Dummy credentials only."""
import json
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
RENDER=ROOT/'scripts/client/render-ping-provider.sh'
VERIFY=ROOT/'scripts/client/verify-policy-schema.sh'


class PublicRolloutAssets(unittest.TestCase):
    def render(self, secret, output, enabled=False, method='client_secret_basic', scopes='openid profile email'):
        command=[str(RENDER),'--client-secret-file',str(secret),'--output',str(output),'--client-auth-method',method,'--scopes',scopes]
        if enabled: command.append('--enable')
        return subprocess.run(command,capture_output=True,text=True)

    def test_secret_stays_private_and_provider_disabled_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);secret=root/'secret';secret.write_text('dummy-only-never-live\r\n')
            for method in ['client_secret_basic','client_secret_post']:
                for enabled in [False,True]:
                    output=root/f'{method}-{enabled}.private.json'
                    result=self.render(secret,output,enabled,method)
                    self.assertEqual(result.returncode,0,result.stderr)
                    self.assertNotIn('dummy-only',result.stdout+result.stderr)
                    provider=json.loads(output.read_text())
                    self.assertEqual(provider['enabled'],enabled)
                    self.assertEqual(provider['config']['clientSecret'],'dummy-only-never-live')
                    self.assertEqual(provider['config']['clientAuthMethod'],method)
                    self.assertEqual(provider['config']['issuer'],'https://ping-sso-uat.schneider-electric.com')
                    self.assertFalse(provider['trustEmail']);self.assertFalse(provider['storeToken'])
                    self.assertEqual(provider['config']['validateSignature'],'true')
                    self.assertEqual(stat.S_IMODE(output.stat().st_mode),0o600)
                    original=output.read_bytes()
                    self.assertNotEqual(self.render(secret,output,enabled,method).returncode,0)
                    self.assertEqual(output.read_bytes(),original)

    def test_bad_inputs_do_not_write_or_expose_secret(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);secret=root/'secret';secret.write_text('dummy-only-never-live')
            for method,scopes in [('','openid'),('client_secret_jwt','openid'),('client_secret_basic','profile email')]:
                result=self.render(secret,root/'output.private.json',True,method,scopes)
                self.assertNotEqual(result.returncode,0)
                self.assertFalse((root/'output.private.json').exists())
                self.assertNotIn('dummy-only',result.stdout+result.stderr)
            secret.write_text(' \n')
            self.assertNotEqual(self.render(secret,root/'output.private.json').returncode,0)
            self.assertFalse((root/'output.private.json').exists())

    def test_existing_provider_options_are_preserved_and_wrong_alias_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);secret=root/'secret';secret.write_text('dummy-only')
            existing=root/'previous.private.json'
            provider=json.loads((ROOT/'identity/ping-uat.json').read_text())
            provider['config']['clientSecret']='********'
            provider['config']['clientSpecificOption']='retain-this-option'
            provider['internalId']='existing-internal-identity'
            existing.write_text(json.dumps(provider))
            output=root/'new.private.json'
            command=[str(RENDER),'--client-secret-file',str(secret),'--output',str(output),'--client-auth-method','client_secret_basic','--scopes','openid','--existing-provider-file',str(existing),'--enable']
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            rendered=json.loads(output.read_text())
            self.assertEqual(rendered['config']['clientSpecificOption'],'retain-this-option')
            self.assertEqual(rendered['config']['clientSecret'],'dummy-only')
            self.assertEqual(rendered['internalId'],'existing-internal-identity')
            output.unlink();provider['alias']='other-provider';existing.write_text(json.dumps(provider))
            self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
            self.assertFalse(output.exists())

    def test_schema_manifest_and_candidate_image_comparison(self):
        self.assertEqual(subprocess.run([str(VERIFY)],capture_output=True).returncode,0)
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'schema';shutil.copytree(ROOT/'rollouts/ping-policy-studio/schema',target)
            (target/'005_policy_lifecycle.down.sql').write_text('-- ignored, never executed\n')
            self.assertEqual(subprocess.run([str(VERIFY),str(target)],capture_output=True).returncode,0)
            unknown=target/'012_unreviewed.sql';unknown.write_text('SELECT 1;')
            self.assertNotEqual(subprocess.run([str(VERIFY),str(target)],capture_output=True).returncode,0)
            unknown.unlink()
            first=target/'004_policy_persistence.sql';first.write_text(first.read_text()+'\n-- changed\n')
            self.assertNotEqual(subprocess.run([str(VERIFY),str(target)],capture_output=True).returncode,0)

    def test_chart_policy_profile_is_opt_in_and_startup_ddl_stays_off(self):
        for chart,overlay in [('applications/logai','applications/logai/values-eu-west-3-eks-shared-dev.yaml'),('helm/gamestory-schneider-platform','environments/uat/values.yaml')]:
            command=['helm','template','logai',str(ROOT/chart),'-f',str(ROOT/overlay)]
            baseline=subprocess.run(command,capture_output=True,text=True,check=True).stdout
            self.assertNotIn('name: POLICY_STORAGE_BACKEND',baseline)
            rendered=subprocess.run([*command,'--set','logaiApi.policyConfigMap=approved-existing-profile'],capture_output=True,text=True,check=True).stdout
            self.assertIn('name: POLICY_STORAGE_BACKEND',rendered)
            self.assertIn('name: approved-existing-profile',rendered)
            self.assertNotIn('name: AWS_SECRET_ACCESS_KEY',rendered)
            deployments=[d for d in yaml.safe_load_all(rendered) if d and d.get('kind')=='Deployment']
            api=next(c for d in deployments for c in d['spec']['template']['spec']['containers'] if c['name']=='logai-api')
            env={entry['name']:entry for entry in api['env']}
            self.assertEqual(str(env['APPLY_DATABASE_SCHEMA_ON_STARTUP']['value']).lower(),'false')
            self.assertEqual(str(env['SEED_SAMPLE_DATA_ON_STARTUP']['value']).lower(),'false')
            self.assertEqual(env['POLICY_STORAGE_BACKEND']['valueFrom']['configMapKeyRef']['name'],'approved-existing-profile')
            # Existing chart tests parse environment values; defaults must remain false.
            self.assertNotIn('POLICY_LIFECYCLE_ACTIVATION_ENABLED, value: "true"',rendered)


if __name__=='__main__': unittest.main()
