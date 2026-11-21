"""Ensure coverage checks reject deliberate ERD corruption; no DB needed."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parent
source = (root.parents[1] / 'keycloak-db.mmd').read_text()
probes = {
    'type': source.replace('character_varying(36) id', 'integer id', 1),
    'nullability': source.replace('"NOT NULL"', '"NULL"', 1),
    'fk_marker': source.replace(' FK ', ' ', 1),
    'fk_cardinality': source.replace('||..o{', '|o..o{', 1),
    'table': source.replace('admin_event_entity {', 'missing_entity {', 1),
}
results = {}
with tempfile.TemporaryDirectory() as tmp:
    for name, mutated in probes.items():
        assert mutated != source, name
        path = Path(tmp) / 'mutated.mmd'
        path.write_text(mutated)
        result = subprocess.run([sys.executable, str(root / 'validate-coverage.py'),
                                 str(root / 'catalogue.json'), str(path)], capture_output=True)
        assert result.returncode != 0, f'validator accepted {name}'
        results[name] = 'correctly rejected'
(root / 'negative-probes.json').write_text(json.dumps(results, indent=2) + '\n')
print(json.dumps(results, indent=2))
