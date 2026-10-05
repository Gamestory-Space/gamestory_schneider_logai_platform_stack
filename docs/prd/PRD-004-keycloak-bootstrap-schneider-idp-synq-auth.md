# PRD — LogAI Keycloak Bootstrap Authentication & Schneider IdP Transition

**Target:** Codex
**Release target:** v0.1.5
**Scope:** LogAI UI, Identity API, LogAI API, Keycloak configuration and Gamestory-owned runtime configuration
**Out of scope:** Schneider-owned Helm and Argo CD configuration

## 1. Objective

Change the initial Schneider EKS authentication strategy from `authMode: none` to **Keycloak-backed authentication from day one**, without making initial deployment dependent on Schneider IdP/Entra integration.

Phase 1 uses Keycloak-native local users. Phase 2, expected shortly afterwards, adds Schneider IdP federation/identity brokering while preserving the LogAI-to-Keycloak OIDC contract.

Also establish a strict separation between:
- human authentication into LogAI; and
- machine-to-machine authentication from LogAI/Autobahn to SynQ and other downstream systems.

## 2. Target progression

```text
PHASE 1 — INITIAL EKS

User
  | username/password
  v
Keycloak (local user)
  | OIDC/JWT
  v
LogAI UI / APIs


PHASE 2 — SCHNEIDER SSO

Schneider User
  v
Schneider IdP / Entra
  v
Keycloak identity broker
  | same OIDC/JWT application contract
  v
LogAI UI / APIs
```

LogAI must depend on Keycloak's OIDC contract, not on the mechanism Keycloak used to authenticate the user.

## 3. Human authentication requirements

For initial EKS:
- Keycloak is a required runtime component.
- LogAI UI authenticates through Keycloak using OIDC.
- APIs validate the appropriate Keycloak-issued access tokens.
- Protected endpoints remain protected.
- Preserve existing roles/claims.
- Login, token/session behaviour and logout must work.
- Local Keycloak users are bootstrap identities for initial deployment validation.
- `authMode: none` may remain for development/test if useful, but is not the EKS target.

Inspect existing authentication before changing it and preserve working behaviour wherever possible.

## 4. Keycloak realm/bootstrap handover

Inspect the existing `gamestory-sso` realm and produce a sanitized deployable realm/client configuration or equivalent documented bootstrap mechanism.

It must contain no real passwords, client secrets, Schneider secrets, private keys or confidential environment credentials.

Document:
- realm name;
- clients/client types;
- redirect URI requirements;
- web origins where applicable;
- roles;
- required claims/mappers;
- token expectations;
- bootstrap administrator handling;
- local-user creation procedure;
- deployment-time configuration/secrets.

Never bake credentials into the image or committed realm export.

## 5. Bootstrap users

Provide a safe administrative mechanism to create/reset initial local users after deployment.

Do not ship fixed production passwords in Git or OCI images. Where practical, require password change on first login.

Validate:
- login;
- OIDC redirect/callback;
- token issuance;
- API token validation;
- role/claim propagation;
- protected endpoint access;
- rejection of unauthorised requests;
- logout.

## 6. Schneider IdP transition

Prepare the current architecture so Schneider IdP can subsequently become an upstream Keycloak identity provider:

```text
Schneider IdP
      v
Keycloak Identity Broker
      v
Keycloak-issued application token
      v
LogAI
```

Do not implement or invent Schneider-specific credentials until supplied.

Document future configuration points:
- issuer/discovery endpoint;
- client ID;
- secret/certificate mechanism;
- redirect URI;
- claim mapping;
- group/role mapping;
- username/email mapping;
- logout behaviour.

The application-facing OIDC contract should remain stable when federation is introduced.

## 7. SynQ and downstream authentication boundary

**Keycloak authenticates people into LogAI. It does not automatically authenticate LogAI to SynQ.**

```text
User
  | Keycloak token
  v
LogAI
  | business operation
  v
Autobahn / integration layer
  | SynQ-specific machine authentication
  v
SynQ
```

Do not automatically forward an end-user Keycloak token to SynQ, WMS, PLC systems or other downstream services.

Each downstream connector must use the authentication mechanism required by that target, potentially:
- OAuth2 client credentials;
- service/workload identity;
- mTLS;
- API credentials;
- Basic authentication where unavoidable;
- another Schneider-approved mechanism.

The exact SynQ mechanism is deliberately not decided here; confirm it with Schneider/SynQ.

## 8. Human identity vs technical identity

Keep these separate.

**Human/business identity** identifies who initiated/approved the action, e.g. user subject, username and roles.

**Technical identity** is the machine credential used for the outbound integration, e.g. LogAI/Autobahn service identity, SynQ OAuth client or mTLS certificate.

They must not be treated as interchangeable.

## 9. Audit context

When an authenticated user causes a downstream operation, preserve audit context through LogAI/Autobahn.

Support a model capable of carrying:
- correlationId;
- requestId;
- initiating user/subject;
- source service;
- target system;
- operation;
- timestamp.

Do not expose the user's Keycloak access token merely for auditability. Never log access tokens or secrets.

Desired trace:

```text
User X
 -> LogAI operation Y
 -> decision/function Z
 -> Autobahn outbound operation
 -> SynQ API operation A
```

The actual SynQ request still uses its approved machine credential.

## 10. SynQ readiness

Ensure the authentication architecture does not couple SynQ integration to Keycloak.

Use or introduce a clean connector-authentication abstraction if required so the eventual SynQ mechanism can be supplied without changing human authentication.

Do not implement speculative SynQ authentication.

Document information required from SynQ/Schneider:
- authentication mechanism;
- token endpoint if applicable;
- credential type;
- provisioning/rotation;
- certificate requirements;
- scopes/roles;
- token lifetime;
- endpoint/base URL;
- TLS requirements;
- per-environment credentials;
- required correlation/audit headers.

## 11. Secrets

All authentication secrets remain runtime secrets.

Never store them in Git, Dockerfiles, Nuitka binaries, frontend JavaScript, OCI images, committed realm exports or logs.

This applies to Keycloak/Schneider IdP credentials and downstream credentials such as SynQ.

## 12. Interaction with v0.1.5 hardening

Do not weaken the existing v0.1.5 requirements:
- Nuitka compilation for proprietary Python APIs;
- source-free API runtime images;
- production-only Next.js UI;
- API UID 10001;
- UI UID 1000;
- read-only root filesystem;
- explicit writable paths;
- source-leak verification;
- Trivy/SBOM/release evidence.

Authentication configuration remains external to immutable images.

## 13. Schneider ownership boundary

Codex must not create or modify Schneider's Helm chart or Argo CD configuration.

Gamestory provides the runtime contract Schneider needs, including:
- Keycloak image/version;
- ports;
- realm/bootstrap mechanism;
- persistence/database requirements;
- environment variables;
- secret requirements;
- LogAI OIDC issuer/base URL;
- redirects/callbacks;
- health/readiness endpoints;
- writable filesystem requirements;
- bootstrap procedure;
- future Schneider IdP integration points.

Schneider translates this contract into Helm/Argo/EKS.

## 14. Codex execution approach

### Phase 1 — Inspect
Inspect current Keycloak configuration, `gamestory-sso` realm, UI authentication, Identity API, LogAI API token validation, `authMode`, roles/claims, Compose configuration, existing Entra broker configuration and any embedded secrets.

### Phase 2 — Report
Before broad changes, report:
- current auth flow;
- what already supports local Keycloak users;
- changes actually required;
- realm sanitization needs;
- Entra coupling;
- downstream-auth coupling;
- smallest robust implementation.

Do not rewrite working authentication unnecessarily.

### Phase 3 — Implement
Implement only what is required for Keycloak-local authentication to become the supported initial EKS mode and for clean subsequent Schneider IdP federation.

### Phase 4 — Validate
Run positive and negative authentication tests.

### Phase 5 — Handover
Produce the concise runtime/configuration contract Schneider needs for its Helm chart and Argo CD onboarding.

## 15. Acceptance criteria

The solution must demonstrate:
1. Keycloak starts without Schneider IdP connectivity.
2. A locally created Keycloak user can authenticate.
3. LogAI UI completes OIDC login.
4. Keycloak issues the expected token.
5. Protected LogAI APIs accept valid tokens.
6. Missing/invalid tokens are rejected.
7. required roles/claims are preserved.
8. Logout works.
9. Phase 1 requires no Schneider IdP credential.
10. No secret is embedded in source/image/frontend.
11. `authMode: none` is not required for EKS.
12. Downstream integration does not require forwarding the user's Keycloak token.
13. SynQ authentication can be supplied independently when confirmed.

## 16. Definition of Done

```text
INITIAL EKS

Local Keycloak User
        v
     Keycloak
        | OIDC/JWT
        v
      LogAI


SSO INTEGRATION

Schneider User
        v
Schneider IdP
        v
     Keycloak
        | same OIDC/JWT boundary
        v
      LogAI


DOWNSTREAM INTEGRATION

Authenticated User
        v
      LogAI
        | user/audit context
        v
    Autobahn
        | independent machine credential
        v
      SynQ
```

**Architectural rule:** Keycloak authenticates human users into LogAI. Downstream systems use service-specific machine identities. Human identity may flow as audit context, but human access tokens are not automatically forwarded downstream.
