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

## 21 November release follow-up (supersedes preparation-only inputs above)

- API source d3f58e2847ce58e365832050ed85ebfcd665c043: activation and template
  flags now enforced by snapshot use, capabilities and every runtime cache acquire.
  157 API cases pass locally; schema SQL is unchanged.
- UI source a2ebcb067e55f92becaf8af7f6c5d23272c6880b: 21 contracts, typecheck,
  feature lint, production build and current Playwright browser acceptance pass.
  New policy-studio CI check passed at run 44944679439.
- Eight offline asset checks pass, including Basic/openid minimal defaults, explicit
  POST/scope overrides, missing/unpinned/old image rejection and incomplete-render
  rejection. Existing Helm identity, central transfer and archive policy checks pass.
- Per the user's instruction, missing client method confirmation is replaced by the
  configurable Basic default; only mandatory openid is requested. No optional claims
  or new role mappers are populated. End-to-end acceptance remains at the client site.
- API v0.1.9-rc.1 and UI v0.1.8-rc.1 are published prereleases from those heads;
  both release pipelines passed (44944700794 / 44944703477). The manifest and both
  UAT value paths pin their real published digests. Stable latest tags are unchanged.
- Pulled the exact API digest without starting the image, extracted /app/schema,
  and verified all ten migration files against the packaged checksums.
- The shared release overlay is checked against the complete reference Helm render
  using synthetic site values; the supplied partial central chart is rejected.
  This is not a render of the unseen complete client chart. No remote DB/schema inspection or migration is claimed.
- The API/UI candidates are prereleases; implementation PRs remain unmerged. The
  platform's approved-source publication guard is retained.
