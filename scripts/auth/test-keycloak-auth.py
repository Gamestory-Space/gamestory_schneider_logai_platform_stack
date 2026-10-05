#!/usr/bin/env python3
"""Isolated real-Keycloak acceptance. Creates no client-site users or persistent volumes."""
import argparse
import importlib.util
import json
import os
import secrets
import socket
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen


def module(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--engine',default='docker')
    parser.add_argument('--password-mode',choices=['username','shared'],default='username')
    parser.add_argument('--identity-image',required=True)
    parser.add_argument('--api-image',required=True)
    parser.add_argument('--ui-image',required=True)
    parser.add_argument('--keycloak-image',default='quay.io/keycloak/keycloak:26.0.8@sha256:09a381c715ab0b111835b70f2905955274843a219c6f27efb348e4d9f4086858')
    parser.add_argument('--playwright-module',default='playwright')
    parser.add_argument('--evidence',type=Path,required=True)
    parser.add_argument('--platform-root',type=Path,default=Path(__file__).resolve().parents[2])
    args=parser.parse_args();args.evidence.mkdir(parents=True,exist_ok=True)
    platform=args.platform_root
    renderer=module(platform/'scripts/identity/render-keycloak-realm.py','realm_renderer')
    admin_module=module(platform/'scripts/identity/bootstrap-keycloak-user.py','realm_admin')
    prefix='logai-auth-'+secrets.token_hex(4);containers=[]
    def run(*cmd,check=True):
        result=subprocess.run([args.engine,*cmd],capture_output=True,text=True)
        if check and result.returncode:raise RuntimeError('Container operation failed: '+result.stderr)
        return result
    def port():
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
    kcport,uiport,identityport,apiport=[port() for _ in range(4)]
    kcurl=f'http://127.0.0.1:{kcport}';uiurl=f'http://127.0.0.1:{uiport}'
    identityurl=f'http://127.0.0.1:{identityport}';apiurl=f'http://127.0.0.1:{apiport}'
    admin_password=secrets.token_urlsafe(32);password=secrets.token_urlsafe(24);new_password=secrets.token_urlsafe(24);dbpassword=secrets.token_hex(24)
    network_created=False
    try:
        with tempfile.TemporaryDirectory(prefix='logai-auth-secrets-') as temporary:
            tmp=Path(temporary);tmp.chmod(0o755)
            realm=renderer.render(platform/'identity/keycloak/gamestory-sso-realm.json',uiurl)
            assert not realm.get('identityProviders') and not realm.get('users')
            import_dir=tmp/'import';import_dir.mkdir(mode=0o755)
            (import_dir/'gamestory-sso-realm.json').write_text(json.dumps(realm));(import_dir/'gamestory-sso-realm.json').chmod(0o644)
            run('network','create',prefix);network_created=True
            def start(name,image,env,port_pair=None,extra=(),command=()):
                containers.append(name)
                envfile=tmp/(name+'.env');envfile.write_text('\n'.join(k+'='+str(v) for k,v in env.items())+'\n');envfile.chmod(0o600)
                publish=['-p',port_pair] if port_pair else []
                run('run','-d','--name',name,'--network',prefix,'--env-file',str(envfile),*publish,*extra,image,*command)
            db=prefix+'-db';kc=prefix+'-keycloak'
            start(db,'docker.io/library/postgres:16-alpine',{'POSTGRES_DB':'logai','POSTGRES_USER':'logai','POSTGRES_PASSWORD':dbpassword})
            for _ in range(60):
                if run('exec',db,'pg_isready','-U','logai',check=False).returncode==0:break
                time.sleep(1)
            else:raise RuntimeError('Test database not ready')
            start(kc,args.keycloak_image,{'KC_DB':'postgres','KC_DB_URL':f'jdbc:postgresql://{db}:5432/logai','KC_DB_USERNAME':'logai','KC_DB_PASSWORD':dbpassword,'KC_BOOTSTRAP_ADMIN_USERNAME':'bootstrap-admin','KC_BOOTSTRAP_ADMIN_PASSWORD':admin_password,'KC_HOSTNAME':kcurl,'KC_HEALTH_ENABLED':'true'},
                  f'127.0.0.1:{kcport}:8080',extra=['-v',str(import_dir)+':/opt/keycloak/data/import:ro','--network-alias',kc+'.test.svc'],command=['start-dev','--import-realm'])
            for _ in range(180):
                try:
                    with urlopen(kcurl+'/realms/gamestory-sso/.well-known/openid-configuration',timeout=3) as response:
                        discovery=json.load(response)
                    assert discovery['issuer']==kcurl+'/realms/gamestory-sso';break
                except OSError:time.sleep(1)
            else:raise RuntimeError('Keycloak realm did not become ready')
            admin=admin_module.KeycloakAdmin(kcurl,'bootstrap-admin',admin_password)
            model=json.loads((platform/'identity/bootstrap-groups.json').read_text())
            config_dir=tmp/'bootstrap';config_dir.mkdir(mode=0o755)
            (config_dir/'realm.json').write_text(json.dumps(realm));(config_dir/'realm.json').chmod(0o644)
            (config_dir/'users.json').write_text(json.dumps(model));(config_dir/'users.json').chmod(0o644)
            secrets_dir=tmp/'job-secrets';secrets_dir.mkdir(mode=0o755)
            for name,value in [('username','bootstrap-admin'),('admin-password',admin_password),('user-password',password)]:
                (secrets_dir/name).write_text(value);(secrets_dir/name).chmod(0o444)
            def compiled_bootstrap():
                result=run('run','--rm','--network',prefix,'--user','10001:10001','--read-only',
                    '--cap-drop=ALL','--security-opt=no-new-privileges','--tmpfs','/tmp:rw,nosuid,nodev,mode=1777',
                    '-v',str(config_dir)+':/bootstrap:ro','-v',str(secrets_dir)+':/job-secrets:ro',
                    '-e','KEYCLOAK_BOOTSTRAP_URL=http://'+kc+'.test.svc:8080',
                    '-e','KEYCLOAK_PUBLIC_URL='+kcurl,'-e','KEYCLOAK_BOOTSTRAP_ALLOW_INTERNAL_HTTP=true',
                    '-e','KEYCLOAK_ADMIN_USERNAME_FILE=/job-secrets/username',
                    '-e','KEYCLOAK_ADMIN_PASSWORD_FILE=/job-secrets/admin-password',
                    '-e','KEYCLOAK_BOOTSTRAP_PASSWORD_MODE='+args.password_mode,
                    '-e','KEYCLOAK_BOOTSTRAP_PASSWORD_FILE=/job-secrets/user-password',
                    '--entrypoint','python',args.identity_image,'-c','from app.bootstrap import main; main()')
                return json.loads(result.stdout)
            # A completely absent disposable realm exercises creation, then safe reconciliation on reruns.
            admin.request('DELETE','realms/gamestory-sso')
            assert compiled_bootstrap()['created']==4
            assert compiled_bootstrap()['created']==0
            test_users=[]
            for username in model:
                role='logai-admin' if 'logai_admin' in model[username] else 'as-lead'
                test_users.append({'username':username,'password':('logai_'+username if args.password_mode=='username' else password),'newPassword':secrets.token_urlsafe(24),'role':role,'temporary':args.password_mode=='shared'})
            for username in model:
                user=admin.request('GET','realms/gamestory-sso/users?username='+username+'&exact=true')[0]
                membership=admin.request('GET','realms/gamestory-sso/users/'+user['id']+'/groups')
                assert {g['name'] for g in membership} >= set(model[username])
                assert ('UPDATE_PASSWORD' in user['requiredActions'])==(args.password_mode=='shared')
                assert not admin.request('GET','realms/gamestory-sso/users/'+user['id']+'/role-mappings/realm') or not any(r['name'] in ('logai-admin','as-lead') for r in admin.request('GET','realms/gamestory-sso/users/'+user['id']+'/role-mappings/realm'))
            disabled_id=admin.create_or_reset('gamestory-sso','disabled-test',password,['as-lead'])
            admin.request('PUT','realms/gamestory-sso/users/'+disabled_id,{'enabled':False})
            assert admin.request('GET','realms/gamestory-sso/identity-provider/instances')==[]
            restrictions=['--read-only','--tmpfs','/tmp:rw,nosuid,nodev,mode=1777','--cap-drop=ALL','--security-opt=no-new-privileges']
            issuer=kcurl+'/realms/gamestory-sso';jwks=f'http://{kc}:8080/realms/gamestory-sso/protocol/openid-connect/certs'
            start(prefix+'-identity',args.identity_image,{'KEYCLOAK_PUBLIC_URL':kcurl,'KEYCLOAK_ISSUER_URL':issuer,'KEYCLOAK_JWKS_FETCH_URL':jwks,'KEYCLOAK_AUDIENCE':'logai-api','API_CORS_ORIGINS':uiurl},f'127.0.0.1:{identityport}:8000',extra=['--user','10001:10001',*restrictions])
            start(prefix+'-api',args.api_image,{'AUTH_MODE':'sso','ENVIRONMENT':'test','OIDC_ISSUER_URL':issuer,'OIDC_AUDIENCE':'logai-api','OIDC_JWKS_URL':jwks,'API_CORS_ORIGINS':uiurl,'DATABASE_URL':f'postgresql://logai:{dbpassword}@{db}:5432/logai','APPLY_DATABASE_SCHEMA_ON_STARTUP':'true','SEED_SAMPLE_DATA_ON_STARTUP':'true'},f'127.0.0.1:{apiport}:8000',extra=['--user','10001:10001',*restrictions])
            config_mount='mode=1777' if args.engine=='podman' else 'uid=1000,gid=1000,mode=0700'
            start(prefix+'-ui',args.ui_image,{'AUTH_MODE':'sso','AUTH_URL':kcurl,'AUTH_REALM':'gamestory-sso','AUTH_CLIENT_ID':'logai-ui','AUTH_IDP_HINT':'','AUTH_CALLBACK_URL':uiurl+'/auth/callback','IDENTITY_API_BASE_URL':identityurl,'LOGAI_API_BASE_URL':apiurl},f'127.0.0.1:{uiport}:3000',extra=['--user','1000:1000',*restrictions,'--tmpfs','/app/runtime-config:rw,nosuid,nodev,'+config_mount])
            for base,path in [(identityurl,'/health'),(apiurl,'/health'),(uiurl,'/')]:
                for _ in range(60):
                    try:urlopen(base+path,timeout=3).close();break
                    except OSError:time.sleep(.5)
                else:raise RuntimeError('Application health did not become ready')
            config={'keycloak':kcurl,'ui':uiurl,'identity':identityurl,'api':apiurl,'users':test_users,'disabledUsername':'disabled-test','disabledPassword':password,'evidence':str(args.evidence/'browser-auth.json')}
            env={**os.environ,'LOGAI_AUTH_TEST_CONFIG':json.dumps(config),'PLAYWRIGHT_MODULE':args.playwright_module}
            result=subprocess.run(['node',str(Path(__file__).with_name('keycloak-browser-test.mjs'))],env=env,text=True,capture_output=True)
            args.evidence.joinpath('browser-test.log').write_text(result.stdout+result.stderr)
            if result.returncode:raise RuntimeError('Browser acceptance failed; see sanitized browser-test.log')
            if args.password_mode=='username':
                for user in test_users:
                    found=admin.request('GET','realms/gamestory-sso/users?username='+user['username']+'&exact=true')[0]
                    admin.request('PUT','realms/gamestory-sso/users/'+found['id']+'/reset-password',{'type':'password','value':user['newPassword'],'temporary':False})
            assert compiled_bootstrap()['created']==0
            # A second browser pass uses each private changed password, with no UPDATE_PASSWORD step.
            env['LOGAI_AUTH_TEST_CONFIG']=json.dumps({**config,'rerun':True})
            rerun=subprocess.run(['node',str(Path(__file__).with_name('keycloak-browser-test.mjs'))],env=env,text=True,capture_output=True)
            args.evidence.joinpath('browser-rerun.log').write_text(rerun.stdout+rerun.stderr)
            if rerun.returncode:raise RuntimeError('Password-preservation acceptance failed; see sanitized browser-rerun.log')
            print(result.stdout)
            print(rerun.stdout)
            metadata={image:json.loads(run('image','inspect',image).stdout)[0]['Id'] for image in [args.identity_image,args.api_image,args.ui_image,args.keycloak_image]}
            args.evidence.joinpath('tested-images.json').write_text(json.dumps(metadata,indent=2)+'\n')
    finally:
        for name in reversed(containers):
            logs=run('logs',name,check=False)
            args.evidence.joinpath(name+'.log').write_text(logs.stdout+logs.stderr)
            run('rm','-f','-v',name,check=False)
        if network_created:run('network','rm',prefix,check=False)


if __name__=='__main__':main()
