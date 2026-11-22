# Ping + Policy Studio: UAT rollout preparation

Chris will apply client-side changes manually. Maintain the exact remote paths,
per-file edits and pending/applied statuses in [manual-remote-changes.md](manual-remote-changes.md).
The root `transfer_To_schneider.readme` is the short entry point to that list.

**Prepared, not deployed.** This package contains an additive schema plan and public
Ping configuration tools. API v0.1.9-rc.1 and UI v0.1.8-rc.1 are published, signed
release candidates from the unmerged PR heads. The UAT values pin their digests;
other environment defaults retain their stable releases. Promote the exact candidate
images to the client registry before deployment. No client database or deployment
has been changed, and no implementation PR has been merged.

## Release inputs and boundaries

1. Review/merge API PR #6 and UI PR #6 through normal owner control. The four-section
   implementation and release checks passed at API `d3f58e2847ce58e365832050ed85ebfcd665c043` and UI
   `a2ebcb067e55f92becaf8af7f6c5d23272c6880b`. No implementation is merged by this plan.
2. The published candidates and source/evidence links are in `manifest.json`. Promote
   those exact digests to the client registry and apply `release-values.yaml` last
   after Schneider's private values. Retain Identity API and Keycloak pins. Final
   stable versions can replace these candidates after owner review and merge;
   repeat source/schema/image validation for any replacement.
3. Verify the signed client archive and schema checksums. Extract `/app/db/migration` from
   the approved API image without starting it and compare the ten listed files:

   ```bash
   ./scripts/verify-policy-schema.sh /secure/extracted-api-schema
   ```

   The checked-in SQL is from the reviewed API candidate; matching the exact released
   image is mandatory. Changed SQL requires a reviewed updated manifest and rehearsal.
4. Have the client provide the actual LogAI database, schema/search_path, current
   deployment versions, DDL owner, runtime role, secret references and restored backup
   evidence. Repository placeholders and local tests are not live UAT inventory.
5. The secret for Ping stays at the client site. The agreed defaults are Basic client authentication and mandatory `openid` scope
   only. Optional profile/email scopes and mappings stay unset; POST remains an
   override if client-site testing requires it. Discovery is not client acceptance.

Policy Studio provides configuration and a versioned intelligence preference; it does
not implement Self-hosted/Enterprise AI adapters or a deterministic execution engine.
Snapshot-use flags remain disabled unless the separately governed readiness checks pass.

## A. Read-only database preflight

Use the reviewed shared PostgreSQL database and schema. Keycloak manages its
objects there through Liquibase. Preserve the existing connection options. Run as the approved migration/DDL owner, not by giving
DDL rights to the service's runtime role. Credentials stay in the client's protected
PostgreSQL service/password files; do not put a DSN/password into command arguments,
Git, Helm values or shared logs. Use a PostgreSQL client with access from the approved
operator network. Example commands are relative to this extracted rollout directory:

```bash
export PGSERVICEFILE=/secure/logai-uat.pg_service.conf
export PGSERVICE=logai-uat-migration
psql -X -v expected_database=ACTUAL_DB -v target_schema=ACTUAL_SCHEMA \
  -f preflight.psql > /secure/evidence/logai-preflight.txt
```

The report lists relations, owners, columns and constraints without warehouse rows or
credentials. Guards reject wrong database/schema, common incompatible table layouts,
LogAI tables found only in another schema, conflicting reserved policy identities,
and policy data without a backend registry.
A successful preflight is **not** a complete proof of custom-schema compatibility.
Review the report and restore/rehearse against a fresh, appropriately protected clone.
Do not automatically rename existing tables, coerce unknown columns, disable guards,
truncate data, re-import a realm or execute a down migration.

Existing S3 or PostgreSQL policy metadata, YAML/versioned objects, revisions, approvals,
audits and usage periods must be preserved. If policy history exists, retain its exact
backend/location configuration. The API deliberately refuses an unverified backend
switch. New policy writes are relational; that does not remove the need to read legacy
S3 content. Retain applicable IRSA/IAM/KMS/network access as well as its non-secret settings.

## B. Backup, quiesce and migrate

- Arrange the client maintenance window; stop/quiesce API writers and drain active
  transactions normally. Record original replicas/configuration and keep the UI in
  maintenance. Coordinate this application's GitOps/HPA controls so reconciliation
  cannot restart old writers during migration. Do not terminate database connections
  as a shortcut.
- Take the agreed database backup/snapshot, verify restoration on a clone and record
  its reference. Retain existing S3 object versions too if that backend is present.
- Run `counts.psql` before DDL, with writers stopped, and keep the output private.
  Exact counts time out rather than scanning indefinitely. Use the client's approved
  backup/dataset comparison tooling where counts alone are insufficient.
- Use the migration role and the same reviewed database and schema for Flyway.
  Set `FLYWAY_URL` to the JDBC URL and load `FLYWAY_USER` and `FLYWAY_PASSWORD`
  from the protected operator environment. Set `EXPECTED_DATABASE`,
  `FLYWAY_SCHEMA` and `BACKUP_REFERENCE` to the reviewed target and restored backup.
- Run `./scripts/migrate-policy-schema.sh` from the extracted bundle before
  deploying either application. Flyway records versions in
  `logai_flyway_schema_history` in the shared schema.
- If the shared schema already contains objects and has no Flyway history,
  rehearse explicit baselining on the restored clone. Compare the LogAI catalogue
  with a reference migrated to each candidate version. Baseline at version 0
  only if there are no LogAI objects. Otherwise record the exact highest
  fully applied version and baseline at that version only with reviewed
  evidence. Stop on partial or unknown layouts. Use the same Flyway schema
  and history table settings for baseline and migrate.

Repeat `counts.psql` immediately after DDL, before restarting the API. Compare every
pre-existing table count and the restored-clone checksums/legacy history. New tables
should be empty; no customer policy, Dictionary default or snapshot is seeded.
The local rehearsal additionally fingerprints all original columns and proves rollback
on early layout errors and a later constraint failure. It is not acceptance of the
unseen remote database.

## C. Runtime permissions and configuration

Review/apply the minimal policy grants for the existing approved runtime role:

```bash
psql -X -v expected_database=ACTUAL_DB -v target_schema=ACTUAL_SCHEMA \
  -v runtime_role=ACTUAL_RUNTIME_ROLE -f grant-runtime.psql
```

This adds policy SELECT/INSERT, column-specific updates on mutable heads/intents/
approvals/pointers/use closures, and required sequence access. It grants no table
ownership, schema CREATE, DELETE/TRUNCATE or history UPDATE, and does not revoke or
change existing base-table rights. Audit the role's inherited/existing privileges too.
If it already owns tables, this additive grant script does not remove that ownership.

Before application startup, run `runtime-check.psql` through a PostgreSQL service
entry using the **actual runtime role and connection options/search_path**, with the
same expected_database/target_schema arguments. It performs no DDL and refuses missing
policy privileges or unqualified relations resolving to a different schema. The same
check as the DDL owner would not validate runtime permissions. Retain existing core-table
rights; this plan adds only policy rights.

Use the new API/UI images together after Flyway and the runtime checks succeed. Restore the reviewed replica count after
normal deployment verification. The separate explicit admin Sample action may append
a guide revision; that must not populate the three customer slots.

Both supplied charts accept optional `logaiApi.policyConfigMap` referring to a
client-managed **non-secret** ConfigMap. Only the explicit policy storage/activation
keys are read from it. Use it to preserve an existing backend profile; do not put AWS
keys, database passwords or Ping secrets there. If no profile exists, default PostgreSQL
storage applies. Do not change these activation flags just to make a button work:
`POLICY_LIFECYCLE_ACTIVATION_ENABLED`, `POLICY_RUNTIME_TEMPLATE_VERIFIED`.
Configured policy readiness is not proof of a connected decision engine.

The supplied `applications/logai` central chart is partial. Merge the reviewed template/
value additions into the client's complete chart; do not replace that chart with this
local subset. Render/diff the complete remote chart with its private values before sync.

## D. Ping enablement — separate from database migration

Follow `docs/ping-uat-integration.md` in the extracted client bundle. Render the provider
with the client-site secret file and minimal Basic/`openid` defaults, using
`./scripts/render-ping-provider.sh`. The generated private JSON stays outside Git and
the release archive. Inspect/back up the existing `schneider-main` provider, preserve
its mappers, pass the protected backup with `--existing-provider-file`, and perform a targeted update. Keep local administrator login available;
do not enable automatic Ping redirection during the initial test. No realm-wide import.

Verify the registered broker redirect, signature validation, trusted-email setting and
assigned test user. Test Ping login, Keycloak-issued application token, approved role,
unassigned-user denial, explicit account-link behaviour and agreed logout. Successful
upstream authentication alone must not grant application administrator privileges.

## E. Acceptance and rollback

- Verify the rendered and running API/UI image digests, Flyway history, database
  connectivity, read-model endpoints and existing operational data. A basic /health
  response alone is not a database test.
- Test assigned-user Ping login and the existing local administrator route separately.
- Policy Studio: four fixed tabs, shared Dictionary, four sections, blank new customer
  slots, add/edit/version/save/reload, Must/Prefer priority and all strategy defaults.
  Inspect existing fixed-slot legacy revisions and arbitrary-ID prototype history on
  the clone; old IDs are retained but are not new paid policy products.
- A new shared Dictionary is not silently filled from old policy-local dictionaries.
  Reconcile/register legacy terms explicitly before saving new versions, resolving
  conflicting names/meanings with the customer. No legacy policy is auto-activated.
- Where an old active snapshot exists, review its generator compatibility. New v5
  bundles require complete selected revisions and normal approval/use controls; never
  rewrite old fingerprints. No decision-engine readiness is claimed here.
- Perform one approved test save/reload and verify runtime permission boundaries and
  credential rotation without interrupting existing transactions. Record resulting
  changes in the client acceptance evidence.

If Ping fails, disable only that provider or restore its reviewed prior configuration;
retain the secret's secure source because exported secrets may be masked. If application
acceptance fails, stop new policy writes and use the rehearsed application rollback
using an image compatible with the migrated schema. Keep the additive schema/history. Do not run down
scripts or blindly restore the whole database after new operational writes; database
restoration needs its own reviewed recovery window and reconciliation. Prefer a
verified forward fix when new-format policy data has already been written.

## Go/no-go record (client-owned)

Record approved API/UI digests and promotion evidence; target DB/schema and preflight;
restored backup reference; migration/count/grant results; preserved backend profile;
private-value diff; Ping default/override used and assigned test user; local admin recovery;
functional/SSO/permission acceptance; and the rehearsed rollback owner/window.
Unconfirmed items keep the rollout in preparation, not declared ready for live sync.

## Release input check

After promoting the approved API/UI images, apply their recorded digests to both
UAT value paths (and the client's complete private chart). Retain the Identity and
Keycloak pins. Render that complete chart to a protected file and run (paths are relative to the
extracted client bundle):

```bash
helm template logai /secure/complete-client-chart \
  -f /secure/current-private-values.yaml \
  -f rollouts/ping-policy-studio/release-values.yaml \
  > /secure/final-logai-render.yaml
```

```bash
./scripts/check-policy-release.sh rollouts/ping-policy-studio/manifest.json /secure/final-logai-render.yaml
```

This read-only check rejects missing/unpinned images, old API/UI references,
missing source commits, partial chart output without both image digests and
known site placeholders. Promotion may change repository names, but must preserve
the recorded digest. It does not certify registry access, database state or login.
Use an approved immutable platform release for `argocd/logai-uat.yaml`; its former
`rel2_v0.1.7` target has been replaced with an explicit required input.

API/UI release candidates come from the PR commits in the manifest. The checked-in
UAT values and shared release overlay use the published digests, for use after the controlled schema migration. They remain
prereleases; all implementation PRs remain unmerged. Platform publication retains
its existing approved-source restriction: complete owner merge/review before the
final platform release. No release-source guard is bypassed.
