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
import stat

REGISTRY = 'docker.io/chrismdgs/gamestory_logai_schneider'
COMPONENTS = {
    'identity-api': ('gamestory-identity-kit', 'gamestory-sso-api'),
    'logai-api': ('gamestory-logai-api', 'gamestory-logai-api'),
    'logai-ui': ('logai_ui', 'logai-ui'),
    'platform': ('gamestory_schneider_logai_platform_stack', 'gamestory-schneider-logai-platform'),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def entries(data):
    """Read ordinary files without accepting traversal, links or duplicate paths."""
    result = {}
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for entry in z.infolist():
            path = Path(entry.filename)
            assert not path.is_absolute() and '..' not in path.parts and '\\' not in entry.filename
            assert not stat.S_ISLNK(entry.external_attr >> 16), 'Archive contains a symbolic link'
            if entry.is_dir():
                continue
            assert entry.filename not in result, 'Duplicate archive entry'
            result[entry.filename] = (z.read(entry), entry.external_attr)
    return result


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
        modern = 'associated_artefacts/manifest.json' in z.namelist()
        manifest_name = 'associated_artefacts/manifest.json' if modern else 'manifest.json'
        manifest = json.loads(z.read(manifest_name))
        assert manifest['version'] == version
        assert set(manifest['components']) == set(COMPONENTS)
        assert set(z.namelist()) == set(manifest['files']) | {manifest_name}
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
            if modern:
                for name, (data, _) in entries(z.read(item['evidence'])).items():
                    assert z.read(f'associated_artefacts/evidence/{component}/{name}') == data
        deployment = f'{"associated_artefacts" if modern else "deployment"}/schneider-logai-platform-{version}.zip'
        assert z.read(deployment + '.sha256').decode().split()[0] == sha(z.read(deployment))
        with zipfile.ZipFile(io.BytesIO(z.read(deployment))) as deployment_zip:
            assert deployment_zip.read(f'schneider-logai-platform-{version}/VERSION').decode().strip() == version
        if modern:
            prefix = f'schneider-logai-platform-{version}/'
            for name, (data, _) in entries(z.read(deployment)).items():
                assert name.startswith(prefix)
                assert z.read(name[len(prefix):]) == data, 'Deployment payload mismatch'
        assert json.loads(z.read(deployment + '.sigstore.json')), 'Missing deployment signature'
    print('Verified handover checksums, version, four evidence packs and artifact digests')


def package(inputs, output, version):
    files = {}
    modes = {}
    components = {}
    for component, (repo, service) in COMPONENTS.items():
        filename = f'{service}-{version}-evidence.zip'
        data = (inputs / repo / filename).read_bytes()
        name = f'associated_artefacts/evidence/{filename}'
        files[name] = data
        components[component] = {'reference': f'{REGISTRY}:{component}-{version}',
                                 'digest': evidence(data, version), 'evidence': name}
        for member, (contents, mode) in entries(data).items():
            destination = f'associated_artefacts/evidence/{component}/{member}'
            files[destination] = contents
            modes[destination] = mode
    platform = inputs / COMPONENTS['platform'][0]
    for suffix in ('', '.sha256', '.sigstore.json'):
        filename = f'schneider-logai-platform-{version}.zip{suffix}'
        files[f'associated_artefacts/{filename}'] = (platform / filename).read_bytes()
    prefix = f'schneider-logai-platform-{version}/'
    deployment_data = files[f'associated_artefacts/schneider-logai-platform-{version}.zip']
    for member, (contents, mode) in entries(deployment_data).items():
        assert member.startswith(prefix), 'Unexpected deployment root'
        destination = member[len(prefix):]
        assert destination and not destination.startswith('associated_artefacts/')
        path = Path(destination)
        assert not any(part in {'.git', '.github', '.env', 'compose.env'} for part in path.parts), 'Private deployment material'
        assert destination not in files, 'Deployment path collision'
        files[destination] = contents
        modes[destination] = mode
    files['associated_artefacts/README.md'] = (
        f'# Schneider LogAI {version} handover\n\n'
        'Deployment files are extracted at the project root; follow its README.md.\n'
        'associated_artefacts/ contains the original signed deployment ZIP, checksum and signature.\n'
        'Its evidence/ folder contains original and expanded identity, API, UI and platform evidence packs.\n'
        'Each pack includes its CycloneDX SBOM, scan, component inventory, validation,\n'
        'signature and provenance. manifest.json records SHA-256 checksums and OCI digests.\n\n'
        'These files can be checked into the client Git repository. Keep the private runtime compose.env ignored.\n'
    ).encode()
    files['.gitignore'] = (
        '# Private runtime settings and generated attachment metadata.\n'
        '**/compose.env\n.env\n.env.*\n*.secret.yaml\n*.secret.yml\n*:Zone.Identifier\n'
    ).encode()
    manifest = {'schemaVersion': 2, 'version': version, 'components': components,
                'files': {name: sha(data) for name, data in files.items()}}
    files['associated_artefacts/manifest.json'] = (json.dumps(manifest, indent=2) + '\n').encode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            entry = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = modes.get(name) or ((stat.S_IFREG | 0o644) << 16)
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
