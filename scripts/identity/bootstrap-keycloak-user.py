#!/usr/bin/env python3
"""Admin-only local-user creation/reset. Passwords are prompts or mounted secret files."""
import argparse
import getpass
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode, quote, urlsplit
from urllib.request import Request, urlopen


class KeycloakAdmin:
    def __init__(self, base_url, username, password):
        parsed=urlsplit(base_url)
        if not parsed.hostname or parsed.query or parsed.fragment or parsed.username or parsed.password or parsed.scheme not in ('http','https'):
            raise ValueError('Invalid Keycloak URL')
        if parsed.scheme=='http' and parsed.hostname not in ('localhost','127.0.0.1','::1') and not parsed.hostname.endswith('.localhost'):
            raise ValueError('Administrative HTTP is allowed only on local loopback URLs; use HTTPS remotely')
        self.base=base_url.rstrip('/')
        form=urlencode({'client_id':'admin-cli','grant_type':'password','username':username,'password':password}).encode()
        request=Request(self.base+'/realms/master/protocol/openid-connect/token',form,
                        {'Content-Type':'application/x-www-form-urlencoded'})
        self.token=json.loads(urlopen(request,timeout=15).read())['access_token']

    def request(self, method, path, payload=None):
        data=json.dumps(payload).encode() if payload is not None else None
        request=Request(self.base+'/admin/'+path,data,
                        {'Authorization':'Bearer '+self.token,'Content-Type':'application/json'},method=method)
        with urlopen(request,timeout=15) as response:
            raw=response.read()
            return json.loads(raw) if raw else None

    def create_or_reset(self, realm, username, password, roles, reset=False, temporary=True, **profile):
        realm_path='realms/'+quote(realm,safe='')
        users=self.request('GET',realm_path+'/users?'+urlencode({'username':username,'exact':'true'}))
        if users and not reset: raise ValueError('User already exists; pass --reset to deliberately reset that account')
        mappings=[self.request('GET',realm_path+'/roles/'+quote(role,safe='')) for role in roles]
        if not users:
            self.request('POST',realm_path+'/users',{'username':username,'enabled':True,**profile})
            users=self.request('GET',realm_path+'/users?'+urlencode({'username':username,'exact':'true'}))
        user_path=realm_path+'/users/'+quote(users[0]['id'],safe='')
        self.request('PUT',user_path+'/reset-password',{'type':'password','value':password,'temporary':temporary})
        existing_roles=self.request('GET',user_path+'/role-mappings/realm')
        previous=[role for role in existing_roles if role['name'] in ('logai-admin','as-lead')]
        if previous:self.request('DELETE',user_path+'/role-mappings/realm',previous)
        self.request('POST',user_path+'/role-mappings/realm',mappings)
        return users[0]['id']


def read_secret(file, prompt):
    value=file.read_text().rstrip('\r\n') if file else getpass.getpass(prompt)
    if not value: raise ValueError('Password cannot be empty')
    return value


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('--url',required=True)
    parser.add_argument('--realm',default='gamestory-sso')
    parser.add_argument('--admin',default='admin')
    parser.add_argument('--admin-password-file',type=Path)
    parser.add_argument('--user-password-file',type=Path)
    parser.add_argument('--role',choices=['logai-admin','as-lead'],action='append',required=True)
    parser.add_argument('--reset',action='store_true')
    parser.add_argument('--first-name')
    parser.add_argument('--last-name')
    parser.add_argument('--email')
    args=parser.parse_args()
    try:
        admin=KeycloakAdmin(args.url,args.admin,read_secret(args.admin_password_file,'Bootstrap admin password: '))
        password=read_secret(args.user_password_file,'Temporary user password: ')
        profile={k:v for k,v in [('firstName',args.first_name),('lastName',args.last_name),('email',args.email)] if v}
        admin.create_or_reset(args.realm,args.username,password,args.role,reset=args.reset,**profile)
    except HTTPError as exc:
        raise SystemExit(f'Keycloak administrative request failed (HTTP {exc.code}); response/credentials suppressed') from None
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    print('User configured. Password change is required at first login. No credential was written to output.')


if __name__=='__main__':main()
