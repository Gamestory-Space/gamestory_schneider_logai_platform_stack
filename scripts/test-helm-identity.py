#!/usr/bin/env python3
"""Validate hook lifecycle, public URLs, secret mounts and runtime restrictions."""
import argparse
import json
import subprocess
from pathlib import Path
import yaml

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--helm',default='helm');args=parser.parse_args()
chart=ROOT/'helm/gamestory-schneider-platform'


def render(env,settings=()):
    result=subprocess.run([args.helm,'template','logai',str(chart),'--namespace','logai-'+env,'-f',str(ROOT/'environments'/env/'values.yaml'),*settings],capture_output=True,text=True,check=True)
    return list(yaml.safe_load_all(result.stdout))


for env in ['build','release','client-local','dev-aws','uat','prod']:
    resources=render(env)
    admin_secret=next(r for r in resources if r and r['kind']=='Secret')
    assert admin_secret['stringData']=={'username':'admin','password':'chris'}
    config=next(r['data'] for r in resources if r and r['kind']=='ConfigMap' and r['metadata']['name'].endswith('-config'))
    assert config['AUTH_MODE']=='sso' and config['AUTH_CLIENT_ID']=='logai-ui' and config['OIDC_AUDIENCE']=='logai-api'
    assert 'sample-' not in json.dumps(resources)
    licences=next(r['data'] for r in resources if r and r['kind']=='ConfigMap' and r['metadata']['name'].endswith('-upstream-licenses'))
    for upstream,filename,key in [('keycloak','LICENSE','keycloak-LICENSE'),('keycloak','NOTICE','keycloak-NOTICE'),('postgres','LICENSE','postgres-LICENSE'),('postgres','CONTAINER-LICENSE','postgres-CONTAINER-LICENSE'),('postgres','NOTICE','postgres-NOTICE')]:
        assert licences[key]==(ROOT/'licensing'/upstream/filename).read_text(), 'Upstream licence snapshot drift'
    for upstream in ['keycloak','postgres']:
        workloads=[r for r in resources if r and r['kind'] in ('Deployment','StatefulSet') and r['metadata']['name'].endswith('-'+upstream)]
        for workload in workloads:
            pod=workload['spec']['template']['spec'];container=pod['containers'][0]
            mount=next(m for m in container['volumeMounts'] if m['name']=='upstream-licenses')
            assert mount['readOnly'] and mount['mountPath']=='/usr/share/licenses/logai-platform/'+upstream
            assert any(v['name']=='upstream-licenses' and 'configMap' in v for v in pod['volumes'])

    if env in ['uat','prod']:
        assert config['AUTH_CALLBACK_URL']=='https://logai-'+env+'.example.invalid/auth/callback'
        assert config['KEYCLOAK_ISSUER_URL']=='https://keycloak-'+env+'.example.invalid/realms/gamestory-sso'
    job=next(r for r in resources if r and r['kind']=='Job')
    annotations=job['metadata']['annotations'];assert annotations['helm.sh/hook']=='post-install,post-upgrade'
    assert annotations['helm.sh/hook-delete-policy']=='before-hook-creation,hook-succeeded'
    pod=job['spec']['template']['spec'];assert pod['automountServiceAccountToken'] is False
    assert pod['securityContext']['runAsUser']==10001
    container=pod['containers'][0];assert container['securityContext']['readOnlyRootFilesystem']
    assert container['command']==['python','-c','from app.bootstrap import main; main()']
    assert sum('secret' in volume for volume in pod['volumes'])==1
    assert next(item['value'] for item in container['env'] if item['name']=='KEYCLOAK_BOOTSTRAP_PASSWORD_MODE')=='username'
    data=next(r['data'] for r in resources if r and r['kind']=='ConfigMap' and r['metadata']['name'].endswith('-identity-bootstrap'))
    realm=json.loads(data['realm.json']);users=json.loads(data['users.json'])
    ui=next(c for c in realm['clients'] if c['clientId']=='logai-ui')
    assert ui['redirectUris']==[config['AUTH_CALLBACK_URL']]
    assert ui['webOrigins']==[config['API_CORS_ORIGINS']]
    assert users==json.loads((ROOT/'identity/bootstrap-groups.json').read_text())
    assert not realm.get('users') and not realm.get('identityProviders')
    assert {g['name']:g['realmRoles'] for g in realm['groups']}=={'logai_admin':['logai-admin'],'as_lead':['as-lead']}
    for deployment in [r for r in resources if r and r['kind']=='Deployment' and r['metadata']['name'].endswith(('-identity-api','-logai-api','-logai-ui'))]:
        pod=deployment['spec']['template']['spec'];container=pod['containers'][0]
        assert container['securityContext']['readOnlyRootFilesystem'] and pod['automountServiceAccountToken'] is False
        expected=1000 if deployment['metadata']['name'].endswith('-logai-ui') else 10001
        assert pod['securityContext']['runAsUser']==expected
        if expected==1000:assert not any('secretKeyRef' in item.get('valueFrom',{}) for item in container.get('env',[]))
custom=render('uat',['--set','identity.domain=customer.example'])
config=next(r['data'] for r in custom if r and r['kind']=='ConfigMap' and r['metadata']['name'].endswith('-config'))
assert config['AUTH_CALLBACK_URL']=='https://logai-uat.customer.example/auth/callback'
assert config['KEYCLOAK_PUBLIC_URL']=='https://keycloak-uat.customer.example'
argo=render('uat',['--set','identityBootstrap.hookMode=argo'])
job=next(r for r in argo if r and r['kind']=='Job');assert job['metadata']['annotations']['argocd.argoproj.io/hook']=='PostSync'
for setting in ['identity.authMode=none','identity.publicUiUrl=http://localhost:3000','identity.publicUiUrl=https://bad.example/path','identityBootstrap.passwordMode=invalid','identityBootstrap.hookMode=invalid']:
    result=subprocess.run([args.helm,'template','logai',str(chart),'-f',str(ROOT/'environments/uat/values.yaml'),'--set',setting],capture_output=True,text=True)
    assert result.returncode!=0,'Unsafe/incomplete values rendered successfully'
shared=render('uat',['--set','identityBootstrap.passwordMode=shared','--set','keycloak.existingAdminSecret=external-admin'])
assert not any(r and r['kind']=='Secret' for r in shared)
job=next(r for r in shared if r and r['kind']=='Job')
assert sum('secret' in v for v in job['spec']['template']['spec']['volumes'])==2
print('PASS: six environments, Helm/Argo hooks, domain override, canonical realm/groups/users, secret references, read-only UIDs and invalid-value rejection')
