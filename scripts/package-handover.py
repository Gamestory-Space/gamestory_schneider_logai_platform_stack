#!/usr/bin/env python3
"""Assemble or verify a handover from already published release attachments."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile

REGISTRY = 'docker.io/chrismdgs/gamestory_logai_schneider'
COMPONENTS = {
    'identity-api': ('gamestory-identity-kit', 'gamestory-sso-api'),
    'logai-api': ('gamestory-logai-api', 'gamestory-logai-api'),
    'logai-ui': ('logai_ui', 'logai-ui'),
    'platform': ('gamestory_schneider_logai_platform_stack', 'gamestory-schneider-logai-platform'),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def evidence(data, version):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        for required in ('sbom/', 'vulnerability-scan/trivy.sarif',
                         'license-review/component-inventory.csv',
                         'provenance/release-digest.md', 'signature/', 'validation/'):
            assert any(n.startswith(required) and not n.endswith('/') for n in names), required
        metadata = 'image-metadata.md' if 'image-metadata.md' in names else 'artifact-metadata.md'
        assert f'- Version: {version}\n' in z.read(metadata).decode(), 'Evidence version mismatch'
        text = z.read('provenance/release-digest.md').decode()
        match = re.search(r'^- (?:OCI digest|Digest): (sha256:[0-9a-f]{64})$', text, re.M)
        assert match, 'Missing released artifact digest'
        sboms = [n for n in names if n.startswith('sbom/') and n.endswith('.json')]
        assert sboms and all(json.loads(z.read(n)).get('bomFormat') == 'CycloneDX' for n in sboms)
        return match[1]


def verify(archive, version, registry=False):
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist()) == len(set(z.namelist())), 'Duplicate ZIP entries'
        manifest = json.loads(z.read('manifest.json'))
        assert manifest['version'] == version
        assert set(manifest['components']) == set(COMPONENTS)
        assert set(z.namelist()) == set(manifest['files']) | {'manifest.json'}
        for name, digest in manifest['files'].items():
            assert not name.startswith('/') and '..' not in Path(name).parts
            assert sha(z.read(name)) == digest, f'Checksum mismatch: {name}'
        for component, item in manifest['components'].items():
            assert item['reference'] == f'{REGISTRY}:{component}-{version}'
            assert evidence(z.read(item['evidence']), version) == item['digest']
            if registry:
                descriptor = json.loads(subprocess.check_output(
                    ['oras', 'manifest', 'fetch', '--descriptor', item['reference']], text=True))
                assert descriptor['digest'] == item['digest'], f'Registry digest mismatch: {component}'
        deployment = f'deployment/schneider-logai-platform-{version}.zip'
        assert z.read(deployment + '.sha256').decode().split()[0] == sha(z.read(deployment))
        with zipfile.ZipFile(io.BytesIO(z.read(deployment))) as deployment_zip:
            assert deployment_zip.read(f'schneider-logai-platform-{version}/VERSION').decode().strip() == version
        assert json.loads(z.read(deployment + '.sigstore.json')), 'Missing deployment signature'
    print('Verified handover checksums, version, four evidence packs and artifact digests')


def package(inputs, output, version):
    files = {}
    components = {}
    for component, (repo, service) in COMPONENTS.items():
        filename = f'{service}-{version}-evidence.zip'
        data = (inputs / repo / filename).read_bytes()
        name = f'evidence/{filename}'
        files[name] = data
        components[component] = {'reference': f'{REGISTRY}:{component}-{version}',
                                 'digest': evidence(data, version), 'evidence': name}
    platform = inputs / COMPONENTS['platform'][0]
    for suffix in ('', '.sha256', '.sigstore.json'):
        filename = f'schneider-logai-platform-{version}.zip{suffix}'
        files[f'deployment/{filename}'] = (platform / filename).read_bytes()
    files['README.md'] = (
        f'# Schneider LogAI {version} handover\n\n'
        'deployment/ contains the original signed deployment ZIP, checksum and signature.\n'
        'evidence/ contains the identity, API, UI and platform release evidence packs.\n'
        'Each pack includes its CycloneDX SBOM, scan, component inventory, validation,\n'
        'signature and provenance. manifest.json records SHA-256 checksums and OCI digests.\n\n'
        'Unzip the deployment ZIP separately and follow its README.md for deployment.\n'
    ).encode()
    manifest = {'version': version, 'components': components,
                'files': {name: sha(data) for name, data in files.items()}}
    files['manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(entry, data)
    verify(output, version)
    output.with_suffix('.zip.sha256').write_text(f'{sha(output.read_bytes())}  {output.name}\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('version')
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--registry', action='store_true')
    args = parser.parse_args()
    assert re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+(?:[.-][A-Za-z0-9.-]+)?', args.version)
    if args.inputs:
        package(args.inputs, args.archive, args.version)
    else:
        verify(args.archive, args.version, args.registry)
