# LogAI v0.1.6: UAT and production deployment

Send this runbook with the approved platform release, its image digest manifest, and the site's reviewed Helm overrides. Images must be published or mirrored before the client can deploy. The current local implementation does not publish images or apply anything to a client cluster.

## 1. Prepare the release and site configuration

Publish or mirror the approved LogAI API, identity API and UI images into the registry accessible from Schneider's clusters. Record immutable digests and set each component's `image.repository` and `image.digest`. Include the approved Keycloak and PostgreSQL image references where applicable. Commit the platform chart and environment values into the repository Argo CD will read, and create the referenced `v0.1.6` release tag only after validation.

For UAT, start with `environments/uat/values.yaml`; for production use `environments/prod/values.yaml`. Supply the real database host, database name and database user, registry pull Secret if required, ingress class, and `identity.domain`. The default `example.invalid` is a deliberately non-live placeholder and must be replaced before login acceptance. With a domain of `customer.example`, the derived UAT origins are:

- `https://logai-uat.customer.example`
- `https://api-uat.customer.example`
- `https://identity-uat.customer.example`
- `https://keycloak-uat.customer.example`

Production uses the same prefixes with `prod`. Individual `identity.publicUiUrl`, `identity.logaiApiUrl`, `identity.identityApiUrl` and `identity.publicUrl` overrides support different host conventions. Arrange DNS and TLS for all four origins. Set `ingress.tls` to the site's TLS Secret and matching real hostnames; update the production example host list when changing the domain. Supply UAT TLS configuration as well.

## 2. Prepare each cluster namespace and Secrets

Create the target namespace before syncing; the supplied Argo Applications have `CreateNamespace=false`. Provision these Secrets through the client's Secret manager or securely from local files, never by committing credentials into Git:

| Environment | Secret | Required keys |
| --- | --- | --- |
| UAT | `schneider-managed-uat-database` | `password`, `databaseUrl` |
| UAT | `schneider-managed-uat-keycloak-admin` | `username`, `password` |
| UAT | `schneider-managed-uat-bootstrap-users` | `password` |
| Production | `schneider-managed-prod-database` | `password`, `databaseUrl` |
| Production | `schneider-managed-prod-keycloak-admin` | `username`, `password` |
| Production | `schneider-managed-prod-bootstrap-users` | `password` |

`databaseUrl` is the complete application PostgreSQL connection URL, including the site's TLS settings. The chart uses the separately supplied database password and connection settings for Keycloak. Confirm the database user can create the required application and Keycloak tables. Keep UAT and production databases and Secrets separate.

The bootstrap-users password is the approved temporary initial password supplied at runtime. New users must change it on first login. Existing users retain their password and account state on subsequent syncs. The Keycloak administrator password is a separate credential.

For a fresh application database, temporarily set `logaiApi.applyDatabaseSchemaOnStartup: true` and `logaiApi.replicas: 1` for the first sync. After schema initialization and API checks succeed, set schema-on-startup back to `false` and restore the intended replica count. Leave `logaiApi.seedSampleDataOnStartup: false` in production; sample seeding is also off by default in UAT. Real operational data requires its own approved import/integration procedure.

## 3. Deploy UAT through Argo CD

Fill in every placeholder in `argocd/logai-uat.yaml`: repository URL, Argo project, registered cluster name and namespace. Confirm `targetRevision` exists and includes the reviewed UAT values. Apply the Application in the Argo CD namespace:

```bash
kubectl apply -f argocd/logai-uat.yaml
argocd app sync logai-uat
argocd app wait logai-uat --sync --health --operation --timeout 900
```

Use a full Application sync: selective resource sync does not run hooks. The Helm chart owns the post-install/post-upgrade identity Job; Argo CD maps that same Job to PostSync, with no separate hook in the Application. Standalone Helm executes the same chart hook directly. All paths use the compiled Identity API reconciler. It creates/reconciles the realm, clients, roles, groups and user memberships after the services become healthy. No manual Keycloak user entry is required. Successful hook Jobs are deleted; check the Argo operation result for success. Failed Jobs remain available temporarily for diagnosis.

```bash
kubectl -n <LOGAI_UAT_NAMESPACE> get deployments,pods,jobs,ingress
kubectl -n <LOGAI_UAT_NAMESPACE> get events --sort-by=.lastTimestamp
```

Inspect a failed Job's logs with `kubectl -n <namespace> logs job/<job-name>`. Fix missing Secrets, registry access, database connectivity, DNS/TLS or configuration, then run another full sync.

## 4. Accept UAT

Confirm all pods are ready, HTTPS origins work, the API health/readiness checks pass, and application reads succeed against the intended database. Login must use realm `gamestory-sso`.

Verify Chris is in `logai_admin` with `logai-admin`; Elvis, Beau and Sunil are in `as_lead` with `as-lead`. Test first-login password change, a normal LogAI business operation, and logout. Chris should pass the admin identity endpoint; AS leads should receive 403 on that admin-only endpoint while retaining normal business access. Confirm an unauthenticated request is rejected. Run another full sync and verify changed passwords still work and memberships remain present.

Record image digests, chart revision, configuration revision and acceptance evidence. Complete the first-sync schema flag cleanup before approving promotion.

## 5. Promote to production

Use the exact application image digests accepted in UAT. Review the production URLs, TLS, database, namespace, Secret references and replica counts independently. Confirm database backup/recovery arrangements and approve any schema change before rollout.

Fill in `argocd/logai-prod.yaml`, then deploy:

```bash
kubectl apply -f argocd/logai-prod.yaml
argocd app sync logai-prod
argocd app wait logai-prod --sync --health --operation --timeout 900
```

Repeat the UAT acceptance checks against production. The same users, roles and groups are initialized in each environment; passwords and databases are independent. Configure the Schneider external identity provider separately when its real issuer, client credentials and claim mappings are supplied. Native realm users can be used for initial acceptance.

## 6. Recovery and handover

For a failed rollout, retain the failed operation/log evidence and revert Git to the previously approved chart/configuration/image digests, then sync. Application rollback does not automatically undo database migrations or reset Keycloak user passwords. Use the site's approved database recovery procedure if required.

Hand over the release digest manifest, reviewed site values, Argo Application definitions, Secret names and ownership, DNS/TLS details, UAT acceptance evidence, production verification and recovery contacts. Never include plaintext passwords in the handover bundle.

Local Helm rendering and disposable-container acceptance validate the implementation. Client EKS networking, ingress, Secrets integration and an actual Argo CD sync must still be verified at the site.

The release also includes [image licensing documentation](image-licensing.md). Application images must pass the canonical proprietary licence/notice gate, and Gamestory must approve the exact licence text before publication. Keycloak remains Apache-2.0; PostgreSQL remains under the PostgreSQL License and its official container scripts under MIT. Their notices are shipped and mounted separately, preserving upstream image digests.
