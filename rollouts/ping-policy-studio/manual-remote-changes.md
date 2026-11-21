# Manual remote changes — Ping + Policy Studio

Updated: 21 November 2026. Chris will apply client-side changes manually.
Repository preparation and passing CI do not mark remote edits complete. All items
remain pending until Chris confirms application. Further client-side changes remain
manual unless Chris explicitly changes that instruction.

The base/UAT values, chart metadata, helpers and API template were supplied earlier
and are saved in this repo. The older chart capture/screenshots are additional,
approximate evidence. The other current client templates are still needed for a
complete render. Preserve unrelated remote edits and client-owned configuration.

## Remote files

Paths beginning `applications/logai/` refer to the client's existing central chart.

| ID | Remote path/resource | Manual action | Status |
| --- | --- | --- | --- |
| R01 | `applications/logai/values.yaml` | Add the blank policy ConfigMap reference; correct old tag spelling only if present. | Pending |
| R02 | `applications/logai/values-eu-west-3-eks-shared-dev.yaml` | Update API/UI pins together; keep startup DDL and seeding false. | Pending |
| R03 | `applications/logai/templates/20-logai-api.yaml` | Add optional policy ConfigMap key mapping under container `env`. | Pending |
| V01 | `applications/logai/templates/30-logai-ui.yaml` | Verify digest support; change the image expression only if required. Current file still needed. | Pending verification |
| V02 | Existing client Argo Application/ApplicationSet; actual source path awaiting file | Verify revision, chart path and UAT value-file selection; edit only if stale. | Pending verification |
| O01 | Client-managed policy ConfigMap; actual name chosen only if needed | Preserve storage profile or supply approved snapshot-use flags. | Conditional |

### R01 — shared values

Merge under the existing `logaiApi` mapping in `applications/logai/values.yaml`:

```yaml
logaiApi:
  policyConfigMap: ""
```

Leave it blank unless a client-managed policy ConfigMap is needed. If the remote
file still contains `identity-api-v01.7` or `logai-ui-v01.7`, correct those to
`identity-api-v0.1.7` and `logai-ui-v0.1.7`. UAT's new pins belong in R02.
Retain existing credential recovery, resource, replica and security settings.

### R02 — UAT override

Manually merge into `applications/logai/values-eu-west-3-eks-shared-dev.yaml`:

```yaml
logaiApi:
  image:
    repository: global-artifacts.se.com/gsc-logai-docker-prod-fed/gamestory_logai_schneider
    tag: logai-api-v0.1.9-rc.1
    digest: sha256:306fbbca9fd5777a6f84219026ad302b2ff694ed008987744188b4f74172324e
  applyDatabaseSchemaOnStartup: false
  seedSampleDataOnStartup: false
logaiUi:
  image:
    repository: global-artifacts.se.com/gsc-logai-docker-prod-fed/gamestory_logai_schneider
    tag: logai-ui-v0.1.8-rc.1
    digest: sha256:7ef465cdc0a3250d78960caba5f5fbb8650b5ce39f85a6bcfe08d2fee6152a47
```

These are signed, published candidates from the unmerged implementation PRs.
`manifest.json` records their source/evidence. Promote both exact digests from
Docker Hub to JFrog before sync. Retain Identity v0.1.7 and Keycloak 26.0.8, plus
existing UAT hosts, namespace, gateway/Rancher settings, Secret references,
database connection/search path and credential recovery settings.

`release-values.yaml` has the same block as a copy/reference or optional final
overlay. Manual merging does not require adding that file to Argo. Keep this
ledger, the overlay and manifest together when a later image replaces a candidate.

### R03 — API template

Under the existing API container's `env` list in `20-logai-api.yaml`, add this block.
The supplied template puts it after credential-refresh entries, before `DB_HOST`:

```yaml
            {{- if .Values.logaiApi.policyConfigMap }}
            {{- $policyConfigMap := .Values.logaiApi.policyConfigMap }}
            {{- range $key := list "POLICY_STORAGE_BACKEND" "POLICY_S3_BUCKET" "POLICY_S3_REGION" "POLICY_S3_PREFIX" "POLICY_S3_KMS_KEY_ID" "POLICY_S3_EXPECTED_ACCOUNT_ID" "POLICY_S3_CREDENTIALS_SOURCE" "POLICY_S3_RETENTION_DAYS" "POLICY_LIFECYCLE_ACTIVATION_ENABLED" "POLICY_RUNTIME_TEMPLATE_VERIFIED" }}
            - name: {{ $key }}
              valueFrom:
                configMapKeyRef:
                  name: {{ $policyConfigMap }}
                  key: {{ $key }}
                  optional: true
            {{- end }}
            {{- end }}
```

Use the prepared template for indentation. Retain existing auth, database/password
file variables, Secret mounts, probes and service wiring. This ConfigMap is non-secret.

### Conditional verification

- **V01, UI:** the supplied `logai.image` helper supports digests. If the UI already
  uses it, retain the expression. If the current image expression ignores the
  digest, its equivalent using the existing helper is:

  ```yaml
  image: {{ include "logai.image" .Values.logaiUi.image }}
  ```

  Preserve existing runtime configuration and writable `/app/runtime-config` mount.
  Check the full actual template before marking this item complete.
- **V02, Argo:** retain the client's Application/ApplicationSet. Verify selection of
  `applications/logai`, `values-eu-west-3-eks-shared-dev.yaml` and the approved client
  revision. The repo's `argocd/logai-uat.yaml` references a different chart layout;
  it must not replace the existing client resource.
- **O01, policy ConfigMap:** leave the reference blank for default PostgreSQL authoring
  unless existing storage configuration requires it. Preserve a registered backend
  and any legacy S3 location/IAM/KMS access. Unknown optional settings stay absent.
  Both `POLICY_LIFECYCLE_ACTIVATION_ENABLED` and `POLICY_RUNTIME_TEMPLATE_VERIFIED`
  default false. Set both to `"true"` only after approval for snapshot use and runtime
  YAML contract verification. Roll out API pods after changing environment-backed
  configuration. These flags do not supply a decision engine or replace independent
  snapshot review.

No new edits are currently planned for `Chart.yaml`, `_helpers.tpl`, Identity API,
Keycloak, bootstrap, namespace, gateway/VirtualServices or PDB templates. Check their
current files when available and add any newly necessary edit to this list. Earlier
bootstrap and credential-recovery transfers remain separate baseline checks.
Merge individual edits; the supplied partial chart must not replace the full chart.

## Separate one-off client operations

| ID | Prepared source | Client-side action | Status |
| --- | --- | --- | --- |
| A01 | Image references in `manifest.json` | Promote both exact candidate digests to JFrog. | Pending |
| A02 | Entire `rollouts/ping-policy-studio/` directory | Extract/copy to the secured operator workspace, retaining relative `schema/` paths. | Pending |
| A03 | `scripts/client/verify-policy-schema.sh`, `check-policy-release.sh`, `render-ping-provider.sh` | Extracted bundle places these under `scripts/`; use that layout for manual transfer. | Pending |
| A04 | `identity/ping-uat.json`, `docs/ping-uat-integration.md` | Extract/copy into the same relative operator-workspace paths. | Pending |
| D01 | Rollout `.psql` scripts and schema | Apply the reviewed DB sequence with actual target DB/schema/roles and verified backup. | Pending |
| P01 | Rendered private Ping provider JSON | Perform a targeted Keycloak provider create/update for `schneider-main`. | Pending |
| V03 | `scripts/check-policy-release.sh` in extracted workspace | Check the complete client-chart render against the manifest before sync. | Pending |

**D01:** follow the rollout README for preflight, backup/clone rehearsal, writer
quiescence, before/after counts, transactional migration, runtime grants and actual
runtime-role/search-path verification. SQL order is `001 → 003 → 004 → 005 → 006 →
007 → 008 → 009 → 010 → 011`; LogAI currently uses ordered SQL, not Flyway.
Keep the existing application database/schema and Keycloak tables. Exclude seed
`002` and every down script. Keeping this ledger performs no migration.

**P01:** defaults are `client_secret_basic` and mandatory `openid` only. Optional
profile/email scopes, extra claims/mappers, PKCE and upstream logout remain unset
unless needed. POST is an override. Keep the secret and generated private JSON at
the client site. The renderer needs `--enable` to create enabled output. Preserve
existing provider options/mappers and local admin login through a targeted update;
no whole-realm import. The Ping provider itself requires no Keycloak deployment
template, image or database wiring change. Commands are in the Ping integration doc.

## Manual completion record

| ID(s) | Applied by / date | Client commit or operator evidence | Verification |
| --- | --- | --- | --- |
| — | — | Awaiting Chris's manual application updates | — |

Update statuses only when Chris reports an item applied. A repository PR or image
publication alone does not establish remote completion.
