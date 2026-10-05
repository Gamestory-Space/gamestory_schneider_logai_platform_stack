# Keycloak bootstrap runtime contract — v0.1.6

One desired-state reconciler runs from the compiled Identity API image: `python -c "from app.bootstrap import main; main()"`. Compose executes a finite `identity-bootstrap` service; standalone Helm executes the chart's post-install/post-upgrade Job; Argo CD interprets that same chart-defined Job as PostSync. No separate Argo hook or manual Keycloak console setup is required. Supply runtime credentials and site configuration before deployment.

Use the shipped `scripts/deploy-compose.sh` (source checkout: `scripts/client/deploy-compose.sh`) for every Compose deployment. It starts PostgreSQL/Keycloak, runs a fresh disposable bootstrap container after readiness, stops on failure, then starts the APIs/UI. Ordinary Compose startup also has health/completion dependencies for fresh installations, but a completed job may not rerun on an unchanged `up`; the deployment wrapper guarantees redeployment reconciliation.

## Runtime and persistence

The local Compose service uses Keycloak 26.0.8 (`quay.io/keycloak/keycloak:26.0.8`, tested digest `sha256:09a381c715ab0b111835b70f2905955274843a219c6f27efb348e4d9f4086858`). `start-dev` is for local validation. EKS must use production `start`, a durable PostgreSQL database, externally reachable HTTPS hostname and TLS/proxy settings matching Schneider ingress. Keycloak listens on 8080; health-enabled management port 9000 exposes `/health/ready` and `/health/live`. Keycloak requires writable `/opt/keycloak/data` and `/tmp`; keep these explicit if imposing a read-only root. Mount the sanitized import at `/opt/keycloak/data/import` read-only and use `--import-realm` for initial provisioning.

Supply database URL/user/password and bootstrap administrator username/password through runtime secrets (`KC_DB=postgres`, `KC_DB_URL`, `KC_DB_USERNAME`, `KC_DB_PASSWORD`, `KC_BOOTSTRAP_ADMIN_USERNAME`, `KC_BOOTSTRAP_ADMIN_PASSWORD`). Never place values in Git, image layers, frontend configuration or evidence. Bootstrap admin credentials create the initial administrator only. Recurring reconciliation requires an active authorized administrator: rotate the runtime Secret to the operational account before retiring the original bootstrap administrator. Back up the Keycloak database, which holds identities, signing keys and sessions.

## Application OIDC contract

Realm: `gamestory-sso`. Public issuer: `https://<keycloak-host>/realms/gamestory-sso`. Discovery is `/.well-known/openid-configuration` under that issuer. APIs may fetch JWKS internally at `/realms/gamestory-sso/protocol/openid-connect/certs`, but must validate the public issuer exactly.

`logai-ui` is a public browser client: authorization code with PKCE S256, no browser secret, direct password grants disabled. Configure the exact `https://<ui-host>/auth/callback` redirect, exact UI web origin and exact `https://<ui-host>/` post-logout redirect. The template contains loopback examples only. The internal operator tool `scripts/identity/render-keycloak-realm.py --ui-url https://<ui-host> --output <realm-file>` renders those allowlists before deployment.

`logai-api` is the bearer-only resource audience shared by Identity API and LogAI API. The UI access token includes it through its audience mapper. RS256 tokens must have `iss`, `sub`, `aud`, `iat`, `exp`; username is `preferred_username`, realm roles are `realm_access.roles`, client roles are `resource_access.<client>.roles`. Preserve these when adding a broker. Access tokens last five minutes; the UI refreshes through Keycloak and keeps tokens in memory.

Roles: `logai-admin` (Admin) and `as-lead` (AS Lead) each grant the existing business endpoints. There is no separate entitlement schema or invented difference in permissions; future fine-grained entitlements can extend existing enforcement. `logai-integration` grants technical callbacks and is reserved for a separately provisioned service identity. Human users are not assigned this role. Missing/invalid bearer tokens yield 401; insufficient roles yield 403. `/health` and `/ready` remain unauthenticated probe endpoints.

UI runtime variables: `AUTH_MODE=sso`, `AUTH_URL`, `AUTH_REALM=gamestory-sso`, `AUTH_CLIENT_ID=logai-ui`, `AUTH_CALLBACK_URL`, `AUTH_IDP_HINT=` (empty for local users), `IDENTITY_API_BASE_URL`, `LOGAI_API_BASE_URL`. Failed runtime configuration must not fall back to anonymous mode.

Identity API: `KEYCLOAK_PUBLIC_URL`, `KEYCLOAK_ISSUER_URL`, `KEYCLOAK_JWKS_FETCH_URL`, `KEYCLOAK_AUDIENCE=logai-api`, `API_CORS_ORIGINS` set to the UI origin. LogAI API: `AUTH_MODE=sso`, `OIDC_ISSUER_URL`, `OIDC_JWKS_URL`, `OIDC_AUDIENCE=logai-api`, `API_CORS_ORIGINS`. `AUTH_MODE=none` is restricted to explicit development/test environments and is not the EKS configuration.

APIs remain compiled, UID 10001, read-only root, writable `/tmp`. UI remains production Next.js, UID 1000, read-only root, writable `/tmp` and `/app/runtime-config` owned by UID 1000. No authentication secrets belong in the UI config.

## Bootstrap users and explicit administration

Deployment creates missing users with a temporary password and first-login password change; it never resets existing passwords, enabled/disabled state, profiles or required actions. No console creation or role assignment is needed for the configured bootstrap users. Password resets, disabling users and removal of existing privileges remain explicit administrative operations outside deployment reconciliation. Internal reset utilities are not invoked by deployment.

## Schneider IdP phase two

Configure the upstream provider in Keycloak after Schneider supplies its issuer/discovery endpoint, client ID, runtime secret or certificate, and the broker redirect `https://<keycloak-host>/realms/gamestory-sso/broker/<alias>/endpoint`. Agree username/email mapping, account linking, required profile fields, group-to-role mapping, first-login flow and upstream logout/session behavior. Keep the public Keycloak issuer, application clients/audiences, roles and callback stable. Set `AUTH_IDP_HINT=<alias>` only after the broker is operational; an empty hint continues to allow local bootstrap login. No Schneider credentials or invented broker configuration are included.

## SynQ and downstream boundary

Human Keycloak access tokens stop at LogAI. `app.audit.MachineAuthenticator` supplies independent connector headers when a confirmed mechanism is implemented; no speculative SynQ mechanism is selected. Current outbound requests contain audit metadata and no human Authorization header. Before production integration, Schneider/SynQ must supply authentication mechanism, token endpoint if any, credential type/provisioning/rotation, certificate requirements, scopes/roles, lifetime, base URL, TLS requirements, per-environment secrets and required audit headers. Until supplied, authenticated external integration readiness is pending.

Audit context carries correlation/request IDs, initiating subject/username/roles, source service, target system, operation and UTC timestamp in `X-LogAI-Audit-Context`; correlation/request IDs also have separate headers. The orchestration state persists the initiating context, without the access token. Downstream systems must treat the context as business metadata and authenticate the machine independently.

## Acceptance and release

Run `scripts/auth/test-keycloak-auth.py` with the three locally built images, an installed Playwright module and evidence directory. It creates disposable PostgreSQL/Keycloak/application containers, generates ephemeral passwords, tests first-login reset, browser callback, real JWT acceptance, negative access, roles, UI API authorization, logout/session revocation and config failure, then removes its containers and network. No client volumes are touched.

Retain source-leak gates, Trivy and SBOM checks for the final images. Registry push, signing and fresh digest pull remain deferred until publication is authorized. Local evidence records actual tested image IDs; it does not establish a published release.

## Shared users, roles and environment URLs

The same four bootstrap usernames (`chris`, `elvis`, `beau`, `sunil`) and group/role mapping apply in build, release, client-local, UAT and production. `identity/bootstrap-groups.json` assigns Chris to `logai_admin` / `logai-admin` and the others to `as_lead` / `as-lead`. Add future usernames to that non-secret model. Passwords are independent runtime credentials in each environment.

Assumed URL convention (replace `example.invalid` with the configured domain):

| Environment | LOGAI_PUBLIC_URL | KEYCLOAK_PUBLIC_URL |
|---|---|---|
| client-local | http://localhost:3000 | http://localhost:8080 |
| uat | https://logai-uat.example.invalid | https://keycloak-uat.example.invalid |
| prod | https://logai-prod.example.invalid | https://keycloak-prod.example.invalid |

Set `LOGAI_ENV=client-local`, `uat` or `prod`. Run the renderer with `--env <environment> --ui-url <LOGAI_PUBLIC_URL>` (or supply both variables in its environment), then import the resulting single realm. UAT/prod validation requires HTTPS and the explicit `logai-<env>.` hostname prefix, and rejects paths, wildcards, credentials, queries, fragments and cross-environment origins. Each generated client has exactly one callback, one origin and one post-logout URL. Configure each API's CORS origin and UI runtime callback from the same `LOGAI_PUBLIC_URL`; set the issuer from its environment's `KEYCLOAK_PUBLIC_URL`. Compose accepts `KEYCLOAK_REALM_DIRECTORY` to mount a rendered realm directory for custom origins. Stable client/audience names are not additional environment knobs.

`environments/uat/values.yaml` and `environments/prod/values.yaml` are the Helm deployment inputs. The chart generates exact application redirects and runtime URLs from the same settings. The reconciler creates missing realms/clients and repairs declared application-owned settings on existing installations without overwriting external IdPs. Legacy unrelated clients are preserved; retiring them requires an explicit migration decision.

Future Schneider mappings must consume agreed group/application entitlements and map recognized values to `logai-admin`/`as-lead`. No Schneider group names or secrets have been invented.

Configuration CI runs `scripts/identity/check-keycloak-config.py` to reject sample identifiers or embedded credentials in the deployable realm, enforce PKCE/client/role structure, validate all environment URLs and reject absent bootstrap assignments.

Reference behavior was checked against the official Keycloak [bootstrap administrator guide](https://www.keycloak.org/server/bootstrap-admin-recovery) and [hostname guide](https://www.keycloak.org/server/hostname).

The identity-kit realm is the canonical baseline; `identity/keycloak/gamestory-sso-realm.json` in this platform release is its byte-identical sanitized handover snapshot. Deployment-specific files are generated from that snapshot, rather than maintained separately per environment.

## Reconciliation and credentials

The only reconciliation implementation is `app.bootstrap` and `app.identity_bootstrap` in the Identity API image. Platform `scripts/identity/bootstrap-identity.py` is an optional container-launch adapter; it contains no separate reconciliation algorithm. The desired realm and user model are mounted JSON, never embedded credentials.

Compose receives administrator credentials from its existing runtime env file and `KEYCLOAK_LOGAI_BOOTSTRAP_PASSWORD` as the temporary initial user password. Set the latter before deployment; examples intentionally leave it blank. Do not commit the runtime env file or put passwords in command arguments. Kubernetes uses mounted existing Secret files for admin username/password and initial user password. The shared entry point supports mounted files in both paths and fails closed on missing credentials.

The reconciler waits for `/health/ready`, creates a missing realm, repairs declared realm settings and user-profile requirements, creates/updates the two application clients, ensures canonical roles/groups/group mappings, creates missing users and adds configured memberships. Existing credentials and user account state are preserved. Known direct canonical roles are retained and reflected in equivalent groups. Reconciliation is additive: it does not remove extra memberships or downgrade existing privileges. External IdPs and unrelated clients are preserved.

The bootstrap administrator must remain authorized across deployments; updating a bootstrap Secret does not automatically reset an existing Keycloak administrator password. Synchronize credential rotation with the operational account.

Final artifact and archive checks reject proprietary source and prohibited credential bytes. Runtime env files and Windows Zone.Identifier metadata are excluded from client bundles. Browser acceptance checks fresh initialization and changed-password preservation; Compose lifecycle tests check rerun and failure gating. Images must be published or mirrored before a client deployment; local validation does not constitute registry publication or an EKS/Argo sync.
