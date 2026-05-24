# Schneider Logai + Identity Integration Bits

This is the working inventory for bringing the Schneider platform stack together from:

- `C:\chris\workspace\gamestory\logai_ai`
- `C:\chris\workspace\gamestory\gamestory-identity-kit`

No real Schneider secrets should be committed here. Keep this document to placeholders, required values, file references, and setup sequence.

## Target Public URLs

Request two DNS names for the deployed environment:

```text
LOGAI_PUBLIC_URL=https://<logai-app-host>
KEYCLOAK_PUBLIC_URL=https://<logai-auth-host>
```

Expected routing:

```text
https://<logai-app-host>  -> Logai UI
https://<logai-auth-host> -> Keycloak
```

Keycloak must use the same public auth hostname that users and Entra see. Do not configure browser-facing OIDC flows with an internal Keycloak hostname.

## Logai UI Bits

Source module:

```text
C:\chris\workspace\gamestory\logai_ai
```

Key files:

```text
.env.example
src\auth\config.ts
src\auth\authClient.ts
src\auth\AuthProvider.tsx
src\auth\identityApi.ts
src\components\auth\AuthStatusOverlay.tsx
src\features\auth\LogaiAuthLanding.tsx
src\app\page.tsx
```

Runtime values needed for Schneider SSO mode:

```text
NEXT_PUBLIC_AUTH_MODE=sso
NEXT_PUBLIC_AUTH_URL=https://<logai-auth-host>
NEXT_PUBLIC_AUTH_REALM=<keycloak-realm>
NEXT_PUBLIC_AUTH_CLIENT_ID=<logai-keycloak-client-id>
NEXT_PUBLIC_AUTH_IDP_HINT=<schneider-idp-alias>
NEXT_PUBLIC_AUTH_CALLBACK_URL=https://<logai-app-host>/auth/callback
NEXT_PUBLIC_IDENTITY_API_BASE_URL=https://<identity-api-host>
```

Current local defaults:

```text
NEXT_PUBLIC_AUTH_MODE=none
NEXT_PUBLIC_AUTH_URL=http://localhost:8080
NEXT_PUBLIC_AUTH_REALM=gamestory-sso
NEXT_PUBLIC_AUTH_CLIENT_ID=sample-ui
NEXT_PUBLIC_AUTH_IDP_HINT=gamestory-entra
NEXT_PUBLIC_AUTH_CALLBACK_URL=http://sample.localhost:3000/auth/callback
NEXT_PUBLIC_IDENTITY_API_BASE_URL=http://localhost:8000
```

Logai is a public OIDC client of Keycloak. It should not store a client secret in the browser app.

## Identity Module Bits

Source module:

```text
C:\chris\workspace\gamestory\gamestory-identity-kit
```

Key files:

```text
docker-compose.yml
keycloak\realms\gamestory-sso-realm.json
config\identity\identity.customer.env.example
config\identity\oidc-idp.template.json
config\identity\saml-idp.template.json
scripts\validate-customer-identity-config.ps1
scripts\render-idp-template.ps1
backend\app\main.py
backend\app\config.py
backend\app\auth
```

Schneider-specific platform files:

```text
identity\schneider.identity.env.example
docs\schneider-identity.md
```

Identity config values needed from Schneider / Entra:

```text
CUSTOMER_IDP_PROTOCOL=oidc
CUSTOMER_IDP_ALIAS=schneider-main
OIDC_ISSUER_URL=
OIDC_AUTHORIZATION_URL=
OIDC_TOKEN_URL=
OIDC_USERINFO_URL=
OIDC_JWKS_URL=
OIDC_CLIENT_ID=
OIDC_CLIENT_SECRET=
OIDC_SCOPES=openid profile email
OIDC_CLIENT_AUTH_METHOD=client_secret_post
CLAIM_EMAIL=email
CLAIM_DISPLAY_NAME=name
CLAIM_GROUPS=groups
```

If Schneider provides SAML instead of OIDC, fill the SAML section in `identity\schneider.identity.env.example` and leave OIDC empty.

## Keycloak Client Needed For Logai

Create or update one Keycloak client for the Logai UI:

```text
Client ID: <logai-keycloak-client-id>
Client type: public
Standard flow: enabled
PKCE: S256
Valid redirect URIs:
  https://<logai-app-host>/auth/callback
Web origins:
  https://<logai-app-host>
Post logout redirect URIs:
  https://<logai-app-host>/*
```

The existing local realm has `sample-ui`; Schneider deployment should use a Schneider/Logai-specific client id instead of `sample-ui`.

## Entra Registration Needed For Schneider Broker

If Schneider uses Entra via Keycloak identity brokering, Entra redirects back to Keycloak, not directly to the Logai app.

Register this redirect URI in Entra:

```text
https://<logai-auth-host>/realms/<keycloak-realm>/broker/<schneider-idp-alias>/endpoint
```

For the current placeholders:

```text
https://<logai-auth-host>/realms/gamestory-sso/broker/schneider-main/endpoint
```

## Assembly Sequence

1. Confirm public DNS names for Logai UI and Keycloak.
2. Confirm Schneider identity protocol: OIDC or SAML.
3. Fill a private copy of `identity\schneider.identity.env.example`.
4. Validate the Schneider identity env with `gamestory-identity-kit\scripts\validate-customer-identity-config.ps1`.
5. Render the Keycloak IdP snippet with `gamestory-identity-kit\scripts\render-idp-template.ps1`.
6. Create/update the Keycloak realm with:
   - Schneider IdP alias.
   - Logai public OIDC client.
   - Correct redirect URI and web origin.
7. Deploy Logai UI with `NEXT_PUBLIC_AUTH_MODE=sso` and the Schneider values above.
8. Smoke test:
   - Open Logai public URL.
   - Trigger login.
   - Confirm browser redirects to Keycloak public URL.
   - Confirm Keycloak brokers to Schneider/Entra.
   - Confirm redirect returns to `/auth/callback`.
   - Confirm `AuthStatusOverlay` can call identity API `/me`.

## Open Decisions

```text
Logai public hostname:
Keycloak public hostname:
Keycloak realm name:
Logai Keycloak client id:
Identity API public hostname:
Schneider IdP protocol:
Schneider IdP alias:
Required claims/groups:
Logout behavior:
Environment owner:
```
