# LOGAI-DB-V1-02 validation record

Discovery/capture: 2026-11-13 UTC; documentation validation: 2026-11-14 UTC.
All scope here is documentation and a disposable local reference, not a live deployment.

| Check | Result |
| --- | --- |
| Exact deployment image | 26.0.8 tag/digest agrees in release/client-local/Helm configuration; image label and startup confirm 26.0.8. |
| Upstream correspondence | 71/71 JAR migration XML resources byte-identical to upstream commit 9ca0ccddbf9a69d84c8d3391a86251a96ff47ca7. 70 reachable XML files; migration startup reported 148 executed change sets. |
| Metadata capture | PostgreSQL 16.15, fresh public schema, read-only repeatable-read catalogue transaction; schema-only pg_dump. No domain/history row export. |
| Diagram coverage | PASS: 87 tables, 499 ordered columns, 86 PKs, 18 additional UNIQUE constraints, 67 physical FKs, 195 indexes. See coverage.json. |
| Negative probes | Five intentional errors rejected: type, nullability, FK marker, FK cardinality, table name. See negative-probes.json. |
| Mermaid parsing/rendering | PASS: CLI 11.12.0, Mermaid 11.17.2, Puppeteer 23.11.1, Chrome headless shell 131.0.6778.204. Full SVG and PNG each exit 0. |
| SVG structural check | PASS: XML parses; 87 entity nodes and 67 relationship paths, all entity/column labels present; no syntax-error graphic. |
| Visual check | Native-size user_entity, realm (53 columns), resource_server_perm_ticket previews inspected: readable types, attributes, PK/UK/FK markers, nullable and NOT NULL labels. Full SVG preserves all nodes. |
| Generation determinism | Re-run generator without input changes leaves diagram/inventory hashes unchanged. |
| Whitespace | git diff --check and staged equivalent pass. |
| Live verification | Outstanding: no running local Podman deployments; Docker Desktop WSL CLI unavailable. No live credentials accessed. |

Reproduction commands: reproduction.md. SHA-256 file records immutable evidence
content; per-migration/JAR hashes are also in source-provenance.json. `NULL` in ER
attributes describes allowed SQL nullability; no records were inspected.

The fixture ran on an internal Podman network with tmpfs database storage, no host
ports, no existing volume, no imported realm and no supplied admin credentials.
Initialization was performed only by the exact Keycloak binary in this disposable
reference. It was stopped and removed with its network after metadata capture.
No target Keycloak schema/configuration/image/authentication or deployment was changed.
