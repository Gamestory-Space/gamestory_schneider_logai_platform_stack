# LOGAI-DB-V1-02 validation

Executed 2026-11-14 against deployment source master
`9f5f9123364b4914d1fb05dc8ce4846f0e33713a` and Keycloak upstream
`9ca0ccddbf9a69d84c8d3391a86251a96ff47ca7` (26.0.8).

## Schema and provenance

- Re-initialized the exact configured image digest in a new disposable PostgreSQL
  16.15 fixture, internal network, no host ports or existing data mounts.
- Image config ID `e447933b6a5015646c24a1b927a40202ce07adbadac839e7a1f99c463d68a224`,
  amd64, image version label 26.0.8. Startup reported Keycloak 26.0.8 and 148 run /
  zero previously run / 148 total change sets. No realm/user import or admin login.
- Re-extracted catalogue JSON compared equal as parsed JSON to catalogue.json;
  schema-only pg_dump compared byte-for-byte after removing its random restrict
  lines. Migration JAR compared byte-for-byte to the recorded source JAR.
- `verify-migrations.py` PASS: all 71 image changelog XML resources byte-identical
  to pinned upstream; 70 reachable via master includes. Table source mapping covers
  all 85 domain/migration_model tables plus two Liquibase bookkeeping tables.
- No existing client database was accessed. This is version-matched reference
  verification; actual deployment/search_path/upgrade drift remains outstanding.

## Diagram coverage

```sh
EVIDENCE=docs/database/evidence/LOGAI-DB-V1-02
python3 "$EVIDENCE/generate-erd.py"
python3 "$EVIDENCE/validate-coverage.py" "$EVIDENCE/catalogue.json" docs/database/keycloak-db.mmd
python3 "$EVIDENCE/test-negative-probes.py"
```

PASS: 87 tables / 499 columns / 86 PKs / 18 extra UNIQUE constraints / 67 FKs /
195 indexes. coverage.json records input hashes and checked properties. Five
corruptions (type, nullability, FK marker, FK cardinality, table inventory) rejected.
The generator and validator use separate parsing paths. The validator checks
physical ordered attributes and foreign-key edge multisets against catalogue JSON.
Regeneration preserves the diagram bytes and inventory deterministically.

## Mermaid rendering and visual review

Mermaid CLI 11.12.0; resolved Mermaid 11.17.2, Puppeteer 23.11.1,
Chrome headless shell 131.0.6778.204; Node 24.20.0.

```sh
# Existing temporary tooling outside repository; not an application dependency.
# puppeteer config contains {"args":["--no-sandbox"]} for this isolated browser run.
LD_LIBRARY_PATH=/tmp/logai-erd-libs/extracted/usr/lib/x86_64-linux-gnu \
/tmp/logai-erd-tools/node_modules/.bin/mmdc \
  -i docs/database/keycloak-db.mmd \
  -o docs/database/evidence/LOGAI-DB-V1-02/keycloak-db.svg \
  -p /tmp/logai-erd-puppeteer.json
```

PASS, exit 0. Browser inspection of rendered SVG: **87 `g.node` entities and
67 `path.relationshipLine` edges**. The large full graph is intentionally retained;
user_entity, realm and resource_server_perm_ticket detail screenshots were visually
inspected for readable types, key markers and nullability. SVG XML parses normally.

Initial rendering failed because this minimal WSL host lacks libnss3.so; rerun
with temporary extracted libnss3/libnspr4/libasound2t64 libraries succeeded. No system
package, application dependency or deployment configuration was modified. On a host
with supported browser libraries ordinary `mmdc` works; use reproduction.md.

`git diff --check` PASS. Exactly one `.mmd` added. No runtime/schema/configuration
files changed; runtime suites are unrelated to these documentation artifacts.
