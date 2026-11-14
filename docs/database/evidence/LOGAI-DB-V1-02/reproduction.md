# Reproduce the Keycloak reference ERD

Use a disposable local fixture only. These commands initialize an empty temporary
PostgreSQL store; they must not be pointed at an existing deployment/database.
No host ports or existing volumes are mounted. Only metadata is exported.
Do not provide real credentials or import any realm/user data.

Run from this repository root with Podman, Git, Python 3 and Node available.
Pinned PostgreSQL image corresponds to the captured PostgreSQL 16.15 amd64 image.
The Keycloak image is the exact configured release digest, not a mutable tag.

```sh
podman pull quay.io/keycloak/keycloak:26.0.8@sha256:09a381c715ab0b111835b70f2905955274843a219c6f27efb348e4d9f4086858
podman pull docker.io/library/postgres@sha256:1a66d744c1b459e13b05a8fca341da84cb63383e99ce262210efee5a319d4551
podman network create --internal logai-db-v1-02-reference
podman run -d --name logai-db-v1-02-postgres \
  --network logai-db-v1-02-reference --tmpfs /var/lib/postgresql/data \
  -e POSTGRES_DB=logai_reference -e POSTGRES_USER=erd_reference \
  -e POSTGRES_HOST_AUTH_METHOD=trust \
  docker.io/library/postgres@sha256:1a66d744c1b459e13b05a8fca341da84cb63383e99ce262210efee5a319d4551
podman exec logai-db-v1-02-postgres pg_isready -U erd_reference -d logai_reference
```

Wait for pg_isready success before starting Keycloak. Fixture-only trust auth is
confined to its internal network; no password is exported to Git or terminal.

```sh
podman run -d --name logai-db-v1-02-keycloak \
  --network logai-db-v1-02-reference \
  -e KC_DB=postgres \
  -e KC_DB_URL=jdbc:postgresql://logai-db-v1-02-postgres:5432/logai_reference \
  -e KC_DB_USERNAME=erd_reference \
  quay.io/keycloak/keycloak@sha256:09a381c715ab0b111835b70f2905955274843a219c6f27efb348e4d9f4086858 \
  start-dev --http-enabled=true
podman logs --tail 30 logai-db-v1-02-keycloak
```

Wait for `Keycloak 26.0.8 ... started`; reference initialization reported 148 executed
Liquibase change sets. No bootstrap admin configuration or realm import is supplied.
No logs containing domain data need to be committed. Then extract only metadata:

```sh
podman exec -i logai-db-v1-02-postgres \
  psql -X -qAt -v ON_ERROR_STOP=1 -U erd_reference -d logai_reference \
  < docs/database/evidence/LOGAI-DB-V1-02/catalogue.sql \
  > docs/database/evidence/LOGAI-DB-V1-02/catalogue.json
podman exec logai-db-v1-02-postgres \
  pg_dump -U erd_reference -d logai_reference --schema-only --no-owner \
  --no-privileges --schema=public > /tmp/logai-keycloak-reference-ddl.sql
podman cp logai-db-v1-02-keycloak:/opt/keycloak/lib/lib/main/org.keycloak.keycloak-model-jpa-26.0.8.jar \
  /tmp/logai-keycloak-model-jpa-26.0.8.jar
git clone --depth 1 --branch 26.0.8 https://github.com/keycloak/keycloak.git \
  /tmp/logai-keycloak-26.0.8-source
python3 docs/database/evidence/LOGAI-DB-V1-02/verify-migrations.py \
  /tmp/logai-keycloak-26.0.8-source /tmp/logai-keycloak-model-jpa-26.0.8.jar
```

For deterministic committed DDL, remove only pg_dump's random psql restriction
wrapper, leaving every SQL statement intact (the 16.15 tool emits these wrappers):

```sh
python3 - <<'PY'
from pathlib import Path
source = Path('/tmp/logai-keycloak-reference-ddl.sql').read_text()
lines = [line for line in source.splitlines()
         if not line.startswith(('\\restrict ', '\\unrestrict '))]
Path('docs/database/evidence/LOGAI-DB-V1-02/reference-schema.sql').write_text(
    '\n'.join(lines) + '\n')
PY
python3 docs/database/evidence/LOGAI-DB-V1-02/generate-erd.py
python3 docs/database/evidence/LOGAI-DB-V1-02/validate-coverage.py \
  docs/database/evidence/LOGAI-DB-V1-02/catalogue.json \
  docs/database/keycloak-db.mmd
```

Regeneration must not leave tables without provenance: verify-migrations.py requires
all non-Liquibase tables to match a reachable migration operation. It also checks
the exact upstream commit and compares all 71 image XML resources byte-for-byte.
The final state is determined from PostgreSQL metadata, including effects of drops,
renames, custom changes and PostgreSQL type conversion, not only XML CREATE entries.

Render the one source with Mermaid CLI (the captured CLI resolved Mermaid 11.17.2).
For exact reproduction use that resolved Mermaid version as well; Mermaid layout
can change independently of schema content. Keep this installation outside the repo:

```sh
npm install --prefix /tmp/logai-erd-tools @mermaid-js/mermaid-cli@11.12.0 mermaid@11.17.2
/tmp/logai-erd-tools/node_modules/.bin/mmdc \
  -i docs/database/keycloak-db.mmd \
  -o docs/database/evidence/LOGAI-DB-V1-02/keycloak-db.svg -b white
```

The recorded environment needed a Puppeteer config
`{"args":["--no-sandbox"]}` at `/tmp/logai-erd-puppeteer.json` and `-p` with that
path. Browser shared libraries were already extracted in /tmp from the earlier
policy-ERD task; it used this successful invocation:

```sh
LD_LIBRARY_PATH=/tmp/logai-erd-libs/extracted/usr/lib/x86_64-linux-gnu \
/tmp/logai-erd-tools/node_modules/.bin/mmdc \
  -p /tmp/logai-erd-puppeteer.json \
  -i docs/database/keycloak-db.mmd \
  -o docs/database/evidence/LOGAI-DB-V1-02/keycloak-db.svg -b white
```

Use a normal sandboxed browser installation where supported. Inspect the full SVG
at readable zoom; confirm 87 entity nodes and 67 FK relationship paths. Re-run
coverage after any source/diagram change. No runtime test suite is required to
validate this documentation-only change; repository PR checks still apply.

Clean up only the disposable resources created above (do not remove others):

```sh
podman stop logai-db-v1-02-keycloak logai-db-v1-02-postgres
podman rm logai-db-v1-02-keycloak logai-db-v1-02-postgres
podman network rm logai-db-v1-02-reference
```

For a future explicitly authorized deployed comparison, use a dedicated read-only
connection and an owner-backed table allowlist in catalogue.sql: its public-schema
query intentionally inventories **all** fixture tables. A shared deployment also
contains Logai tables, which must be separated using migration/source ownership,
not blindly added to the Keycloak ERD. Do not export records, passwords, tokens,
connection strings or role credentials. Live verification remains outstanding here.
