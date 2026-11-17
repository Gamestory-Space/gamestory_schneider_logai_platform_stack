# Schneider Ping UAT integration

Status (16 November 2026): client reports redirect registration complete. Ping public
discovery is reachable and confirms the issuer and OIDC support. Live UAT provider
state has not been inspected or changed; this environment cannot resolve the UAT
Keycloak hostname and has no client UAT admin connection. Existing local Keycloak authentication
and application token validation stay in place.

## Client support email draft

Subject: LogAI UAT – Ping SSO configuration confirmations

Hi team,

Thank you for the UAT client and OAuth endpoint details. For client
`logai_68225_uat`, please register this exact redirect URI:

`https://logai-auth-uat.se.com/realms/gamestory-sso/broker/schneider-main/endpoint`

We will integrate Ping through our Keycloak identity broker. Could you please
confirm the following so we can complete configuration and UAT testing?

1. Does this client support OpenID Connect Authorization Code Flow, including
   the `openid` scope and signed ID tokens? Please provide the discovery URL
   and exact issuer value.
2. Which scopes are approved for this client (for example `openid profile email`),
   and which token endpoint client authentication method is configured
   (`client_secret_basic`, `client_secret_post`, or another method)? Is PKCE
   required, and if so which method?
3. Which claims are returned in the ID token and/or userinfo response for the
   stable user identifier, email, email verification, first name and surname?
   A redacted example payload would help.
4. How will LogAI access be restricted to approved users? If Ping supplies
   groups or application roles, please provide the claim name, value format,
   and agreed group/role values. We can then agree the LogAI role mapping.
5. Is logout expected to end only the LogAI session or also the Ping SSO session?
   If Ping logout is required, please provide the supported logout endpoint and
   any post-logout redirect registration requirements.
6. Are network allowlists or private connectivity required from our UAT
   environment to the token, userinfo and JWKS endpoints? Please also confirm
   an assigned UAT test user and a contact for a joint login test.

Please confirm once the redirect URI is registered. We will arrange secure
provisioning of the full client secret separately; please do not include it in
the email reply.

Thanks,
Chris

## Prepared configuration

`identity/ping-uat.json` contains the supplied public endpoints and client ID.
Issuer is verified from discovery. Scopes and the client authentication method still
require the client-specific settings; server discovery advertises capabilities, not
the configuration of this particular client. The provider
is disabled, signature validation is enabled, email is not automatically trusted,
and upstream tokens are not stored. No automatic account linking or role/group
mappers have been added. Revocation and introspection endpoints are not used as
logout endpoints. Keycloak continues issuing the tokens consumed by LogAI.

After support confirms OIDC and the missing settings, render a private provider
file from the extracted client bundle (replace the example arguments with confirmed values). In the source repository the helper is `scripts/client/render-ping-provider.sh`:

```bash
mkdir -p identity/generated
bash scripts/render-ping-provider.sh \
  --issuer 'https://CONFIRMED-ISSUER' \
  --scopes 'openid profile email' \
  --client-auth-method client_secret_basic \
  --client-secret-file /secure/path/ping-client-secret \
  --output identity/generated/ping-uat.private.json
```

The output is created with mode 0600, is ignored by Git, and contains the secret.
The renderer refuses to overwrite an existing file. It performs no network calls.
If Ping requires another authentication method or PKCE, extend configuration
before import; do not substitute unconfirmed settings.

An authenticated Keycloak administrator can create the provider using the Admin
CLI in an appropriately secured operator environment:

```bash
kcadm.sh create identity-provider/instances -r gamestory-sso \
  -f identity/generated/ping-uat.private.json
```

This creates a disabled provider. If the alias already exists, inspect and back
up its configuration securely before performing a targeted update; do not
re-import the complete realm. Check that the console displays the exact redirect
URI above. Complete claim/access mapping and approve the first-login/account-link
behavior before enabling the provider. Keep local administrator access available.
No default redirect to Ping or UI IdP hint is configured by this preparation.

## Acceptance before rollout

Verify an assigned user can sign in through Ping and return to LogAI with the
expected Keycloak-issued token and approved role. Verify an unassigned user is
denied, an existing local account cannot be silently linked by email, and missing
roles cannot access protected operations. Check local login still works and test
the agreed logout behavior. Never grant elevated roles merely because a user
successfully authenticates at Ping. End-to-end acceptance requires the deployed
UAT environment and real credentials; it has not been performed locally.

References: [Keycloak OIDC identity brokering](https://www.keycloak.org/docs/latest/server_admin/#_identity_broker)
and [Admin CLI provider management](https://github.com/keycloak/keycloak/blob/main/docs/documentation/server_admin/topics/admin-cli.adoc).


## On-site enablement after redirect registration

Verified on 16 November 2026 without credentials:

- Discovery: `https://ping-sso-uat.schneider-electric.com/.well-known/openid-configuration`
- Issuer: `https://ping-sso-uat.schneider-electric.com`
- Authorization/token/userinfo/JWKS endpoints match `identity/ping-uat.json`.
- Authorization Code flow and scopes `openid`, `profile`, `email` are advertised.
- Both `client_secret_basic` and `client_secret_post` are advertised, alongside other
  methods. This does not identify the method assigned to `logai_68225_uat`.

The client secret stays at the client site. Run the following from its secured operator
workstation and extracted client bundle, with the client-approved scopes and authentication method. The example
uses Basic and `openid profile email`; substitute the actual client settings rather
than assuming discovery grants those settings to this client.

```bash
umask 077
mkdir -p identity/generated
bash scripts/render-ping-provider.sh \
  --issuer 'https://ping-sso-uat.schneider-electric.com' \
  --scopes 'openid profile email' \
  --client-auth-method client_secret_basic \
  --client-secret-file /secure/path/ping-client-secret \
  --enable \
  --output identity/generated/ping-uat.enabled.private.json
```

If `schneider-main` already exists, export it first with the authenticated UAT admin
session into a protected file, and add
`--existing-provider-file identity/generated/ping-uat.before.private.json` to the
renderer command. The renderer retains existing internal identity/unknown configuration,
replaces only the confirmed UAT connection/security fields and new secret, and rejects
a different alias/provider type/client ID. Existing claim/group mappers are retained by
the targeted provider update; review them on site. The first render above is appropriate
for a missing provider. No export or private generated file belongs in the archive.

This only creates an enabled **configuration file**, with mode 0600; it does not
connect to or change Keycloak. Without `--enable`, output remains disabled.

Using an already authenticated UAT Keycloak admin CLI session (configured for
`https://logai-auth-uat.se.com`), inspect the existing `schneider-main` provider and
securely back up its configuration before a targeted update. Retain its existing
claim/group mappers. Do not re-import the realm or change the default login flow.

```bash
# Existing provider: back up securely, then update only this provider.
kcadm.sh get identity-provider/instances/schneider-main -r gamestory-sso \
  > identity/generated/ping-uat.before.private.json
kcadm.sh update identity-provider/instances/schneider-main -r gamestory-sso \
  -f identity/generated/ping-uat.enabled.private.json

# If inspection confirms the provider does not exist, use create instead of update:
# kcadm.sh create identity-provider/instances -r gamestory-sso \
#   -f identity/generated/ping-uat.enabled.private.json
```

The CLI must target the UAT server; credentials and its admin-session file stay at the
client site. Exported secrets may be masked, so retain their original secure source
for rollback. Confirm alias `schneider-main`, enabled state, client ID and the exact
registered redirect URI in the console. Keep `trustEmail=false`, `storeToken=false`
and signature validation enabled. Leave automatic Ping redirection off for the first
test; use the Schneider Electric SSO button so local admin login remains available.

Test with an assigned UAT user: LogAI → Keycloak → Ping → Keycloak → LogAI. Check
Keycloak-issued application tokens and approved LogAI roles, plus denial for an
unassigned user and the agreed logout behaviour. Successful Ping authentication alone
must not grant an administrator role. An `invalid_scope` or `invalid_client` response
requires checking this client's assigned scopes/authentication method with the client
team; it is not evidence of a redirect-registration problem.
