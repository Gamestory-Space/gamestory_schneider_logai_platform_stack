# Keycloak PostgreSQL ERD — Logai V1

[keycloak-db.mmd](keycloak-db.mmd) is the single Keycloak ER source. It describes the
**configured Keycloak 26.0.8 fresh-install PostgreSQL reference**, derived by running
the exact pinned image's migrations in a disposable fixture. It is not a capture
of an existing client/production database. Live deployment version, migration state,
upgrade-path differences and drift remain unverified.

Task authority: merged Command [PRD](https://github.com/chrismdgamestory/gamestory-command/blob/8f3d83f/command/prds/LOGAI-DB-V1-02/PRD.md)
and [assignment](https://github.com/chrismdgamestory/gamestory-command/blob/8f3d83f/command/assignments/LOGAI-DB-V1-02/codex.md),
read from main at 8f3d83f (task merged via Command PR #28).

## Deployment ownership and version evidence

Owning repository: `Gamestory-Space/gamestory_schneider_logai_platform_stack`.
Inspected default `master` at `9f5f9123364b4914d1fb05dc8ce4846f0e33713a`.
The implementation branch adds documentation only and preserves existing local work.

| Evidence at that revision | Finding |
| --- | --- |
| [compose.yaml](https://github.com/Gamestory-Space/gamestory_schneider_logai_platform_stack/blob/9f5f9123364b4914d1fb05dc8ce4846f0e33713a/compose.yaml) | Keycloak image from version/digest variables; KC_DB=postgres; JDBC URL uses the same POSTGRES_DB and POSTGRES_USER as Logai API. No KC_DB_SCHEMA or currentSchema override. |
| [environments/release/compose.env](https://github.com/Gamestory-Space/gamestory_schneider_logai_platform_stack/blob/9f5f9123364b4914d1fb05dc8ce4846f0e33713a/environments/release/compose.env), [client-local equivalent](https://github.com/Gamestory-Space/gamestory_schneider_logai_platform_stack/blob/9f5f9123364b4914d1fb05dc8ce4846f0e33713a/environments/client-local/compose.env) | Non-secret selected fields pin quay.io/keycloak/keycloak:26.0.8, digest below; postgres:16-alpine; database/user logai. Environment files are not exported into evidence. |
| [Helm values](https://github.com/Gamestory-Space/gamestory_schneider_logai_platform_stack/blob/9f5f9123364b4914d1fb05dc8ce4846f0e33713a/helm/gamestory-schneider-platform/values.yaml) | Same Keycloak tag/digest, PostgreSQL 16, bundled database/user logai; externalDatabase can override deployment location. |
| [Helm Keycloak template](https://github.com/Gamestory-Space/gamestory_schneider_logai_platform_stack/blob/9f5f9123364b4914d1fb05dc8ce4846f0e33713a/helm/gamestory-schneider-platform/templates/keycloak.yaml) | Uses shared bundled/external database settings; no distinct Keycloak schema. Passwords are secret references and were not read. |
| [legacy docker-compose.yml](https://github.com/Gamestory-Space/gamestory_schneider_logai_platform_stack/blob/9f5f9123364b4914d1fb05dc8ce4846f0e33713a/docker-compose.yml) | Older development entry point uses mutable tag 26.0 and database fallback keycloak. It is not the authority for the pinned client/release schema. |

Exact configured image:
`quay.io/keycloak/keycloak:26.0.8@sha256:09a381c715ab0b111835b70f2905955274843a219c6f27efb348e4d9f4086858`.
Pulled amd64 image config ID:
`e447933b6a5015646c24a1b927a40202ce07adbadac839e7a1f99c463d68a224`.
Image version label and startup both report 26.0.8. No custom provider/image overlay
is introduced by compose.build.yaml for Keycloak.

V1 uses **one shared PostgreSQL schema**, with logical diagram ownership boundaries.
No db-schema setting is present in inspected deployment paths. Version-matched
[DatabaseOptions.java](https://github.com/keycloak/keycloak/blob/9ca0ccddbf9a69d84c8d3391a86251a96ff47ca7/quarkus/config-api/src/main/java/org/keycloak/config/DatabaseOptions.java)
has no db-schema default, and
[DefaultJpaConnectionProviderFactory.getSchema](https://github.com/keycloak/keycloak/blob/9ca0ccddbf9a69d84c8d3391a86251a96ff47ca7/model/jpa/src/main/java/org/keycloak/connections/jpa/DefaultJpaConnectionProviderFactory.java)
returns the configured schema. The fixture resolves to public with the default
PostgreSQL search path. This supports the configured shared-public baseline;
actual deployment search_path/role settings are not established by manifests alone.
Keycloak owns its Liquibase migrations. This ERD does not move them into Flyway,
create a schema, or imply cross-domain FKs. No Logai-owned tables are included.

## Physical authority and traceability

Upstream tag 26.0.8 resolves to
[`9ca0ccddbf9a69d84c8d3391a86251a96ff47ca7`](https://github.com/keycloak/keycloak/tree/9ca0ccddbf9a69d84c8d3391a86251a96ff47ca7).
The image's `/opt/keycloak/lib/lib/main/org.keycloak.keycloak-model-jpa-26.0.8.jar`
contains 71 migration XML resources. **All 71 match the source checkout byte-for-byte**;
[provenance manifest](evidence/LOGAI-DB-V1-02/source-provenance.json) records their
SHA-256 values, JAR hash and version refs. This prevents substituting an arbitrary
upstream version for the configured binary.

The [master changelog](https://github.com/keycloak/keycloak/blob/9ca0ccddbf9a69d84c8d3391a86251a96ff47ca7/model/jpa/src/main/resources/META-INF/jpa-changelog-master.xml)
reaches 70 XML files, including authorization changelogs, database-specific branches,
and versions through 26.0.6. Startup's Liquibase 4.29.1 summary reports 148 executed
change sets. Source XML also contains historical dropped/renamed objects and
non-PostgreSQL branches; simply collecting every createTable would be inaccurate.

The final physical authority for this reference is therefore the **post-migration
PostgreSQL catalogue**, corroborated by a schema-only pg_dump:

- [catalogue.sql](evidence/LOGAI-DB-V1-02/catalogue.sql): repeatable-read, read-only
  pg_catalog extraction; no SELECT from identity/domain tables or Liquibase rows.
- [catalogue.json](evidence/LOGAI-DB-V1-02/catalogue.json): ordered columns, exact
  format_type spelling, nullability/defaults, ordered constraints and index definitions.
- [reference-schema.sql](evidence/LOGAI-DB-V1-02/reference-schema.sql): schema-only
  DDL evidence, not an application migration or deployment script. No INSERT/COPY data.
- [table-sources.json](evidence/LOGAI-DB-V1-02/table-sources.json): each of the 85
  Keycloak domain/migration_model tables maps to historical XML operations/change-set
  IDs in the pinned source; databasechangelog/databasechangeloglock are Liquibase
  infrastructure. These mappings explain provenance, not that every historical
  operation survives in the final schema. Final per-column evidence is the catalogue/DDL.
- [inventory.md](evidence/LOGAI-DB-V1-02/inventory.md): complete 87-table checklist,
  counts, ordered PK and extra UNIQUE groups, FK and index counts per table.

Example version-sensitive facts: 26.0.0 removes user_session, user_session_note,
client_session and related legacy client-session tables. They are absent here,
not silently omitted. offline_user_session/offline_client_session remain with
composite keys. 26.0.6 adds admin_event_entity.details_json (PostgreSQL text).
Organization tables exist physically regardless of whether organization features
are used; their presence is not evidence of activation or populated records.

## Coverage and Mermaid conventions

**87 tables, 499 columns, 86 primary keys, 18 additional UNIQUE constraints,
67 foreign keys and 195 B-tree indexes** (104 unique PK/UNIQUE backing indexes and
91 nonunique indexes). No sequences, views, materialized views, user triggers,
explicit CHECK constraints or additional public-schema user types were found in
this reference. PostgreSQL creates internal FK triggers; these are constraints,
not additional user triggers. databasechangelog is the sole table without a PK.

Each diagram entity includes every catalogue column in physical order. PK implies
NOT NULL. `NULL` means the column permits NULL, not that it contains a NULL record.
Mermaid types cannot include spaces, so reversible underscores encode:

| Diagram type | PostgreSQL format_type |
| --- | --- |
| character_varying(n) | character varying(n) |
| timestamp_without_time_zone | timestamp without time zone |
| bigint, integer, smallint, boolean, bytea, text | identical spelling |

PK markers identify membership in the table's single PK, not individual uniqueness
for composite keys. UK markers appear only for single-column UNIQUE constraints;
all composite UNIQUE groups are listed in inventory.md and exact catalogue/DDL.
Defaults, index expressions and SQL constraint semantics are not invented as ER
attributes. Names retain physical lowercase spelling; constraint names preserve
catalogue case (including ORG_pkey and ORG_DOMAIN_pkey).

Every edge is one actual physical FK, labelled by its exact constraint name.
Ordered source/target columns are in catalogue.json and DDL. All 67 FKs are
single-column, validated, immediate/non-deferrable and use default NO ACTION on
update/delete. There is no implicit cascade.

- Parent endpoint is exactly one if the child FK column is NOT NULL, otherwise
  zero-or-one (14 nullable FK constraints).
- Child endpoint is zero-to-many unless an unconditional simple unique key/index
  limits the FK's source columns to at most one matching row. No minimum-one child
  is asserted merely because normal application behaviour creates children.
- Solid lines identify FKs whose source column belongs to the child PK. Dashed
  lines are **non-identifying physical FKs**, not speculative logical references.
- Join tables include associated_policy, composite_role, resource_policy,
  resource_scope, scope_policy and the realm/client/user mapping tables; none are
  collapsed into unimplemented many-to-many edges.

## Constraints/indexes and logical references

All 195 exact index definitions and 171 named PK/UNIQUE/FK constraints are retained
in catalogue.json and reference-schema.sql; the inventory groups the composite keys.
Important examples include client UNIQUE(realm_id,client_id), user_entity UNIQUE
(realm_id,username) and (realm_id,email_constraint), keycloak_group UNIQUE
(realm_id,parent_group,name), and org UNIQUE(realm_id,name), (realm_id,alias) and
(group_id). These are not individually unique realm/name columns. Nullable UNIQUE
columns retain PostgreSQL's NULL semantics. No custom SQL CHECK validates email,
JSON serialized into text, timestamps encoded in integers, or domain identifiers.

Relevant lookup indexes include idx_user_email, idx_user_service_account,
idx_client_id, idx_org_domain_org_id and offline-session user/refresh/broker indexes.
See DDL for exact columns, ordering and every remaining index; names are preserved
rather than normalized or added to the application.

Many ID-shaped attributes intentionally have no physical FK. For example:

| Fields | Evidence and interpretation |
| --- | --- |
| user_entity.realm_id, service_account_client_link | UserEntity.java named queries use realmId/clientInternalId; catalogue has no corresponding FK. |
| client.realm_id | ClientEntity.java realmId field; no realm FK in catalogue. |
| keycloak_group.parent_group, realm_id | GroupEntity.java parentId/realm strings and queries; no self/realm FK. |
| org.realm_id/group_id, org_domain.org_id | Changelog columns, uniqueness/lookup indexes; no corresponding physical FK. |
| offline_user_session and offline_client_session IDs | Composite identities/references exist as columns; no physical FKs on either table. |
| user_role_mapping.role_id, user_group_membership.group_id | Mapping columns are present, but only user_id has a physical FK on these tables. |

Entity source directory:
[model/jpa/.../entities](https://github.com/keycloak/keycloak/tree/9ca0ccddbf9a69d84c8d3391a86251a96ff47ca7/model/jpa/src/main/java/org/keycloak/models/jpa/entities).
These are application-level interpretations, not additional edges or guaranteed
cardinalities. Event/audit subject IDs likewise do not establish physical FKs.
No FK to Logai policy, business tables or external identity-provider users is inferred.

## Validation and legibility

[Validation record](evidence/LOGAI-DB-V1-02/validation.md) and
[coverage.json](evidence/LOGAI-DB-V1-02/coverage.json) record exact metadata coverage.
The independent parser checks all ordered attributes, types, nullability/key markers
and constraint-labelled endpoints/cardinalities. Five deliberate mutations are
rejected. Mermaid CLI parses/renders the entire source, and the resulting SVG has
87 entity nodes and 67 relationship paths. Detailed entity previews were visually
inspected. No entity or relation is hidden to obtain a smaller picture.

The complete graph is wide (about 30,933 × 3,953 SVG coordinate units with this
renderer). Open [the SVG](evidence/LOGAI-DB-V1-02/keycloak-db.svg) in a browser/vector
viewer, zoom and pan; a page-fit thumbnail will not make 499 attributes readable.
Logical section comments in the one source and inventory.md help locate a domain.
For print, use large-format/tiling or crop the rendered view; do not split the
maintained ERD or treat an overview crop as the complete model.

## Regeneration and remaining uncertainty

See [reproduction.md](evidence/LOGAI-DB-V1-02/reproduction.md) for exact-image fixture,
metadata-only extraction, migration-resource verification, generation and rendering.
Do not apply reference-schema.sql to a live database. Keycloak continues to own
schema creation/upgrades. Generate/validate this documentation after a reviewed
Keycloak version change; never flatten historical XML createTable operations alone.

Live PostgreSQL access was unavailable: no running Podman containers were present,
and Docker Desktop's WSL CLI was not integrated. No live credentials were sought.
The only writes were Keycloak's normal initialization in a newly created disposable
fixture, with no mounted existing data, no host port and an internal network. No
realms/users were imported, no bootstrap admin credentials supplied, and only
catalogue/schema metadata was exported. No target DB/config/auth/deployment changed.
The fixture was removed after capture.

The mutable legacy development tag/config and possible external Helm overrides
remain explicit differences. Actual deployed image, privileges/ownership, search_path,
extensions, additional provider tables, feature/schema drift and historical upgrade
artifacts require a later authorized catalogue comparison. No claim is made that
an upgraded/extended client database is byte-identical to this pristine reference.
