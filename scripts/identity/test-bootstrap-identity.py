#!/usr/bin/env python3
"""Compose lifecycle contract: shared reconciler, health gate and rerun/failure behaviour."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[2]

class ComposeLifecycleTests(unittest.TestCase):
    def test_every_environment_uses_same_compiled_entrypoint_and_account_model(self):
        config=yaml.safe_load((ROOT/'compose.yaml').read_text())
        job=config['services']['identity-bootstrap']
        self.assertEqual(job['command'],['python','-c','from app.bootstrap import main; main()'])
        self.assertEqual(job['restart'],'no')
        self.assertEqual(job['depends_on']['keycloak']['condition'],'service_healthy')
        self.assertTrue(job['read_only'])
        for upstream in ['keycloak','postgres']:
            self.assertIn('./licensing/'+upstream+':/usr/share/licenses/logai-platform/'+upstream+':ro',config['services'][upstream]['volumes'])

        for service in ['identity-api','logai-api']:
            self.assertEqual(config['services'][service]['depends_on']['identity-bootstrap']['condition'],'service_completed_successfully')
        for env in ['build','release','client-local']:
            text=(ROOT/'environments'/env/'compose.env.example').read_text()
            self.assertIn('NEXT_PUBLIC_AUTH_MODE=sso',text)
            self.assertIn('LOGAI_ENV='+env,text)
            self.assertIn('KEYCLOAK_LOGAI_BOOTSTRAP_PASSWORD=',text)
        self.assertNotIn('def bootstrap(', (ROOT/'scripts/identity/bootstrap-identity.py').read_text())

    def commands(self,failure=False):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);log=path/'commands';envfile=path/'compose.env';envfile.write_text('')
            engine=path/'podman';engine.write_text("#!/usr/bin/env python3\nimport json,os,sys\nwith open(os.environ['COMMAND_LOG'],'a') as f:f.write(json.dumps(sys.argv[1:])+'\\n')\nif 'run' in sys.argv and os.getenv('FAIL_BOOTSTRAP'):sys.exit(17)\n")
            engine.chmod(0o755)
            env={**os.environ,'PATH':str(path)+':'+os.environ['PATH'],'COMMAND_LOG':str(log)}
            if failure:env['FAIL_BOOTSTRAP']='1'
            results=[subprocess.run(['bash',str(ROOT/'scripts/client/deploy-compose.sh'),str(envfile)],env=env,capture_output=True) for _ in range(2)]
            return results,[json.loads(line) for line in log.read_text().splitlines()]

    def test_redeployment_always_runs_a_fresh_job_before_applications(self):
        results,commands=self.commands()
        self.assertTrue(all(r.returncode==0 for r in results))
        jobs=[i for i,c in enumerate(commands) if 'run' in c]
        apps=[i for i,c in enumerate(commands) if 'up' in c and 'logai-ui' in c]
        self.assertEqual(len(jobs),2);self.assertEqual(len(apps),2)
        self.assertTrue(all(j<a for j,a in zip(jobs,apps)))
        for i in jobs:self.assertIn('--rm',commands[i]);self.assertIn('identity-bootstrap',commands[i])

    def test_failed_reconciliation_stops_deployment(self):
        results,commands=self.commands(True)
        self.assertTrue(all(r.returncode==17 for r in results))
        self.assertFalse(any('up' in c and 'logai-ui' in c for c in commands))

if __name__=='__main__':unittest.main()
