#!/usr/bin/env python3
"""Exercise the client checkout layout and integrity boundaries."""
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec = importlib.util.spec_from_file_location('handover', Path(__file__).with_name('package-handover.py'))
handover = importlib.util.module_from_spec(spec)
spec.loader.exec_module(handover)
VERSION = 'v9.9.9'


def zipped(files):
    data = io.BytesIO()
    with zipfile.ZipFile(data, 'w') as z:
        for name, contents in files.items():
            entry = zipfile.ZipInfo(name)
            entry.external_attr = (0o100755 if name.endswith('.sh') else 0o100644) << 16
            z.writestr(entry, contents)
    return data.getvalue()


class LayoutTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for component, (repo, service) in handover.COMPONENTS.items():
            directory = self.root / repo
            directory.mkdir()
            metadata = 'artifact-metadata.md' if component == 'platform' else 'image-metadata.md'
            files = {
                metadata: f'- Version: {VERSION}\n',
                'sbom/component.cdx.json': json.dumps({'bomFormat': 'CycloneDX'}),
                'vulnerability-scan/trivy.sarif': '{}',
                'license-review/component-inventory.csv': 'name,version\n',
                'provenance/release-digest.md': '- Digest: sha256:' + 'a' * 64 + '\n',
                'signature/signature.txt': 'signed',
                'validation/check.txt': 'passed',
            }
            (directory / f'{service}-{VERSION}-evidence.zip').write_bytes(zipped(files))
        self.deployment_files = {
            f'schneider-logai-platform-{VERSION}/VERSION': VERSION,
            f'schneider-logai-platform-{VERSION}/README.md': 'Deployment instructions',
            f'schneider-logai-platform-{VERSION}/compose.yaml': 'services: {}',
            f'schneider-logai-platform-{VERSION}/scripts/deploy-compose.sh': '#!/bin/bash\n',
        }

    def package(self):
        directory = self.root / handover.COMPONENTS['platform'][0]
        archive = directory / f'schneider-logai-platform-{VERSION}.zip'
        archive.write_bytes(zipped(self.deployment_files))
        archive.with_suffix('.zip.sha256').write_text(handover.sha(archive.read_bytes()) + '  ' + archive.name)
        archive.with_suffix('.zip.sigstore.json').write_text('{"signature":"test"}')
        output = self.root / 'handover.zip'
        handover.package(self.root, output, VERSION)
        return output

    def test_checkout_layout_and_permissions(self):
        with zipfile.ZipFile(self.package()) as z:
            self.assertIn('compose.yaml', z.namelist())
            self.assertEqual(z.read('README.md'), b'Deployment instructions')
            self.assertIn('**/compose.env', z.read('.gitignore').decode())
            self.assertTrue(z.getinfo('scripts/deploy-compose.sh').external_attr >> 16 & 0o111)
            self.assertIn('associated_artefacts/manifest.json', z.namelist())
            for component in handover.COMPONENTS:
                self.assertIn(f'associated_artefacts/evidence/{component}/sbom/component.cdx.json', z.namelist())
            self.assertFalse(any(n.startswith('deployment/') for n in z.namelist()))

    def test_rejects_runtime_credentials(self):
        self.deployment_files[f'schneider-logai-platform-{VERSION}/environments/client-local/compose.env'] = 'PASSWORD=private'
        with self.assertRaises(AssertionError):
            self.package()

    def test_rejects_traversal(self):
        self.deployment_files[f'schneider-logai-platform-{VERSION}/../outside'] = 'invalid'
        with self.assertRaises(AssertionError):
            self.package()

    def test_rejects_corrupted_expanded_payload(self):
        archive = self.package()
        with zipfile.ZipFile(archive) as z:
            files = {name: z.read(name) for name in z.namelist()}
        files['compose.yaml'] = b'tampered'
        archive.write_bytes(zipped(files))
        with self.assertRaises(AssertionError):
            handover.verify(archive, VERSION)


if __name__ == '__main__':
    unittest.main()
