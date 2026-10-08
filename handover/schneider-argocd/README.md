# Schneider Argo CD Helm transfer review

This material implements `handover/ArgoCD helm changes.prd.txt` against the manually captured Schneider state. The Schneider machine and feature branch were not inspected. These are additive transfer files, not a replacement chart. No deployment, database change, commit or push is performed.

## Correct / retain

- One RDS PostgreSQL host with separate `logai` / `keycloak` databases, `logai_runtime` / `keycloak` users and independent passwords is compatible. Neither API nor Keycloak creates PostgreSQL databases or login users. Schneider must provision both before deployment. Keycloak manages its own tables inside its database and needs appropriate schema privileges.
- Keep `logaiApi.applyDatabaseSchemaOnStartup` and `seedSampleDataOnStartup` false for UAT/PROD.
- Retain the Keycloak Service/Deployment, `start`, pinned image, proxy headers and management probes. Set `KC_HOSTNAME=https://<hosts.auth>` so discovery returns the expected public issuer.
- The existing `logai-keycloak` Secret can contain admin credentials and `db-password`. Separate Secrets are optional for different access/rotation ownership; this adaptation projects only the two admin keys into the Job. LogAI credentials remain in `logai-database`.

## Missing / must add

1. Copy `templates/45-identity-bootstrap.yaml` and both `files/*.json` into the same paths under Schneider's `applications/logai`. The ConfigMap is a normal Sync resource; only the finite Job is PostSync.
2. Merge `values-transfer.yaml` into the existing values. Preserve Schneider's namespace, gateway, Rancher configuration, external Secret ownership and empty platform placeholders.
3. Add a second port to the **existing Keycloak Service** in `40-keycloak.yaml`:

   ```yaml
   - name: management
     port: 9000
     targetPort: management
   ```

   Keep HTTP port 80 targeting `http`. Do not expose management through Istio/public routes. A container port alone does not expose port 9000 through a Service. Permit Job-to-Keycloak traffic on 80 and 9000 in platform network policies.
4. Transfer the runtime environment mapping below into the existing application templates or their ConfigMap. The Job does not configure the API/UI Deployments.

## Needs confirmation from Schneider

- Confirm v0.1.7 image availability and approved image digests, imagePullSecret, namespace policies and initial-user policy. `username` preserves the current reference contract: newly created users receive `logai_<username>` without forced rotation. `shared` requires an external `logai-bootstrap-users` Secret key `password` and forces initial password change. Existing accounts retain passwords, enabled state, profile and required actions in both modes.
- Confirm full Argo syncs and PostSync support. PostSync runs only after all Sync resources are healthy; do not make application readiness depend on the realm bootstrap or the hook will never run. Hooks do not run in selective syncs. See [Argo phases and waves](https://argo-cd.readthedocs.io/en/latest/user-guide/sync-waves/).
- Confirm schema ownership, migration credentials, approval, backup/recovery and execution order before first deployment.

## Potential defect

- Captured v0.1.4 application tags are placeholders; the supplied overlay proposes v0.1.7, without asserting the remote values have changed.
- `identity.authMode: none` is invalid for the LogAI API with `ENVIRONMENT=prod` or `uat`; `keycloak` is not a supported API auth mode either. Use `sso`. Client `gamestory-ui` mismatches the existing `logai-ui` client. Clear `gamestory-entra` unless that IdP actually exists; bootstrap preserves existing external IdPs and does not create one.
- The old reference chart puts Keycloak and LogAI on the same database/credential configuration. Do not copy its Keycloak JDBC/database wiring into Schneider's separated topology.
- `/health` and `/ready` currently return static success without checking tables or the database. With both initialization flags false, an empty database does not receive schema; API startup can succeed, but table-backed requests fail. A successful rollout or bootstrap Job does not prove LogAI schema readiness.
- The UI entrypoint writes specifically `/app/runtime-config/config.json`. Its values field does not change that path; retain `/app/runtime-config`, mount a writable emptyDir and keep UID/GID 1000. APIs use UID/GID 10001. UI listens on 3000, APIs on 8000.

## Schneider/platform-owned input required

Supply real UI/API/identity/auth DNS hostnames, RDS host, external Secrets, TLS secret, image pull credentials if needed, both databases/users and namespace/network permissions. No hostnames or credentials are supplied here. The enabled bootstrap template rejects missing hosts/RDS host, invalid public hostname shapes and incompatible identity settings. Existing Schneider validation must also cover disabled-bootstrap deployments and its other required fields.

## Runtime environment mapping

Use HTTPS public origins from `hosts.*`; do not place Kubernetes Service addresses in browser configuration.

| Deployment | Environment mapping |
| --- | --- |
| Both APIs | `ENVIRONMENT=environment`, `API_CORS_ORIGINS=https://hosts.ui` |
| Identity API | `KEYCLOAK_REALM=gamestory-sso`, `KEYCLOAK_PUBLIC_URL=https://hosts.auth`, `KEYCLOAK_ISSUER_URL=https://hosts.auth/realms/gamestory-sso`, `KEYCLOAK_JWKS_FETCH_URL=http://keycloak:80/realms/gamestory-sso/protocol/openid-connect/certs`, `KEYCLOAK_AUDIENCE=logai-api` |
| LogAI API | `AUTH_MODE=sso`, `OIDC_ISSUER_URL=https://hosts.auth/realms/gamestory-sso`, `OIDC_JWKS_URL=http://keycloak:80/realms/gamestory-sso/protocol/openid-connect/certs`, `OIDC_AUDIENCE=logai-api`, both startup flags `false` |
| UI | `AUTH_MODE=sso`, `AUTH_URL=https://hosts.auth`, `AUTH_REALM=gamestory-sso`, `AUTH_CLIENT_ID=logai-ui`, `AUTH_IDP_HINT=identity.idpHint`, `AUTH_CALLBACK_URL=https://hosts.ui/auth/callback`, `IDENTITY_API_BASE_URL=https://hosts.identity`, `LOGAI_API_BASE_URL=https://hosts.api`, `HOSTNAME=0.0.0.0` |

The reference LogAI chart **does not construct** DATABASE_URL from individual fields: it reads a complete URL from an existing Secret (`databaseUrl` in the reference). For Schneider use its externally managed `logai-database` key `database-url` consistently:

```yaml
- name: DATABASE_URL
  valueFrom:
    secretKeyRef:
      name: {{ .Values.database.secretName }}
      key: database-url
```

The Secret owner must construct `postgresql://<percent-encoded username>:<percent-encoded password>@<database.host>:<database.port>/<database.name>?sslmode=<database.sslMode>` targeting `logai_runtime`, `logai` and `require`. Verify every field against the environment; Helm cannot inspect that external Secret. Never concatenate unescaped credentials in Helm values.

Keycloak instead uses `jdbc:postgresql://<database.host>:<database.port>/<keycloak.db.name>?sslmode=<database.sslMode>`, `KC_DB_USERNAME=keycloak.db.username`, and `KC_DB_PASSWORD` from `keycloak.secretName` / `db-password`. Do not substitute `database.name` or LogAI's username/password.

## Existing bootstrap contract and lifecycle

Source: `gamestory-identity-kit/backend/app/bootstrap.py`, `bootstrap_admin.py`, `identity_bootstrap.py`; Helm reference: `helm/gamestory-schneider-platform/templates/identity-bootstrap.yaml`.

The Job reuses `docker.io/chrismdgs/gamestory_logai_schneider:identity-api-v0.1.7` and overrides CMD with `python -c "from app.bootstrap import main; main()"`. The production image retains Python and the compiled app module. Realm and users are mounted at `/bootstrap/realm.json` and `/bootstrap/users.json`. Admin files mount at `/runtime-secrets/admin/{username,password}` from the existing Secret's `admin-username` / `admin-password` keys. Only shared mode mounts the user password Secret.

Explicit environment uses internal `KEYCLOAK_BOOTSTRAP_URL=http://keycloak:80`, `KEYCLOAK_BOOTSTRAP_HEALTH_URL=http://keycloak:9000/health/ready`, `KEYCLOAK_BOOTSTRAP_ALLOW_INTERNAL_HTTP=true`, public `KEYCLOAK_PUBLIC_URL` and `LOGAI_PUBLIC_URL`, admin file variables and password mode. The default readiness wait is 300 seconds; the Job deadline is 600 seconds with one retry. It checks readiness, authenticates, reconciles, checks the public discovery issuer, and exits.

Reconciliation creates the realm if absent, updates declared realm settings/user-profile schema and application-owned clients, adds canonical roles/groups/memberships and creates missing users. Existing user profile state/passwords and external IdPs are preserved; application-owned realm/client/profile-schema configuration is deliberately reconciled. Unrelated users, groups and direct roles are not removed.

`BeforeHookCreation,HookSucceeded` reruns the named Job and cleans successful hooks; failed Jobs remain for diagnosis until the next full sync. No Job TTL is used, so Kubernetes cannot remove evidence before Argo reads the result. The ConfigMap remains available for every sync.

## Database initialization and migration gap

`gamestory-logai-api/app/db.py:apply_schema()` applies `001_release_and_chutes_read_models.sql` and `003_order_orchestration_runs.sql`, committing each file separately. `002_seed_schneider_sample_read_models.sql` is separate sample seeding and must not run in UAT/PROD. SQL files ship in the production image under `/app/schema`. This is schema initialization, not a versioned migration runner: there is no migration ledger, concurrency lock, whole-operation transaction or implemented Argo PreSync migration Job in the current reference.

A controlled operation can reuse the LogAI API image with `python -c "from app.db import apply_schema; apply_schema()"`, the approved DATABASE_URL Secret and SSO environment required by Settings. This is a proposal for initial schema preparation, not an automatically enabled migration. Validate the SQL and privileges against a disposable database and obtain Schneider's migration process decision before transfer. A separate schema owner/migration credential should hold DDL privileges; grant runtime only required access. Existing IF NOT EXISTS statements do not implement future column changes.

For a future PreSync Job, the namespace, Secret, image pull Secret, service account and network access must already exist before PreSync; ordinary Sync resources are too late. Do not enable schema-on-startup or seed samples to mask this gap. Verify required tables and one authorized table-backed request after schema preparation, independently of `/ready`.
