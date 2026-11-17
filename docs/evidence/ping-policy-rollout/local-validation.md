# Ping + Policy Studio rollout preparation — local evidence

Scope: local preparation only; no UAT/production connection, DDL, secret import,
provider enablement, implementation merge, image release/promotion or deployment.

- Reviewed API source/schema: dde5d6b86050a359d30690c94ba7d45b706b6b41.
- UI source: cfd4ff294d21793e0afc0c7a6f46a43715b20eea.
- Ten SQL files match the API candidate; manifest enumerates 25 policy tables.
- Twelve PostgreSQL 17 rehearsal cases pass; five offline asset checks pass.
- PostgreSQL rehearsal runs only in policy_rollout_test using isolated temporary schemas.
- Covers populated operational/unrelated rows, existing PostgreSQL policy history,
  S3 metadata without object access, normalized schema-4 task/intelligence data,
  repeat application, incompatible schema/table/Keycloak/reserved-identity targets, missing backup
  reference, missing backend registry, late-constraint rollback and runtime grants.
- Backend grant test exercises storage registration, shared Dictionary inserts and
  sequences as the unprivileged runtime role, without granting DDL/history mutation.
  A runtime-connection check fails when a required INSERT grant is absent.
- Five offline asset checks cover private credential rendering for Basic/POST,
  disabled-by-default output, explicit enable flag, no-clobber/0600, no secret output,
  existing-provider option preservation, schema tamper/extra-SQL rejection, opt-in
  policy ConfigMap wiring and startup DDL/seeding remaining off.
- Existing Helm identity and Schneider transfer tests pass. Shell syntax checks pass.
- Final archive policy tests verify rollout assets, portable checksum filenames,
  internal/application-source exclusions and generated private-file rejection.
- No image pins were changed. On-site database inventory and backup/restore rehearsal,
  new release image digests/promotion and confirmed Ping client method remain prerequisites.
