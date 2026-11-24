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
| R01 | `applications/logai/values.yaml` | Merge the shared image pins and opt-in migration settings. | Pending |
| R02 | `applications/logai/values-eu-west-3-eks-shared-dev.yaml` | Inherit the shared image pins, remove the legacy startup values and keep migration disabled. | Pending |
| R03 | `applications/logai/templates/20-logai-api.yaml` | Retain the supplied policy ConfigMap mapping and credential recovery wiring. Remove legacy startup environment entries if present. | Pending |
| R04 | `applications/logai/templates/19-logai-api-migration.yaml` | Add the Flyway PreSync Job from the archive. | Pending |
| V01 | `applications/logai/templates/30-logai-ui.yaml` | Retain the existing image helper, which honors the shared digest. | Verified against supplied template |
| V02 | Existing client Argo Application/ApplicationSet; actual source path awaiting file | Verify revision, chart path and UAT value-file selection; edit only if stale. | Pending verification |
| O01 | Client-managed policy ConfigMap; actual name chosen only if needed | Preserve storage profile or supply approved snapshot-use flags. | Conditional |

### R01 and R02 — shared and UAT values

Merge the signed bundle's `applications/logai/values.yaml` into Schneider's shared
values. It pins API rc.4, UI rc.1 and Identity v0.1.7. Keep the UAT override free
of image blocks so it inherits the shared pins. Retain the site's namespace, hosts,
gateway, resources, Secret references and database settings. The optional policy
ConfigMap stays blank unless the site has an approved policy storage profile.

The UAT override leaves `logaiApi.migration.enabled: false`. For the shared-credential
candidate, confirm the Argo application selects Schneider UAT and verify the signed
API image in JFrog before pinning it in the chart. Update the API source commit,
image reference and evidence in `manifest.json`, and use the same image pin in
`release-values.yaml` and the chart defaults when preparing the archive.

Before enabling, run the read-only UAT catalog check in
[`diagnostics/schneider-uat-db.yaml`](diagnostics/schneider-uat-db.yaml).
In Rancher, open the UAT cluster, use **Import YAML** to paste the manifest, then
open **Workloads → Pods** in `68225-logai-uat` and view the `diagnostic` container
logs. The diagnostic connects with the existing `logai-db-secret`, sets the
transaction read-only, and emits catalog and connection metadata. Delete the
diagnostic pod after collecting its logs.

Once permissions and schema are verified, set `logaiApi.migration.enabled: true`
in the UAT override. The Job defaults to `database.secretName` key `database-url`
and discovers the schema from that connection. To require dedicated credentials,
set `logaiApi.migration.secretName` to an existing Secret containing `FLYWAY_URL`,
`FLYWAY_USER` and `FLYWAY_PASSWORD`. Optionally set `logaiApi.migration.schema` to
assert the expected runtime schema. Provide `reviewedBaselineVersion` only for
reviewed first adoption without Flyway history. Use a full Argo CD application
sync and confirm the PreSync hook result before checking the API.

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

**D01:** Use the API image's bundled Flyway via the PreSync Job for the
Schneider UAT chart. Review the schema using the rollout preflight. The Job
applies versions `001 → 003 → 004 → 005 → 006 → 007 → 008 → 009 → 010 → 011`
as needed, then verifies runtime grants with the API's database credentials.
Preserve existing LogAI data and Keycloak/Liquibase objects. The bundle excludes
seed `002` and the down scripts. A reviewed standalone migration remains available
for charts that do not use the PreSync Job.

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
