# PRD — LogAI Keycloak Realm Productionisation: Users, Roles & Environment URLs

**Target:** Codex
**Release:** v0.1.5
**Primary baseline:** `gamestory-identity-kit/keycloak/realms/gamestory-sso-realm.json`
**Scope:** Keycloak realm/client cleanup, initial local users, LogAI roles, environment-specific OIDC URLs, configuration and validation
**Out of scope:** Schneider IdP federation itself; Schneider-owned Helm/Argo CD implementation

## 1. Objective

Convert the current `gamestory-sso` realm from the identity-kit/sample configuration into the real LogAI authentication contract.

The result must:

1. replace `sample-app`, `sample-ui`, sample localhost URLs and sample audience naming;
2. define the real LogAI OIDC client/audience model based on the existing application implementation;
3. define the first two canonical LogAI roles;
4. support four initial Keycloak-native users;
5. keep user passwords out of Git and realm JSON;
6. support environment-specific LogAI URLs without maintaining divergent realm designs;
7. preserve external-IdP capability for upcoming Schneider SSO;
8. make Keycloak authentication the normal EKS path rather than `authMode: none`.

## 2. Existing baseline

Current realm already defines `gamestory-sso`, OpenID Connect, PKCE S256, `sample-app`, `sample-ui`, and a Gamestory Entra identity-provider placeholder.

The sample clients, audiences and localhost URLs are identity-kit residue and must not become the Schneider LogAI contract.

Codex must inspect the actual LogAI UI/API authentication code before deciding the final client topology. Do not mechanically rename sample clients if the implementation requires a different arrangement.

## 3. Canonical roles

Create these Keycloak realm roles:

| Display meaning | Canonical role identifier |
|---|---|
| Admin | `logai-admin` |
| AS Lead | `as-lead` |

Use canonical identifiers in JWTs, API authorization and future Schneider group mappings. Display strings such as `Admin` and `AS Lead` must not become authorization keys in application code.

## 4. Initial local users

Support these Keycloak-native users:

- Elvis (`elvis`)
- Beau (`beau`)
- Sunil (`sunil`)
- Chris (`chris`)

Do not invent email addresses.

### Role assignment

The exact user-to-role assignment must be configurable and easy to change without rebuilding application images. Until the assignment is explicitly supplied, provide a bootstrap mapping/configuration mechanism rather than guessing:

```text
elvis  -> <logai-admin | as-lead>
beau   -> <logai-admin | as-lead>
sunil  -> <logai-admin | as-lead>
chris  -> <logai-admin | as-lead>
```

A user may support multiple roles, but keep the initial model simple.

## 5. Password provisioning

Do not commit passwords into the realm JSON, Git, Dockerfiles, OCI images, frontend configuration or Nuitka binaries.

Provide a secure bootstrap mechanism for setting initial passwords at deployment/runtime. Initial passwords should preferably be temporary credentials requiring a password change on first login.

Document the operator procedure for creating/bootstraping the users, assigning roles, setting initial passwords, resetting a password and disabling a bootstrap user.

The realm import must be usable without knowing any user password.

## 6. Real LogAI OIDC contract

Inspect the current LogAI UI authentication flow, Identity API, LogAI API, callback handling, token validation, issuer, audience and role claim handling.

Replace the sample identity-kit contract with the actual LogAI contract.

Preferred stable naming, where compatible with the implementation:

```text
logai-ui
logai-api
```

The browser-facing client should use OIDC Authorization Code + PKCE unless inspection proves the application intentionally requires something else. Do not enable implicit flow or direct password grants merely for convenience.

## 7. Remove sample configuration

Remove or replace production-facing occurrences of:

```text
sample-app
sample-ui
Sample Relying Party Application
Identity Sample UI
sample-app-audience
sample.localhost
sample-app.localhost
```

Add a lightweight CI/configuration check that fails if these sample identifiers remain in deployable LogAI identity configuration, except deliberately retained test/history fixtures.

## 8. Environment-specific URL model

Do not hard-code one Schneider hostname into the realm design.

Canonical deployment environments for this authentication contract:

```text
client-local
uat
prod
```

`build` and `release` may retain their existing validation behaviour where required.

Use an explicit environment tag and configurable domain:

```text
LOGAI_ENV=uat
LOGAI_PUBLIC_URL=https://logai-uat.<schneider-domain>

LOGAI_ENV=prod
LOGAI_PUBLIC_URL=https://logai-prod.<schneider-domain>
```

For client-local:

```text
LOGAI_ENV=client-local
LOGAI_PUBLIC_URL=http://localhost:3000
```

`<schneider-domain>` remains configurable until Schneider supplies final DNS/domain details. Do not invent a Schneider domain.

The assumed convention is:

```text
https://logai-<env>.<configured-domain>
```

Production should retain the explicit `prod` tag unless Schneider later requires an untagged production hostname.

## 9. Redirect URI and web-origin derivation

Derive Keycloak redirect URIs and web origins from `LOGAI_PUBLIC_URL` plus the actual callback path used by LogAI.

Conceptually:

```text
Web origin:
${LOGAI_PUBLIC_URL}

Redirect URI:
${LOGAI_PUBLIC_URL}/<actual-auth-callback-path>

Post logout redirect:
${LOGAI_PUBLIC_URL}/<actual-post-logout-path-or-pattern>
```

Codex must discover the actual callback/logout paths from the application. Do not guess `/auth/callback` merely because it existed in the sample realm.

Use the narrowest practical redirect URI patterns; avoid unrestricted wildcards where predictable callback paths can be used.

## 10. Realm templating/configuration

Implement the smallest robust mechanism compatible with the existing identity-kit/startup process for deployment-specific non-secret values such as:

```text
LOGAI_ENV
LOGAI_PUBLIC_URL
LOGAI_UI_CLIENT_ID
LOGAI_API_AUDIENCE
```

Do not create unnecessary variables where stable values such as `logai-ui` and `logai-api` can remain constant across environments.

Principle:

```text
same application identity contract
+ environment-specific URLs/secrets
= different deployment environment
```

Do not create separate hand-maintained realm files that can drift in security behaviour.

## 11. Issuer model

Keep the realm identity stable:

```text
gamestory-sso
```

LogAI must consume the correct environment-specific Keycloak issuer URL. Document the contract conceptually as:

```text
KEYCLOAK_PUBLIC_URL=<environment-specific Keycloak URL>
KEYCLOAK_REALM=gamestory-sso
OIDC_ISSUER=${KEYCLOAK_PUBLIC_URL}/realms/gamestory-sso
```

Reuse existing application variable names where possible rather than introducing duplicates.

## 12. Role claim contract

Ensure the access token presented to LogAI exposes canonical roles in a deterministic claim/path understood by the API.

```text
authenticated user
    |
    v
Keycloak access token
    |
    +-- logai-admin
    or
    +-- as-lead
    |
    v
LogAI authorization
```

Document the exact JWT claim/path used after implementation.

## 13. Future Schneider SSO compatibility

Preserve the future flow:

```text
Schneider user
      |
      v
Schneider IdP / Entra
      |
      | group / entitlement claims
      v
Keycloak
      |
      | selected claim -> canonical LogAI role
      v
logai-admin / as-lead
      |
      v
LogAI
```

Do not invent Schneider group names and do not assume Schneider will send every AD group. Future mapping should consume only the group/application-entitlement claims agreed with Schneider and map recognised values to the same canonical roles.

The four local users are bootstrap users, not a replacement corporate identity store.

## 14. Existing external IdP placeholder

The realm currently contains an Entra identity-provider definition using `ENTRA_TENANT_ID`, `ENTRA_CLIENT_ID` and `ENTRA_CLIENT_SECRET` placeholders.

Do not silently turn the Gamestory placeholder into a Schneider production IdP by inventing values.

Inspect whether it should remain disabled/hidden as a template until Schneider configuration arrives, or move into an environment-specific external-IdP configuration layer.

Local-user login must work independently of the external IdP.

## 15. Login UX

For the non-IdP phase:

```text
User opens LogAI
      |
      v
LogAI detects unauthenticated session
      |
      v
redirect to Keycloak
      |
      v
Keycloak username/password page
      |
      v
successful authentication
      |
      v
redirect back to LogAI
```

Do not build a second username/password form inside LogAI. Keycloak owns credential collection. Custom Keycloak theming is optional for this PRD.

## 16. Authorization boundary

This PRD establishes authentication and canonical application roles.

Role-to-entitlement behaviour may live in LogAI/PostgreSQL, but Codex must first inspect the existing authorization model. Do not invent a new entitlement schema merely to complete this change.

Intended separation:

```text
Schneider identity
 -> Schneider group/application assignment
 -> Keycloak canonical LogAI role
 -> LogAI/Postgres entitlements
 -> API enforcement
```

## 17. Schneider runtime handover

Produce a concise identity runtime contract containing no secrets. It must state:

- realm: `gamestory-sso`;
- actual LogAI OIDC client ID(s);
- API audience;
- OIDC flow;
- PKCE requirement;
- issuer pattern;
- callback path;
- logout callback/path;
- environment URL convention;
- required public Keycloak URL;
- canonical roles `logai-admin` and `as-lead`;
- expected JWT role claim/path;
- required runtime secrets by name/purpose;
- bootstrap-user procedure;
- external-IdP integration points.

Schneider owns translating this into its Helm/Argo/EKS configuration. Codex must not create or modify Schneider-owned Helm or Argo CD configuration.

## 18. Validation

Validate `client-local` plus configuration generation/validation for `uat` and `prod`.

For each bootstrap user, verify redirect to Keycloak, authentication, first-login password change if configured, return to LogAI, token issuer, audience, assigned canonical role, protected API access and logout.

Negative tests must cover invalid password, disabled user, missing token, expired/invalid token, wrong issuer, wrong audience where applicable, and insufficient role.

Verify generated/configured URL values for all three environments and confirm there are no accidental sample URLs or cross-environment redirects.

## 19. CI/configuration checks

Fail deployable identity configuration if it contains sample identifiers such as `sample-app`, `sample-ui`, `sample.localhost` or `sample-app.localhost`, or plaintext bootstrap passwords/confidential IdP secrets.

Do not weaken existing v0.1.5 source-protection, non-root, read-only filesystem, SBOM or security-scanning requirements.

## 20. Codex execution sequence

### Phase 1 — Inspect

Inspect the realm JSON, Keycloak startup/import process, LogAI UI OIDC implementation, Identity API, LogAI API, existing environment files, runtime-config mechanism and current role/authorization handling.

### Phase 2 — Proposal

Before broad implementation, report the actual OIDC flow, callback/logout paths, required clients/audiences, reusable configuration variables, proposed realm changes, secure bootstrap-user mechanism and environment URL substitution mechanism.

Avoid introducing parallel configuration models.

### Phase 3 — Implement

Implement the smallest coherent productionisation of the realm and application configuration.

### Phase 4 — Validate

Run authentication, authorization and environment-isolation tests.

### Phase 5 — Handover

Produce the Schneider identity runtime contract.

## 21. Definition of Done

The identity kit no longer exposes a sample application contract. The deployable model is:

```text
client-local / uat / prod
          |
          | environment-specific URLs
          v
      gamestory-sso
          |
          +-- actual LogAI UI client contract
          +-- actual LogAI API audience contract
          |
          +-- role: logai-admin
          +-- role: as-lead
          |
          +-- Elvis
          +-- Beau
          +-- Sunil
          +-- Chris
          |
          +-- future Schneider IdP
```

Passwords remain outside source control. The same canonical LogAI roles work with local users today and Schneider group-to-role mapping later. Environment differences are configuration, not different application images or divergent identity designs.
