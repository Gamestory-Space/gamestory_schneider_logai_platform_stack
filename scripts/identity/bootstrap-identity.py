#!/usr/bin/env python3
"""Operator adapter: execute the same compiled reconciler as Compose and Helm."""
import argparse
import subprocess
from pathlib import Path

def main():
    root=Path(__file__).resolve().parents[2]
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',required=True)
    parser.add_argument('--admin',default='admin')
    parser.add_argument('--admin-password-file',type=Path,required=True)
    parser.add_argument('--bootstrap-password-file',type=Path,required=True)
    parser.add_argument('--mapping',type=Path,default=root/'identity/bootstrap-groups.json')
    parser.add_argument('--realm-file',type=Path,default=root/'identity/keycloak/gamestory-sso-realm.json')
    parser.add_argument('--health-url',required=True,help='Reachable Keycloak /health/ready management URL')
    parser.add_argument('--ui-url',default='http://localhost:3000')
    parser.add_argument('--engine',choices=['docker','podman'],default='podman')
    parser.add_argument('--image',default='docker.io/chrismdgs/gamestory_logai_schneider:identity-api-v0.1.6')
    args=parser.parse_args()
    command=[args.engine,'run','--rm','--network=host','--read-only','--user=10001:10001','--cap-drop=ALL',
        '--security-opt=no-new-privileges','--tmpfs=/tmp:rw,nosuid,nodev,mode=1777',
        '-e','KEYCLOAK_BOOTSTRAP_URL='+args.url,'-e','KEYCLOAK_PUBLIC_URL='+args.url,
        '-e','KEYCLOAK_BOOTSTRAP_HEALTH_URL='+args.health_url,'-e','LOGAI_PUBLIC_URL='+args.ui_url,
        '-e','KEYCLOAK_ADMIN_USERNAME='+args.admin]
    for source,target,variable in [(args.realm_file,'/bootstrap/realm.json','KEYCLOAK_REALM_FILE'),
        (args.mapping,'/bootstrap/users.json','KEYCLOAK_USERS_FILE'),
        (args.admin_password_file,'/runtime-secrets/admin-password','KEYCLOAK_ADMIN_PASSWORD_FILE'),
        (args.bootstrap_password_file,'/runtime-secrets/user-password','KEYCLOAK_BOOTSTRAP_PASSWORD_FILE')]:
        command+=['-v',str(source.resolve())+':'+target+':ro','-e',variable+'='+target]
    command+=['--entrypoint','python',args.image,'-c','from app.bootstrap import main; main()']
    subprocess.run(command,check=True)

if __name__=='__main__':main()
