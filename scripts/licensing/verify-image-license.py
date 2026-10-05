#!/usr/bin/env python3
"""Require declared application licence/notice bytes in the final image filesystem."""
import argparse
import hashlib
import io
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path,PurePosixPath

PREFIX='licenses/'
FILES={'LICENSE':PREFIX+'GAMESTORY-LICENSE.txt','NOTICE':PREFIX+'THIRD_PARTY_NOTICES.txt'}
LABELS={'org.opencontainers.image.vendor':'Gamestory Ltd','org.opencontainers.image.licenses':'LicenseRef-Gamestory-Proprietary',
 'com.gamestory.license.scope':'application-code-only',
 'com.gamestory.license.file':'/'+FILES['LICENSE'],
 'com.gamestory.license.notice':'/'+FILES['NOTICE']}

def inspect_archive(archive, expected):
    if set(expected)!={'LICENSE','NOTICE'} or any(not value.strip() for value in expected.values()):
        raise ValueError('Nonempty canonical licence and notice inputs are required')
    files={}
    with tarfile.open(archive) as outer:
        manifest=json.load(outer.extractfile('manifest.json'))
        if len(manifest)!=1:raise ValueError('Expected one image')
        config=json.load(outer.extractfile(manifest[0]['Config']))
        labels=config['config'].get('Labels') or {}
        for key,value in LABELS.items():
            if labels.get(key)!=value:raise ValueError('Missing/incorrect application licence metadata: '+key)
        for layer_name in manifest[0]['Layers']:
            with tarfile.open(fileobj=outer.extractfile(layer_name),mode='r|*') as layer:
                for member in layer:
                    path=PurePosixPath(member.name.lstrip('/'));name=str(path)
                    if path.name=='.wh..wh..opq':
                        parent='' if str(path.parent)=='.' else str(path.parent).rstrip('/')+'/'
                        files={key:value for key,value in files.items() if not key.startswith(parent)}
                    elif path.name.startswith('.wh.'):
                        target=str(path.parent/path.name[4:])
                        files={key:value for key,value in files.items() if key!=target and not key.startswith(target+'/')}
                    elif name in FILES.values():
                        files.pop(name,None)
                        if member.isfile():files[name]=layer.extractfile(member).read()
    for name,value in expected.items():
        if files.get(FILES[name])!=value:raise ValueError('Missing or mismatched final application '+name+' file')
    return {'status':'passed','license':'LicenseRef-Gamestory-Proprietary','scope':'application-code-only',
            'legalApproval':'separate publication gate',
            'files':{name:{'path':'/'+FILES[name],'sha256':hashlib.sha256(value).hexdigest()} for name,value in expected.items()}}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('image');parser.add_argument('evidence',type=Path)
    parser.add_argument('--license-file',type=Path,required=True);parser.add_argument('--notice-file',type=Path,required=True);parser.add_argument('--engine',default='docker');args=parser.parse_args()
    try:expected={'LICENSE':args.license_file.read_bytes(),'NOTICE':args.notice_file.read_bytes()}
    except OSError:raise SystemExit('Canonical licence/notice build inputs are missing; do not publish this image') from None
    with tempfile.TemporaryDirectory(prefix='logai-license-') as tmp:
        archive=Path(tmp)/'image.tar'
        subprocess.run([args.engine,'save','-o',str(archive),args.image],check=True,capture_output=True)
        result=inspect_archive(archive,expected)
    args.evidence.mkdir(parents=True,exist_ok=True)
    (args.evidence/'LICENSE').write_bytes(expected['LICENSE'])
    (args.evidence/'THIRD_PARTY_NOTICES').write_bytes(expected['NOTICE'])
    (args.evidence/'image-license.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
