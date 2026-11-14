"""Independently compare parsed ER attributes and FK edges to pg_catalog output.

Usage: python3 validate-coverage.py CATALOGUE_JSON MERMAID_FILE
This validates this documented Mermaid subset, not arbitrary Mermaid syntax.
The Mermaid CLI separately parses and renders the complete file.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

catalogue_path, diagram_path = map(Path, sys.argv[1:])
cat = json.loads(catalogue_path.read_text())
diagram = diagram_path.read_text()
entities = {}
for table, text in re.findall(r'^    (\w+) \{\n(.*?)^    \}', diagram, re.M | re.S):
    assert table not in entities, f'duplicate entity {table}'
    attrs = []
    for row in text.strip().splitlines():
        m = re.fullmatch(r'\s*(\S+) (\w+)(?: ((?:PK|FK|UK)(?:, (?:PK|FK|UK))*))? "(NULL|NOT NULL)"', row)
        assert m, row
        typ, name, key_text, null = m.groups()
        attrs.append((name, typ, frozenset(key_text.split(', ') if key_text else []), null == 'NULL'))
    entities[table] = attrs
assert set(entities) == {t['name'] for t in cat['tables']}, 'entity inventory mismatch'
expected_edges = []
for t in cat['tables']:
    constraints = t['constraints']
    primary = next((c['columns'] for c in constraints if c['kind'] == 'p'), [])
    foreign = set(col for k in constraints if k['kind'] == 'f' for col in k['columns'])
    unique = {k['columns'][0] for k in constraints if k['kind']=='u' and len(k['columns'])==1}
    expected = [(c['name'], c['type'].replace(' ', '_'),
                 frozenset(k for k, condition in [('PK', c['name'] in primary),
                   ('FK', c['name'] in foreign), ('UK', c['name'] in unique)] if condition),
                 c['nullable']) for c in t['columns']]
    assert entities[t['name']] == expected, f'attribute mismatch: {t["name"]}'
    for k in [c for c in constraints if c['kind']=='f']:
        target = next(tab for tab in cat['tables'] if tab['name'] == k['referenced_table'])
        assert all(c in [x['name'] for x in target['columns']] for c in k['referenced_columns'])
        assert len(k['columns']) == len(k['referenced_columns'])
        parent_optional = any(c['nullable'] for c in t['columns'] if c['name'] in k['columns'])
        # An unconditional simple unique index with all key attributes in the FK
        # limits a referenced parent to at most one matching child row.
        at_most_one = False
        for i in t['indexes']:
            if i['unique'] and i['valid'] and not i['predicate'] and not i['expressions']:
                if i['key_columns'] and all(c in k['columns'] for c in i['key_columns']):
                    at_most_one = True
        identifying = all(c in primary for c in k['columns'])
        expected_edges.append((target['name'], '|o' if parent_optional else '||',
                               '--' if identifying else '..', 'o|' if at_most_one else 'o{',
                               t['name'], k['name']))
actual_edges = re.findall(r'^    (\w+) (\|o|\|\|)(--|\.\.)(o\||o\{) (\w+) : "([^"]+)"$', diagram, re.M)
assert Counter(actual_edges) == Counter(expected_edges), 'FK/edge mismatch'
assert len(actual_edges) == len(re.findall(r'^    .* : ', diagram, re.M)), 'unparsed extra edge'
s = Counter(c['kind'] for t in cat['tables'] for c in t['constraints'])
print(json.dumps({'result':'PASS', 'tables':len(entities),
 'columns':sum(len(a) for a in entities.values()), 'primary_keys':s['p'],
 'unique_constraints':s['u'], 'foreign_keys':s['f'],
 'indexes':sum(len(t['indexes']) for t in cat['tables']),
 'checked':['exact entity and ordered column coverage','PostgreSQL type encoding',
 'nullability','PK/FK/single-column UK memberships','FK names and targets',
 'nullability/uniqueness cardinalities','identifying vs non-identifying physical FKs'],
 'catalogue_sha256':hashlib.sha256(catalogue_path.read_bytes()).hexdigest(),
 'diagram_sha256':hashlib.sha256(diagram_path.read_bytes()).hexdigest()},indent=2))
