# LogAI v0.1.6 — Schneider UAT and production deployment configuration

Please configure the following site-specific values before deploying LogAI through Argo CD. Gamestory supplies the approved platform deployment bundle, Helm chart, application image references/digests and release evidence. Schneider supplies the target infrastructure, Git/Argo access, DNS/TLS, database connectivity and runtime Secrets.

Use `environments/uat/values.yaml` for UAT and `environments/prod/values.yaml` for production. Keep environment-specific changes in the corresponding reviewed values file, or add a site override file as the last entry in the Application's `spec.source.helm.valueFiles` list. Do not edit generated manifests or store plaintext credentials in Git.

The `example.invalid` domains and angle-bracket placeholders are intentionally non-live examples and must be replaced. Application image availability must be confirmed before sync; a tag in the supplied values file does not itself establish that the image has been published.

## Configuration file reference

All paths below are relative to the platform project root. Line numbers identify the current supplied files and may move when site overrides are added. Add environment-specific overrides to the UAT/production values file; chart-default references identify inherited keys, not a requirement to edit shared chart defaults.

<table>
<thead><tr><th>Area</th><th>Schneider must supply/configure</th><th>File</th><th>Line</th></tr></thead>
<tbody>
<tr><td rowspan="2">Argo CD</td><td rowspan="2">Git repository, approved revision, Argo project, cluster and namespace</td><td><code>argocd/logai-uat.yaml</code></td><td>7 (project), 9 (repository), 10 (revision), 11 (chart), 13 (values), 16 (cluster), 17 (namespace)</td></tr>
<tr><td><code>argocd/logai-prod.yaml</code></td><td>7 (project), 9 (repository), 10 (revision), 11 (chart), 13 (values), 16 (cluster), 17 (namespace)</td></tr>
<tr><td rowspan="3">URLs and DNS</td><td rowspan="3">Real DNS suffix or explicit HTTPS origins</td><td><code>environments/uat/values.yaml</code></td><td>55 (domain)</td></tr>
<tr><td><code>environments/prod/values.yaml</code></td><td>73 (domain)</td></tr>
<tr><td><code>helm/gamestory-schneider-platform/values.yaml</code></td><td>89 (Keycloak), 90 (UI), 91 (LogAI API), 92 (Identity API): optional origin definitions</td></tr>
<tr><td rowspan="3">Ingress/TLS</td><td rowspan="3">Controller class, annotations, certificates and matching hostnames</td><td><code>environments/uat/values.yaml</code></td><td>65 (class), 66 (hosts)</td></tr>
<tr><td><code>environments/prod/values.yaml</code></td><td>76 (class), 77 (TLS), 78 (TLS Secret), 80 (TLS hosts), 84 (route hosts)</td></tr>
<tr><td><code>helm/gamestory-schneider-platform/values.yaml</code></td><td>101 (annotations), 102 (TLS): inherited definitions</td></tr>
<tr><td rowspan="2">Application images</td><td rowspan="2">Registry repositories and immutable digests; Identity API, LogAI API, UI respectively</td><td><code>environments/uat/values.yaml</code></td><td>8, 20, 32 (repositories); 10, 22, 34 (digests)</td></tr>
<tr><td><code>environments/prod/values.yaml</code></td><td>9, 22, 35 (repositories); 11, 24, 37 (digests)</td></tr>
<tr><td rowspan="2">Registry authentication</td><td rowspan="2">Names of pull-credential Secrets</td><td><code>environments/uat/values.yaml</code></td><td>5</td></tr>
<tr><td><code>environments/prod/values.yaml</code></td><td>5</td></tr>
<tr><td rowspan="2">Database</td><td rowspan="2">Endpoint, port, database, username, TLS mode and Secret reference</td><td><code>environments/uat/values.yaml</code></td><td>46 (host), 47 (port), 48 (database), 49 (username), 50 (Secret), 51 (URL key), 52 (TLS mode)</td></tr>
<tr><td><code>environments/prod/values.yaml</code></td><td>64 (host), 65 (port), 66 (database), 67 (username), 68 (Secret), 69 (URL key), 70 (TLS mode)</td></tr>
<tr><td rowspan="2">Keycloak admin Secret</td><td rowspan="2">Reference to administrator credentials</td><td><code>environments/uat/values.yaml</code></td><td>57</td></tr>
<tr><td><code>environments/prod/values.yaml</code></td><td>47</td></tr>
<tr><td rowspan="2">Bootstrap-user Secret</td><td rowspan="2">Reference to the temporary initial-user password</td><td><code>environments/uat/values.yaml</code></td><td>74</td></tr>
<tr><td><code>environments/prod/values.yaml</code></td><td>92</td></tr>
<tr><td rowspan="3">Initial schema step</td><td rowspan="3">One-time schema initialization flag and one API replica</td><td><code>environments/uat/values.yaml</code></td><td>18: add logaiApi overrides</td></tr>
<tr><td><code>environments/prod/values.yaml</code></td><td>19: add logaiApi overrides</td></tr>
<tr><td><code>helm/gamestory-schneider-platform/values.yaml</code></td><td>18 (replicas), 26 (schema), 27 (sample seeding): inherited definitions</td></tr>
<tr><td rowspan="2">Production promotion</td><td rowspan="2">Exact application digests accepted in UAT and approved chart/config revision</td><td><code>environments/prod/values.yaml</code></td><td>11, 24, 37 (digests)</td></tr>
<tr><td><code>argocd/logai-prod.yaml</code></td><td>10 (revision)</td></tr>
</tbody>
</table>

Secret values, DNS records, ingress-controller installation and database provisioning are external infrastructure inputs; they do not have credential-value lines in the platform repository.

## 1. Argo CD Application settings

Update `argocd/logai-uat.yaml` and `argocd/logai-prod.yaml`:

<table>
<thead><tr><th>Field</th><th>Required site value</th><th>File</th><th>Line</th></tr></thead>
<tbody>
<tr><td rowspan="2">metadata.namespace</td><td rowspan="2">Argo CD control-plane namespace; default is argocd</td><td><code>argocd/logai-uat.yaml</code></td><td>5</td></tr>
<tr><td><code>argocd/logai-prod.yaml</code></td><td>5</td></tr>
<tr><td rowspan="2">spec.project</td><td rowspan="2">Schneider Argo project allowed to deploy LogAI</td><td><code>argocd/logai-uat.yaml</code></td><td>7</td></tr>
<tr><td><code>argocd/logai-prod.yaml</code></td><td>7</td></tr>
<tr><td rowspan="2">spec.source.repoURL</td><td rowspan="2">Schneider-accessible Git repository containing the approved chart and values</td><td><code>argocd/logai-uat.yaml</code></td><td>9</td></tr>
<tr><td><code>argocd/logai-prod.yaml</code></td><td>9</td></tr>
<tr><td rowspan="2">spec.source.targetRevision</td><td rowspan="2">Approved immutable release tag or commit; supplied v0.1.6 must exist in the repository</td><td><code>argocd/logai-uat.yaml</code></td><td>10</td></tr>
<tr><td><code>argocd/logai-prod.yaml</code></td><td>10</td></tr>
<tr><td rowspan="2">spec.source.path</td><td rowspan="2">Chart directory; default helm/gamestory-schneider-platform</td><td><code>argocd/logai-uat.yaml</code></td><td>11</td></tr>
<tr><td><code>argocd/logai-prod.yaml</code></td><td>11</td></tr>
<tr><td rowspan="2">spec.source.helm.valueFiles</td><td rowspan="2">Environment values plus approved site overrides</td><td><code>argocd/logai-uat.yaml</code></td><td>13</td></tr>
<tr><td><code>argocd/logai-prod.yaml</code></td><td>13</td></tr>
<tr><td rowspan="2">spec.destination.name</td><td rowspan="2">Target environment cluster name registered in Argo CD</td><td><code>argocd/logai-uat.yaml</code></td><td>16</td></tr>
<tr><td><code>argocd/logai-prod.yaml</code></td><td>16</td></tr>
<tr><td rowspan="2">spec.destination.namespace</td><td rowspan="2">LogAI namespace for that environment</td><td><code>argocd/logai-uat.yaml</code></td><td>17</td></tr>
<tr><td><code>argocd/logai-prod.yaml</code></td><td>17</td></tr>
</tbody>
</table>

The supplied Applications use `CreateNamespace=false`: provision both target namespaces before sync. Ensure the Argo project and repository/cluster credentials permit these destinations and resources. Sync is operator-controlled by default; the supplied Applications do not enable automated sync. Use a full Application sync so lifecycle hooks run.

## 2. Public URLs, DNS and ingress

Set `identity.domain` to the real approved DNS suffix. The chart derives these origins:

| Service | UAT | Production |
| --- | --- | --- |
| LogAI UI | `https://logai-uat.<domain>` | `https://logai-prod.<domain>` |
| LogAI API | `https://api-uat.<domain>` | `https://api-prod.<domain>` |
| Identity API | `https://identity-uat.<domain>` | `https://identity-prod.<domain>` |
| Keycloak | `https://keycloak-uat.<domain>` | `https://keycloak-prod.<domain>` |

If Schneider uses a different naming convention, set complete HTTPS origins in `identity.publicUiUrl`, `identity.logaiApiUrl`, `identity.identityApiUrl` and `identity.publicUrl` (Keycloak). Origins must contain no path, query, credentials or trailing application route. The chart generates the callback, allowed UI origin and public token issuer from these values.

Replace/configure:

- `ingress.className`: the installed ingress controller class, unless the cluster has the intended default class.
- `ingress.annotations`: any controller-specific load balancer, certificate, exposure or routing settings required by Schneider.
- `ingress.tls`: the real TLS configuration. For Kubernetes Secret-based TLS, provision the referenced certificate Secret in the LogAI namespace and list all relevant real hostnames. Production currently references `schneider-managed-prod-tls` with placeholder hosts; replace those hosts. UAT currently has no explicit TLS block and also requires HTTPS termination configuration. For controller-managed certificates, use Schneider's approved controller configuration instead of assuming a Kubernetes TLS Secret is sufficient.
- `ingress.hosts.*`: normally leave blank to derive hosts from the public origins. If explicitly set, they must match those origins.

Provision DNS records pointing all four origins to the ingress endpoint. Confirm browser/client reachability, certificate trust, and API access from the UI. The chart defines the UI/API/identity/Keycloak Ingress routes and Services; it does not install an ingress controller, create DNS records or issue certificates. Preserve Keycloak's production `start` command and ensure forwarded HTTPS headers match `keycloak.proxyHeaders: xforwarded`.

## 3. Image registry and immutable release references

For `logaiApi.image`, `identityApi.image` and `logaiUi.image`, set:

- `repository`: the approved accessible registry/repository, or Schneider's mirrored repository.
- `digest`: the published `sha256:...` manifest digest supplied in the approved release manifest. A nonempty digest takes precedence over `tag`.
- `tag`: retain the approved component version for traceability; supplied values use `logai-api-v0.1.6`, `identity-api-v0.1.6`, and `logai-ui-v0.1.6`.

If authentication is required, provision registry pull credentials and set `global.imagePullSecrets` to their Secret names. Confirm registry access from cluster nodes/pods. Production must use the same application digests accepted in UAT. The bootstrap Job uses the identity API image, so mirroring that image also covers bootstrap.

Keycloak is supplied with a pinned upstream image. If it must be mirrored, update `keycloak.image.repository` and its mirrored manifest digest while retaining the approved software version. UAT/production have `postgres.enabled: false`: the chart uses an external database and does not deploy the bundled PostgreSQL container.

## 4. Database configuration

Replace the placeholder `externalDatabase.host` (`uat-postgres.example.invalid` / `prod-postgres.example.invalid`). Confirm/set `externalDatabase.port`, `externalDatabase.database`, `externalDatabase.username` and `externalDatabase.sslMode`. The supplied TLS mode is `require`; apply Schneider's approved certificate/verification requirements.

Provide the database Secret described below. Its `databaseUrl` must point to the same database/user as these settings and include the application's required TLS options. In the current chart, the LogAI API and Keycloak both use this configured PostgreSQL database and user. Ensure that arrangement is approved and the user has the permissions needed for their tables. A requirement for separate Keycloak and LogAI database connections needs additional chart configuration work; it is not an existing setting.

Provision separate UAT and production databases/credentials, connectivity from the workload namespaces, backups and recovery procedures. For a fresh LogAI database, perform the agreed initial schema step: temporarily set `logaiApi.applyDatabaseSchemaOnStartup: true` and `logaiApi.replicas: 1`; after successful initialization and checks, restore the flag to `false` and the intended replica count. Keycloak initializes its own schema. Keep `logaiApi.seedSampleDataOnStartup: false` in production; real data onboarding is a separate integration/import activity.

## 5. Runtime Secrets

Provision these Secrets in the corresponding LogAI namespace before sync, through Schneider's approved Secret-management process:

<table>
<thead><tr><th>Purpose</th><th>Required keys</th><th>File</th><th>Line</th><th>Configured Secret</th></tr></thead>
<tbody>
<tr><td rowspan="2">Database</td><td rowspan="2">password, databaseUrl</td><td><code>environments/uat/values.yaml</code></td><td>50</td><td><code>schneider-managed-uat-database</code></td></tr>
<tr><td><code>environments/prod/values.yaml</code></td><td>68</td><td><code>schneider-managed-prod-database</code></td></tr>
<tr><td rowspan="2">Keycloak administration</td><td rowspan="2">username, password</td><td><code>environments/uat/values.yaml</code></td><td>57</td><td><code>schneider-managed-uat-keycloak-admin</code></td></tr>
<tr><td><code>environments/prod/values.yaml</code></td><td>47</td><td><code>schneider-managed-prod-keycloak-admin</code></td></tr>
<tr><td rowspan="2">Initial bootstrap-user password</td><td rowspan="2">password</td><td><code>environments/uat/values.yaml</code></td><td>74</td><td><code>schneider-managed-uat-bootstrap-users</code></td></tr>
<tr><td><code>environments/prod/values.yaml</code></td><td>92</td><td><code>schneider-managed-prod-bootstrap-users</code></td></tr>
</tbody>
</table>

If names differ, update `externalDatabase.existingSecret`, `keycloak.existingAdminSecret` and `identityBootstrap.existingSecret`. Key names can also be configured through their corresponding `passwordKey`, `databaseUrlKey`, `adminUserKey` and `adminPasswordKey` values.

The administrator must be an active authorized Keycloak account for recurring reconciliation. On a fresh database the admin Secret initializes that account; changing the Secret later does not automatically reset an existing administrator's password. Coordinate credential rotation with the existing account.

The bootstrap-user password is the agreed temporary initial password, supplied securely at runtime. It is distinct from the administrator/database credentials. New users must change it on first login. Subsequent reconciliation preserves changed passwords, enabled/disabled state and existing account actions. No passwords belong in Helm values, Git, image labels, browser configuration or the client handover document.

## 6. Configuration supplied by the chart

Retain these application settings unless Gamestory approves a contract change:

- Realm: `gamestory-sso`; browser client: `logai-ui`; API audience: `logai-api`; authentication mode: `sso`.
- Bootstrap enabled and `identityBootstrap.hookMode: helm`.
- Shared user/group assignments: Chris → `logai_admin` → `logai-admin`; Elvis, Beau and Sunil → `as_lead` → `as-lead`.
- Native user login with an empty `identity.idpHint` until a real external identity provider is configured.

The Helm chart owns one post-install/post-upgrade identity Job. Argo CD maps this same Job to PostSync after ordinary resources are healthy. Do not add a second bootstrap Job/hook to the Argo Application. The reconciler creates/repairs the realm, declared settings, application clients, roles, groups, configured users and memberships. Routine deployment does not require Keycloak web-console changes. Membership repair is additive; removal of privileges remains an explicit administration action.

A Schneider external IdP requires separately agreed issuer/discovery details, client credentials, claim/group mappings and broker configuration. The release does not invent these settings. First-login password changes are expected user actions, not deployment-console repair.

## 7. Deployment acceptance and production promotion

1. Confirm release/image availability and approve the reviewed site values.
2. Prepare namespaces, Secrets, database connectivity, ingress/DNS/TLS and registry access.
3. Apply the completed UAT Application and perform a full sync.
4. Confirm ready workloads, successful bootstrap hook, working HTTPS UI/login, expected roles and authorized API access. A successful bootstrap Job is deleted; use the Argo operation result to confirm success. A failed Job's logs are available temporarily.
5. Rerun a full sync and verify changed passwords and memberships remain intact. Complete initial-schema flag cleanup and real-data acceptance as applicable.
6. Promote the exact accepted application digests to production, using production-specific configuration and Secrets, then repeat acceptance checks.

Review the supplied resource requests/limits and production replica counts against cluster capacity and Schneider availability requirements. Retain the prior approved revision/digests and database backup/recovery procedure for rollback. Reverting application images does not automatically undo database migrations or reset Keycloak accounts.

Please return the confirmed Git/Argo destination settings, DNS origins, ingress/TLS approach, registry/digests, database arrangement and Secret names/ownership so that the deployment configuration can be finalized. Do not send plaintext Secret values in that response.
