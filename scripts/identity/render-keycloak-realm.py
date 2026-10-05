#!/usr/bin/env python3
"""Render public deployment URLs into the sanitized realm; never accepts secrets."""
import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlsplit


def render(template: Path, ui_url: str, environment: str = "client-local") -> dict:
    if environment not in ('client-local','uat','prod','build','release'):
        raise ValueError('Unknown LOGAI_ENV')
    url = urlsplit(ui_url)
    if url.scheme not in ('http', 'https') or not url.hostname or url.username or url.password or url.query or url.fragment:
        raise ValueError('UI URL must be a public HTTP(S) origin, without credentials, query or fragment')
    if url.path not in ('', '/'):
        raise ValueError('UI URL must be an origin without a path')
    if url.scheme != 'https' and url.hostname not in ('localhost','127.0.0.1','::1') and not url.hostname.endswith('.localhost'):
        raise ValueError('Non-local UI origins require HTTPS')
    if environment in ('uat','prod') and (url.scheme != 'https' or not url.hostname.startswith('logai-'+environment+'.')):
        raise ValueError('UAT/prod require HTTPS and the explicit logai-<env> hostname prefix')
    origin = ui_url.rstrip('/')
    # Deliberately fail instead of silently accepting localhost for another environment.
    realm = json.loads(template.read_text())
    for client in realm['clients']:
        if client['clientId'] == 'logai-ui':
            client['redirectUris'] = [origin+'/auth/callback']
            client['webOrigins'] = [origin]
            client['attributes']['post.logout.redirect.uris'] = origin+'/'
    assert not realm.get('users') and not realm.get('identityProviders')
    return realm


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--ui-url', default=os.getenv('LOGAI_PUBLIC_URL'), required=not os.getenv('LOGAI_PUBLIC_URL'))
    parser.add_argument('--env', default=os.getenv('LOGAI_ENV','client-local'))
    parser.add_argument('--template', type=Path, default=Path(__file__).resolve().parents[2]/'identity/keycloak/gamestory-sso-realm.json')
    parser.add_argument('--output', type=Path, required=True)
    args=parser.parse_args()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(render(args.template,args.ui_url,args.env),indent=2)+'\n')
    print('Sanitized realm written; no users, passwords or upstream IdP credentials are included.')


if __name__=='__main__':main()
