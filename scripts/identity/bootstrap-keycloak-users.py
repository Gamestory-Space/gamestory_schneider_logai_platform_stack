#!/usr/bin/env python3
"""Provision the four canonical users with an explicit, non-secret role mapping."""
import argparse
import importlib.util
import json
from pathlib import Path

USERS={'elvis':'Elvis','beau':'Beau','sunil':'Sunil','chris':'Chris'}
ROLES={'logai-admin','as-lead'}


def read_mapping(path):
    mapping=json.loads(path.read_text())
    if not isinstance(mapping,dict) or set(mapping)!=set(USERS):
        raise ValueError('Mapping must contain exactly elvis, beau, sunil and chris')
    for username,roles in mapping.items():
        if not isinstance(roles,list) or not roles or any(role not in ROLES for role in roles) or len(roles)!=len(set(roles)):
            raise ValueError('Each user requires an explicit, unique list of logai-admin/as-lead roles')
    return mapping


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--mapping',type=Path,required=True)
    parser.add_argument('--url',required=True)
    parser.add_argument('--admin',default='admin')
    parser.add_argument('--admin-password-file',type=Path)
    parser.add_argument('--password-directory',type=Path,help='Mounted secret directory containing one file per username; otherwise prompts')
    parser.add_argument('--reset',action='store_true')
    args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('bootstrap_admin',Path(__file__).with_name('bootstrap-keycloak-user.py'))
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    try:
        mapping=read_mapping(args.mapping)
        admin=mod.KeycloakAdmin(args.url,args.admin,mod.read_secret(args.admin_password_file,'Bootstrap admin password: '))
        # Check all users before any mutation; existing accounts require an explicit reset.
        for username in USERS:
            existing=admin.request('GET','realms/gamestory-sso/users?username='+username+'&exact=true')
            if existing and not args.reset:raise ValueError('Existing bootstrap users require --reset')
        passwords={username:mod.read_secret(args.password_directory/username if args.password_directory else None,username+' temporary password: ') for username in USERS}
        for username,name in USERS.items():
            admin.create_or_reset('gamestory-sso',username,passwords[username],mapping[username],reset=args.reset,firstName=name)
    except mod.HTTPError as exc:
        raise SystemExit(f'Keycloak administrative request failed (HTTP {exc.code}); credentials suppressed') from None
    except (ValueError,OSError) as exc:
        raise SystemExit(str(exc)) from None
    print('Configured four users; temporary passwords require first-login changes. No credential was logged.')


if __name__=='__main__':main()
