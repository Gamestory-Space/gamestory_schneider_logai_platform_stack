"""Generate the single Keycloak ERD and inventory from metadata-only catalogue JSON.

Run from repository root; optional first argument selects the evidence directory.
"""
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
catalogue = json.loads((root / 'catalogue.json').read_text())
sources = json.loads((root / 'table-sources.json').read_text())
output = root.parents[1] / 'keycloak-db.mmd'

def section(name):
    if name in {'databasechangelog', 'databasechangeloglock', 'migration_model'}:
        return 'Migration bookkeeping (Keycloak and Liquibase owned)'
    if name.startswith(('resource_', 'scope_policy', 'associated_policy', 'policy_config')):
        return 'Authorization services'
    if name.startswith(('offline_', 'revoked_', 'username_login_', 'event_', 'admin_event')):
        return 'Sessions and events'
    if name.startswith(('authentication_', 'authenticator_', 'required_action')):
        return 'Authentication flows and required actions'
    if name.startswith(('identity_provider', 'idp_', 'user_federation', 'fed_', 'federated_', 'broker_')):
        return 'Identity brokering and federation'
    if name.startswith(('client', 'default_client', 'protocol_', 'redirect_', 'web_', 'scope_mapping')):
        return 'Clients and client scopes'
    if name.startswith(('realm', 'component', 'org')):
        return 'Realms, components and organizations'
    return 'Users, groups, roles and credentials'

def mermaid_type(pg_type):
    # Mermaid attribute types cannot contain spaces; preserve PostgreSQL spelling
    # with underscores. Exact format_type spelling is in catalogue.json and notes.
    return pg_type.replace(' ', '_')

lines = ['erDiagram', '    direction TB',
         '    %% Keycloak 26.0.8 exact-image PostgreSQL 16 reference; deployed drift unverified.',
         '    %% Only declared physical FKs are edges. Dashed = non-identifying physical FK.',
         '    %% PK/UK groups and exact PostgreSQL type spelling: keycloak-db-notes.md and evidence.']
inventory = ['# Complete Keycloak reference inventory', '',
             'Generated from catalogue.json; every row is included in keycloak-db.mmd.',
             'Full columns, defaults, ordered key groups and index definitions: catalogue.json / reference-schema.sql.',
             'Historical changelog operations per entity: table-sources.json (final state comes from catalogue).', '',
             '| Section | Table | Columns | PK columns | Extra UNIQUE groups | FKs | Indexes |',
             '| --- | --- | ---: | --- | --- | ---: | ---: |']
tables = catalogue['tables']
for group in sorted({section(t['name']) for t in tables}):
    lines.append('    %% ' + group)
    for t in [t for t in tables if section(t['name']) == group]:
        cs = t['constraints']
        pk = {c for k in cs if k['kind'] == 'p' for c in k['columns']}
        fk = {c for k in cs if k['kind'] == 'f' for c in k['columns']}
        single_uk = {k['columns'][0] for k in cs if k['kind'] == 'u' and len(k['columns']) == 1}
        lines.append('    ' + t['name'] + ' {')
        for col in t['columns']:
            keys = []
            for key, members in [('PK', pk), ('FK', fk), ('UK', single_uk)]:
                if col['name'] in members:
                    keys.append(key)
            nullable = 'NULL' if col['nullable'] else 'NOT NULL'
            lines.append(f"        {mermaid_type(col['type'])} {col['name']}" +
                         (' ' + ', '.join(keys) if keys else '') + f' "{nullable}"')
        lines.append('    }')
        pk_text = ','.join(c for col in cs if col['kind'] == 'p' for c in col['columns']) or 'none'
        unique = '; '.join('(' + ','.join(k['columns']) + ')' for k in cs if k['kind'] == 'u') or 'none'
        inventory.append(f"| {group} | `{t['name']}` | {len(t['columns'])} | {pk_text} | {unique} | " +
                         f"{sum(c['kind']=='f' for c in cs)} | {len(t['indexes'])} |")
lines.append('    %% Declared physical foreign keys; labels are exact constraint names.')
for t in tables:
    pk = {c for k in t['constraints'] if k['kind'] == 'p' for c in k['columns']}
    for fk in [k for k in t['constraints'] if k['kind'] == 'f']:
        cols = set(fk['columns'])
        optional = any(c['nullable'] for c in t['columns'] if c['name'] in cols)
        unique = any(i['unique'] and i['valid'] and not i['predicate'] and not i['expressions']
                     and set(i['key_columns']).issubset(cols) for i in t['indexes'])
        parent = '|o' if optional else '||'
        child = 'o|' if unique else 'o{'
        connector = '--' if cols.issubset(pk) else '..'
        lines.append(f"    {fk['referenced_table']} {parent}{connector}{child} {t['name']} : \"{fk['name']}\"")
assert set(sources) == {t['name'] for t in tables}
output.write_text('\n'.join(lines) + '\n')
(root / 'inventory.md').write_text('\n'.join(inventory) + '\n')
print(f'Generated {output}: {len(tables)} tables, {sum(len(t["columns"]) for t in tables)} columns')
