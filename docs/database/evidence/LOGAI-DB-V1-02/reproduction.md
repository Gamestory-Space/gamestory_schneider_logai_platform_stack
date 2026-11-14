# Reproduce the Keycloak reference

Run from this repository root. Requires Podman, Python 3 and access to the pinned
Keycloak image, PostgreSQL image and upstream source. All initialization writes
below are restricted to **new disposable containers**. Do not substitute a deployed
DB endpoint or mount an existing database volume. No host ports are published.
The fixture password below is public disposable test material, not a client secret.

```sh
EVIDENCE=docs/database/evidence/LOGAI-DB-V1-02
podman network create --internal logai-db-v1-02-reference
podman run -d --name logai-db-v1-02-reference-pg \
  --network logai-db-v1-02-reference \
  -e POSTGRES_DB=keycloak_reference -e POSTGRES_USER=keycloak_reference \
  -e POSTGRES_PASSWORD=disposable-reference-only postgres:16-alpine
podman exec logai-db-v1-02-reference-pg pg_isready -U keycloak_reference
# Wait for PostgreSQL readiness before starting Keycloak.
podman run -d --name logai-db-v1-02-reference-kc \
  --network logai-db-v1-02-reference \
  -e KC_DB=postgres \
  -e KC_DB_URL=jdbc:postgresql://logai-db-v1-02-reference-pg:5432/keycloak_reference \
  -e KC_DB_USERNAME=keycloak_reference -e KC_DB_PASSWORD=disposable-reference-only \
  quay.io/keycloak/keycloak:26.0.8@sha256:09a381c715ab0b111835b70f2905955274843a219c6f27efb348e4d9f4086858 start-dev
podman logs logai-db-v1-02-reference-kc
# Wait for Keycloak 26.0.8 started / migration completion before extraction.
podman exec -i logai-db-v1-02-reference-pg \
  psql -X -qAt -v ON_ERROR_STOP=1 -U keycloak_reference -d keycloak_reference \
  < "$EVIDENCE/catalogue.sql" > /tmp/keycloak-catalogue.json
podman exec logai-db-v1-02-reference-pg \
  pg_dump -U keycloak_reference -d keycloak_reference \
  --schema-only --no-owner --no-privileges --schema=public > /tmp/keycloak-schema.sql
podman cp logai-db-v1-02-reference-kc:/opt/keycloak/lib/lib/main/org.keycloak.keycloak-model-jpa-26.0.8.jar /tmp/keycloak-model-jpa.jar
```

Only pg_catalog is queried; no identity or Liquibase history rows are exported.
`pg_dump --schema-only` exports definitions only. The committed DDL removes only
pg_dump's random `\restrict` / `\unrestrict` lines, enabling stable comparison.
Compare parsed catalogue JSON rather than whitespace; the captured version is
PostgreSQL 16.15. The PostgreSQL image tag is mutable, so check the version if
repeating later. The pinned Keycloak digest is the schema-version authority.

```sh
git clone --branch 26.0.8 --depth 1 https://github.com/keycloak/keycloak.git /tmp/keycloak-source
# Expected HEAD: 9ca0ccddbf9a69d84c8d3391a86251a96ff47ca7
python3 "$EVIDENCE/verify-migrations.py" /tmp/keycloak-source /tmp/keycloak-model-jpa.jar
# Refresh catalogue.json/reference-schema.sql only after reviewing differences.
python3 "$EVIDENCE/generate-erd.py"
python3 "$EVIDENCE/validate-coverage.py" "$EVIDENCE/catalogue.json" docs/database/keycloak-db.mmd
python3 "$EVIDENCE/test-negative-probes.py"
```

For rendering, install `@mermaid-js/mermaid-cli@11.12.0` in a disposable tooling
folder (not application dependencies); this run resolved Mermaid 11.17.2,
Puppeteer 23.11.1 and Chrome 131.0.6778.204. See validation.md for this environment's
browser library setup. On a host with supported Chrome libraries:

```sh
mmdc -i docs/database/keycloak-db.mmd -o /tmp/keycloak-db.svg
```

Review the complete SVG by zooming/panning. Metadata checks are independent of
Mermaid syntax/render checks. Compare against deployed catalogues only under
separate authorized read-only access; this fixture does not establish deployed drift.

Remove only the newly created disposable fixture after capture:

```sh
podman stop logai-db-v1-02-reference-kc logai-db-v1-02-reference-pg
podman rm -v logai-db-v1-02-reference-kc logai-db-v1-02-reference-pg
podman network rm logai-db-v1-02-reference
```

For a future authorized deployed comparison, restrict the catalogue query with an
owner/source-backed table allowlist. The query intentionally captures **all** public
tables in this Keycloak-only fixture. A shared deployment also contains Logai tables;
classify ownership from migrations before comparing, rather than adding them to the
Keycloak diagram. Do not read/export records or credentials.
