# PRD --- LogAI Keycloak User, Group & Role Bootstrap Across Environments

**Target:** Codex\
**Release:** v0.1.6 / Schneider deployment hardening (supersedes the original v0.1.5 target)\
**Scope:** Keycloak identity configuration and bootstrap\
**Principle:** Reproduce the locally validated identity model in every
LogAI environment without manual Keycloak configuration.

## 1. Objective

Make LogAI Keycloak configuration deterministic across **Build → Release
→ Client Local → UAT → Production**.

A clean environment must establish the required LogAI roles, groups,
group-to-role mappings and initial native Keycloak users. Initial
deployment uses Keycloak-native users; Schneider enterprise IdP
federation follows later without changing LogAI's downstream
authorization contract.

## 2. Authorization model

Canonical realm roles in `gamestory-sso`:

  -----------------------------------------------------------------------
  Realm role                          Purpose
  ----------------------------------- -----------------------------------
  `logai-admin`                       LogAI administrator

  `as-lead`                           AutoStore Lead / operational lead

  `logai-integration`                 Technical integration identity; not
                                      for human bootstrap users
  -----------------------------------------------------------------------

Groups:

  Keycloak group   Realm role
  ---------------- ---------------
  `logai_admin`    `logai-admin`
  `as_lead`        `as-lead`

Required chain:

    User → Keycloak Group → Realm Role → JWT realm_access.roles → LogAI authorization

Validated example:

    Chris → logai_admin → logai-admin → LogAI

Group membership alone is insufficient; group-to-realm-role mappings
must be part of deployable configuration.

## 3. Initial users

Provision the initial native Keycloak users in every environment:

-   Chris
-   Elvis
-   Beau
-   Sunil

Inspect existing configuration for canonical usernames and preserve
them. Do not invent email addresses or personal information. Adding
future users must be configuration-driven rather than requiring code
changes.

Confirmed assignments (identical in Build, Release, Client Local, UAT and Production):

| Canonical username | Keycloak group | Canonical realm role |
|---|---|---|
| `chris` | `logai_admin` | `logai-admin` |
| `elvis` | `as_lead` | `as-lead` |
| `beau` | `as_lead` | `as-lead` |
| `sunil` | `as_lead` | `as-lead` |

These assignments are stored in `identity/bootstrap-groups.json`. Future users and memberships remain configuration-driven. Preserve existing known assignments when initializing an established realm; never downgrade or remove memberships implicitly.

## 4. Bootstrap password

The controlled initial bootstrap password is supplied only through the runtime secret `KEYCLOAK_LOGAI_BOOTSTRAP_PASSWORD` or a mounted secret file. Its value is deliberately omitted from this PRD.

**The value must never be persisted in Git or any release artifact.** It
must not appear in realm JSON, source code, Dockerfiles/images/layers,
committed Compose/Helm configuration, generated documentation, logs, CI
output, SBOM/provenance metadata, Nuitka binaries, frontend bundles or
committed test fixtures.

The value is supplied only at bootstrap/runtime through a secret. For
Schneider UAT/Production, expose a secret contract that Schneider can
map into its Helm/Argo deployment. Gamestory defines the secret
semantics; Schneider owns secret storage/injection.

Codex should inspect existing secret naming conventions before defining
a new name. A semantic name such as `KEYCLOAK_LOGAI_BOOTSTRAP_PASSWORD`
is acceptable if no established convention exists.

## 5. Mandatory first-login password change

Every initial password must be temporary. Keycloak must force
`UPDATE_PASSWORD` on first login:

    Initial login → bootstrap password → UPDATE_PASSWORD → user chooses private password → normal LogAI authentication

LogAI must never receive or store user passwords.

## 6. Realm configuration

Treat `gamestory-identity-kit/keycloak/realms/gamestory-sso-realm.json`
as the existing baseline.

The deployable identity configuration must include the realm, canonical
LogAI roles, groups, group-to-role mappings, actual LogAI OIDC
client/audience configuration, required protocol mappers/scopes, and
future external-IdP capability.

Explicitly ensure:

    logai_admin → logai-admin
    as_lead     → as-lead

These mappings must survive a completely clean Keycloak
deployment/import and require no Admin Console repair.

## 7. Configuration versus credentials

Version-controlled/reproducible configuration may contain realm,
clients, roles, groups, group-role mappings, protocol/OIDC configuration
and bootstrap user/group definitions.

The bootstrap password must exist only as a runtime secret.

Where practical, provision users through an idempotent bootstrap
operation rather than embedding credentials in the realm export.

## 8. Environment consistency

The same logical identity model must exist in:

-   `build`
-   `release`
-   `client-local`
-   `uat`
-   `prod`

Roles, groups and mappings must not drift between environments. URLs,
secrets, hostnames and external IdP settings remain environment-specific
configuration.

## 9. Idempotency

Bootstrap must safely rerun when realms, roles, groups, users, mappings
or memberships already exist.

**Rerunning bootstrap must NEVER reset an existing user's password back
to the initial bootstrap credential.**

The bootstrap credential applies only when initially provisioning an
account. Once a user changes the temporary password, subsequent
deployments/bootstrap runs must leave that credential untouched.

## 10. Schneider SSO compatibility

Current:

    Native Keycloak User → Keycloak Group → LogAI Realm Role → JWT → LogAI

Future:

    Schneider Identity → Schneider IdP/Entra → Keycloak federation → LogAI Realm Role → JWT → LogAI

The lower authorization contract remains stable. Do not couple LogAI
authorization directly to future Schneider AD group names.

## 11. JWT contract

Verify canonical application roles appear in access tokens. For Chris,
the semantic equivalent is:

``` json
{
  "realm_access": {
    "roles": ["logai-admin"]
  }
}
```

LogAI authorizes against canonical realm roles, not group names:

`logai_admin` = identity/group construct\
`logai-admin` = application authorization role

## 12. Automated validation

Tests must cover:

1.  **Fresh environment:** clean Keycloak import creates required roles,
    groups and mappings.
2.  **Admin user:** bootstrap Chris, verify `logai_admin` membership and
    `logai-admin` in token.
3.  **First login:** bootstrap credential requires password update.
4.  **After password change:** chosen password works and bootstrap
    password no longer authenticates that user.
5.  **Authorization:** Chris can call a protected endpoint requiring
    `logai-admin`.
6.  **Insufficient role:** appropriate non-admin receives `403` for
    admin-only operation.
7.  **Bootstrap rerun:** after password change, rerun bootstrap and
    verify user, membership and role remain while the changed password
    remains untouched.

The rerun/password-preservation case is release-critical.

## 13. Secret leakage validation

CI should inspect final distributable artifacts and fail if the
bootstrap credential is present in source-controlled deployment
configuration, generated realm JSON, container files/layers, frontend
output, compiled backend artifacts or generated deployment packages.

The check must not echo the credential; report only that forbidden
bootstrap credential material was detected.

## 14. Ownership

Gamestory owns realm contract, roles, groups, mappings, bootstrap
behaviour, JWT authorization contract, required secret semantics and
validation.

Schneider owns shared-EKS Helm implementation, Argo CD configuration,
secret storage/injection, environment-specific URLs, enterprise IdP
configuration and eventual Schneider federation.

Codex must not create Schneider's Helm chart or Argo configuration;
provide the runtime contract Schneider needs.

## 15. No topology change

This work must not introduce another deployable service.

Existing topology remains:

    LogAI UI
    LogAI API
    Identity API
    Keycloak
    Postgres/RDS

Prefer initialization/bootstrap tooling around existing Keycloak rather
than a permanent service.

## 16. Codex execution

### Phase 1 --- Inspect

Inspect current realm JSON, Keycloak startup/import, existing bootstrap
code, Identity API, LogAI authorization/JWT extraction,
Compose/environment configuration, secret conventions, CI and existing
Keycloak scripts. Identify the smallest robust change.

### Phase 2 --- Report

Report the current identity model, proposed implementation, files
affected, secret injection mechanism, idempotency strategy, first-login
reset behaviour and clean-environment validation approach. Do not
redesign unrelated identity components.

### Phase 3 --- Implement

Implement deterministic role/group/user bootstrap.

### Phase 4 --- Validate

Validate against a completely clean Keycloak state, not only the
manually corrected developer realm.

## Definition of Done

A fresh LogAI environment automatically establishes the `gamestory-sso`
canonical roles, groups, group-to-role mappings and configured bootstrap
users.

Chris can authenticate using the runtime-supplied bootstrap credential,
is forced to choose a new password, receives `logai-admin` through
`logai_admin`, and can access appropriate protected LogAI APIs.

The mechanism works across Build, Release, Client Local, UAT and
Production. No manual Keycloak role/group configuration is required.

The bootstrap credential is not persisted in Git, realm configuration,
images, binaries, deployment packages or logs, and rerunning bootstrap
can never reset an established user's password.

**No new deployable service is introduced.**

## Confirmed implementation decisions

- Image candidate version: `v0.1.6`; image publication remains deferred.
- Shared realm: `gamestory-sso`; OIDC client `logai-ui`; API audience `logai-api`.
- Human JWT roles remain `realm_access.roles`; group names are not API authorization keys.
- Shared group model applies to all five environments; public URLs and secrets vary by environment.
- `scripts/identity/bootstrap-identity.py` initializes missing users and group mappings without resetting existing credentials, required actions or enabled state.
- New users receive a temporary credential and `UPDATE_PASSWORD`; an existing user's changed password survives every bootstrap rerun.
- Initial bootstrap tooling runs as a finite administrative deployment step, with no new permanent service and no changes to Schneider-owned Helm/Argo configuration.
- The admin-only identity endpoint is `/api/v1/admin/identity`; `as-lead` receives 403 there while retaining existing business endpoint access.
- Clean-environment acceptance must prove group inheritance, all four assignments, mandatory password change, rejection of the initial credential after change, and successful login with the changed password after bootstrap rerun.

- Release enforcement: every platform PR/release runs bootstrap password-preservation regression tests; a platform release must also pass the real clean-Keycloak browser/rerun suite before publication. Referenced component images must be published first when publication is authorized.

- Release packages exclude runtime env files and Windows metadata; only non-secret templates are distributed. Local regression and archive-policy checks pass. Environment-wide deployment requires invoking the finite bootstrap step with runtime secrets; this session has not deployed Schneider UAT/Production.


### Deployment lifecycle parity — v0.1.6

All five environments invoke the same compiled `app.bootstrap` reconciler. Compose uses a finite `identity-bootstrap` service and the shipped deployment wrapper reruns it on every deployment after Keycloak readiness, propagates failure and gates application startup. Standalone Helm uses post-install/post-upgrade hooks; UAT/Prod Argo maps these chart-owned Helm hooks to PostSync. No separate Argo Application hook or manual Keycloak web-console setup is required. Realm settings, user-profile configuration, clients and missing roles/groups/users/mappings are repaired without changing existing credentials or user account state. Membership repair remains additive. Older operator-only initialization descriptions are superseded by this lifecycle contract.
