#!/usr/bin/env python3
"""Guard the deployable LogAI identity contract using only the standard library."""
import importlib.util
import json
import re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def load(name,filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/identity'/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def main():
    template=ROOT/'identity/keycloak/gamestory-sso-realm.json'
    raw=template.read_text();realm=json.loads(raw)
    assert template.read_bytes()==(ROOT/'helm/gamestory-schneider-platform/files/gamestory-sso-realm.json').read_bytes(), 'Helm realm snapshot drift'
    assert (ROOT/'identity/bootstrap-groups.json').read_bytes()==(ROOT/'helm/gamestory-schneider-platform/files/bootstrap-groups.json').read_bytes(), 'Helm user mapping drift'
    assert not re.search(r'sample-app|sample-ui|sample\.localhost|sample-app\.localhost|Sample Relying Party|Identity Sample UI',raw)
    assert not realm.get('users') and not realm.get('identityProviders')
    def secrets(value):
        if isinstance(value,dict):
            for key,item in value.items():
                assert not (key.lower() in ('password','secret','clientsecret','privatekey','credentials') and item), 'Embedded identity credential'
                secrets(item)
        elif isinstance(value,list):
            for item in value:secrets(item)
    secrets(realm)
    assert realm['realm']=='gamestory-sso'
    clients={c['clientId']:c for c in realm['clients']}
    assert set(clients)=={'logai-ui','logai-api'}
    ui=clients['logai-ui'];assert ui['publicClient'] and ui['standardFlowEnabled']
    assert not ui.get('implicitFlowEnabled') and not ui['directAccessGrantsEnabled'] and not ui['serviceAccountsEnabled']
    assert ui['attributes']['pkce.code.challenge.method']=='S256'
    assert any(m['config'].get('included.client.audience')=='logai-api' and m['config']['access.token.claim']=='true' for m in ui['protocolMappers'])
    assert {r['name'] for r in realm['roles']['realm']}=={'logai-admin','as-lead','logai-integration'}
    assert {g['name']:g['realmRoles'] for g in realm['groups']}=={'logai_admin':['logai-admin'],'as_lead':['as-lead']}
    assert json.loads((ROOT/'identity/bootstrap-groups.json').read_text())['chris']==['logai_admin']
    renderer=load('renderer','render-keycloak-realm.py')
    for env,url in [('build','http://localhost:3000'),('release','http://localhost:3000'),('client-local','http://localhost:3000'),('uat','https://logai-uat.example.invalid'),('prod','https://logai-prod.example.invalid')]:
        rendered=renderer.render(template,url,env);client=next(c for c in rendered['clients'] if c['clientId']=='logai-ui')
        assert client['redirectUris']==[url+'/auth/callback'] and client['webOrigins']==[url]
        assert client['attributes']['post.logout.redirect.uris']==url+'/'
        assert rendered['roles']==realm['roles'] and not rendered.get('users')
    for env,url in [('uat','https://logai-prod.example.invalid'),('prod','http://localhost:3000'),('client-local','https://user:password@example.invalid'),('prod','https://logai-prod.example.invalid/path'),('uat','https://logai-uat.example.invalid?redirect=other')]:
        try:renderer.render(template,url,env)
        except ValueError:pass
        else:raise AssertionError('Unsafe or cross-environment URL accepted')
    mapping=load('bootstrap_mapping','bootstrap-keycloak-users.py')
    try:mapping.read_mapping(ROOT/'identity/bootstrap-users.example.json')
    except ValueError:pass
    else:raise AssertionError('Unassigned roles were silently defaulted')
    for filename in ['compose.yaml','environments/client-local/compose.env.example','environments/uat/identity.env.example','environments/prod/identity.env.example']:
        assert not re.search(r'sample-app|sample-ui|sample\.localhost|sample-app\.localhost',(ROOT/filename).read_text())
    print('PASS: real clients, PKCE, canonical roles, no embedded users/secrets, all environment URL generation, isolation, explicit role mapping')


if __name__=='__main__':main()
