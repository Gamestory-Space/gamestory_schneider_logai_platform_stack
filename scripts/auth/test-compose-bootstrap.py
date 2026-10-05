#!/usr/bin/env python3
"""Disposable real Compose acceptance; never accesses the existing client project."""
import argparse,importlib.util,json,os,secrets,socket,subprocess,tempfile,time
from pathlib import Path
import yaml
parser=argparse.ArgumentParser()
parser.add_argument('--engine',choices=['podman-compose','docker'],default='podman-compose')
parser.add_argument('--identity-image',required=True)
args=parser.parse_args()
P=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('admin',P/'scripts/identity/bootstrap-keycloak-user.py');adminmodule=importlib.util.module_from_spec(spec);spec.loader.exec_module(adminmodule)
with tempfile.TemporaryDirectory(prefix='logai-compose-parity-') as temporary:
 t=Path(temporary);t.chmod(0o755)
 with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
 public='http://127.0.0.1:'+str(port);name='logai-parity-'+secrets.token_hex(4)
 cfg=yaml.safe_load((P/'compose.yaml').read_text());cfg['name']=name
 cfg['services']={k:v for k,v in cfg['services'].items() if k in ['postgres','keycloak','identity-bootstrap']}
 cfg['services']['postgres'].pop('ports')
 cfg['services']['postgres']['volumes']=['postgres-data:/var/lib/postgresql/data',str(P/'licensing/postgres')+':/usr/share/licenses/logai-platform/postgres:ro']
 cfg['services']['identity-bootstrap']['volumes']=[str(P/'identity/keycloak')+':/bootstrap/realm:ro',str(P/'identity/bootstrap-groups.json')+':/bootstrap/users.json:ro']
 cfg['services']['keycloak']['volumes']=[str(P/'identity/keycloak')+':/opt/keycloak/data/import:ro',str(P/'licensing/keycloak')+':/usr/share/licenses/logai-platform/keycloak:ro']
 (t/'compose.yaml').write_text(yaml.safe_dump(cfg))
 env=dict(line.split('=',1) for line in (P/'environments/client-local/compose.env.example').read_text().splitlines() if line and not line.startswith('#') and '=' in line)
 env.update({'KEYCLOAK_PORT':str(port),'KEYCLOAK_PUBLIC_URL':public,'POSTGRES_IMAGE_REPOSITORY':'docker.io/library/postgres','POSTGRES_PASSWORD':secrets.token_hex(24),'KEYCLOAK_ADMIN_PASSWORD':secrets.token_urlsafe(24),'KEYCLOAK_LOGAI_BOOTSTRAP_PASSWORD':secrets.token_urlsafe(24),'IDENTITY_API_IMAGE_REPOSITORY':args.identity_image.rsplit(':',1)[0],'IDENTITY_API_IMAGE_TAG':args.identity_image.rsplit(':',1)[1],'APPLICATION_PULL_POLICY':'never','KEYCLOAK_BOOTSTRAP_PASSWORD_MODE':'shared'})
 (t/'compose.env').write_text('\n'.join(k+'='+v for k,v in env.items())+'\n');(t/'compose.env').chmod(0o600)
 cmd=(['docker','compose'] if args.engine=='docker' else ['podman-compose'])+['-p',name,'--env-file',str(t/'compose.env'),'-f',str(t/'compose.yaml')]
 def run(*args,check=True):
  # Compose shell variables override --env-file; isolate generated test settings.
  process_env={k:v for k,v in os.environ.items() if k not in env}
  r=subprocess.run(cmd+list(args),capture_output=True,text=True,env=process_env)
  if check and r.returncode:
   details=r.stdout+r.stderr
   for key in ['POSTGRES_PASSWORD','KEYCLOAK_ADMIN_PASSWORD','KEYCLOAK_LOGAI_BOOTSTRAP_PASSWORD']:
    if env[key]:details=details.replace(env[key],'[redacted]')
   raise RuntimeError('Compose operation failed: '+str(args)+'\n'+details)
  return r
 try:
  run('up','-d','postgres','keycloak')
  run('run','--rm','--no-deps','identity-bootstrap')
  engine='docker' if args.engine=='docker' else 'podman'
  found=subprocess.run([engine,'ps','--filter','label=com.docker.compose.project='+name,'--filter','label=com.docker.compose.service=keycloak','--format','{{.ID}}'],capture_output=True,text=True,check=True)
  container=found.stdout.strip()
  if not container:raise RuntimeError('Disposable Compose Keycloak container not found')
  for _ in range(35):
   state=subprocess.run([engine,'inspect',container],capture_output=True,text=True,check=True)
   if json.loads(state.stdout)[0]['State'].get('Health',json.loads(state.stdout)[0]['State'].get('Healthcheck',{})).get('Status')=='healthy':break
   time.sleep(1)
  else:raise RuntimeError('Compose Keycloak healthcheck did not report healthy')
  a=adminmodule.KeycloakAdmin(public,env['KEYCLOAK_ADMIN'],env['KEYCLOAK_ADMIN_PASSWORD'])
  model=json.loads((P/'identity/bootstrap-groups.json').read_text());before={}
  for username in model:
   user=a.request('GET','realms/gamestory-sso/users?username='+username+'&exact=true')[0];before[username]=user['id']
  chris=before['chris'];beau=before['beau'];changed=secrets.token_urlsafe(24)
  a.request('PUT','realms/gamestory-sso/users/'+chris+'/reset-password',{'type':'password','value':changed,'temporary':False})
  a.request('PUT','realms/gamestory-sso/users/'+beau,{'enabled':False})
  group=next(g for g in a.request('GET','realms/gamestory-sso/groups') if g['name']=='as_lead')
  a.request('DELETE','realms/gamestory-sso/users/'+before['elvis']+'/groups/'+group['id'])
  role=a.request('GET','realms/gamestory-sso/roles/as-lead')
  a.request('DELETE','realms/gamestory-sso/groups/'+group['id']+'/role-mappings/realm',[role])
  client=a.request('GET','realms/gamestory-sso/clients?clientId=logai-ui')[0]
  a.request('PUT','realms/gamestory-sso/clients/'+client['id'],{'redirectUris':['http://wrong.invalid/callback']})
  a.request('PUT','realms/gamestory-sso',{'registrationAllowed':True})
  run('run','--rm','--no-deps','identity-bootstrap')
  for username in model:
   user=a.request('GET','realms/gamestory-sso/users?username='+username+'&exact=true')[0];assert user['id']==before[username]
   membership=a.request('GET','realms/gamestory-sso/users/'+user['id']+'/groups');assert {g['name'] for g in membership} >= set(model[username])
  assert not a.request('GET','realms/gamestory-sso/users/'+beau)['enabled']
  assert not a.request('GET','realms/gamestory-sso')['registrationAllowed']
  client=a.request('GET','realms/gamestory-sso/clients?clientId=logai-ui')[0];assert client['redirectUris']==['http://localhost:3000/auth/callback']
  roles=a.request('GET','realms/gamestory-sso/groups/'+group['id']+'/role-mappings/realm');assert any(r['name']=='as-lead' for r in roles)
  env['KEYCLOAK_LOGAI_BOOTSTRAP_PASSWORD']='';(t/'compose.env').write_text('\n'.join(k+'='+v for k,v in env.items())+'\n')
  assert run('run','--rm','--no-deps','identity-bootstrap',check=False).returncode!=0
  print('PASS: actual Compose one-shot, health wait, stable user IDs, disabled-account preservation, role/membership/client/realm drift repair, missing-secret failure')
 finally:
  run('down','-v',check=False)
