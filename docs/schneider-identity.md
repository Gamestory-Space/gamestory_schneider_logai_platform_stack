# Schneider Identity Setup

This repo owns Schneider-specific identity values. Generic identity templates and validation scripts live in:

```text
C:\chris\workspace\gamestory\gamestory-identity-kit
```

## Workflow

1. Confirm Schneider protocol: `oidc` or `saml`.
2. Copy `identity/schneider.identity.env.example` to a private env file.
3. Fill only the matching protocol section.
4. Validate with the generic identity script.
5. Render the Keycloak IdP snippet.
6. Apply the IdP config to the Schneider Keycloak realm/deployment.
7. Set Logai UI `NEXT_PUBLIC_AUTH_IDP_HINT=schneider-main`.

## Validation

From `gamestory-identity-kit`:

```powershell
.\scripts\validate-customer-identity-config.ps1 `
  -EnvFile ..\platforms\schneider\gamestory_schneider_logai_platform_stack\identity\schneider.identity.env.example
```

Render a snippet:

```powershell
.\scripts\render-idp-template.ps1 `
  -EnvFile ..\platforms\schneider\gamestory_schneider_logai_platform_stack\identity\schneider.identity.env.example `
  -OutputPath ..\platforms\schneider\gamestory_schneider_logai_platform_stack\identity\generated\schneider-idp.json
```

Do not commit generated files that contain real Schneider secrets or certificates.
