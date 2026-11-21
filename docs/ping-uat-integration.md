# Schneider Ping UAT integration

Prepared for client-site testing; no provider has been enabled remotely.
The client reports that the redirect URI is registered. The secret stays at the client site.

## Minimal defaults agreed on 21 November 2026

- Client: `logai_68225_uat`; Keycloak realm `gamestory-sso`; alias `schneider-main`.
- Redirect: `https://logai-auth-uat.se.com/realms/gamestory-sso/broker/schneider-main/endpoint`.
- Token authentication: `client_secret_basic`. Change to `client_secret_post` if the client test requires it.
- Scope: `openid`, required for OIDC. Optional `profile`/`email` scopes, extra claims,
  PKCE configuration, upstream logout and group/role mappings are unset.
- Provider disabled until explicit enablement; signature/JWKS validation on,
  email trust and token storage off. No automatic IdP redirect or account linking.

These are configurable integration defaults selected by the user, not a claim that
Ping has confirmed this client's assigned settings. Discovery checked on 16 November
advertised Basic/POST and the supplied endpoints. Initial login now proceeds with
these defaults rather than waiting for another configuration questionnaire.

[OAuth client password authentication](https://www.rfc-editor.org/rfc/rfc6749#section-2.3.1)
and [OIDC authentication request scopes](https://openid.net/specs/openid-connect-core-1_0.html#AuthRequest)
provide the protocol basis. No optional scopes or claim mappings are invented.

## Render at the client site

Use the extracted client bundle on its secured operator workstation. In the source
repository the script is `scripts/client/render-ping-provider.sh`.

```bash
umask 077
mkdir -p identity/generated
bash scripts/render-ping-provider.sh \
  --client-secret-file /secure/path/ping-client-secret \
  --output identity/generated/ping-uat.private.json
```

Only the secret file and output are required. This writes a disabled provider with
Basic and `openid`; add `--enable` for the enabled configuration. Optional overrides:
`--client-auth-method client_secret_post` or `--scopes 'openid profile email'`.
Keep optional settings unset unless testing establishes a need. Explicitly invalid
or empty authentication methods/scopes are rejected. Output is 0600, never printed,
and cannot overwrite an existing file or symlink. No network call is made.

If `schneider-main` exists, back it up first and pass
`--existing-provider-file identity/generated/ping-uat.before.private.json`.
This preserves its internal identity and additional configuration; mappers remain
in Keycloak through a targeted update. Review existing mappings on site.

## Targeted enablement

Use an already authenticated UAT admin CLI session targeting
`https://logai-auth-uat.se.com`. Keep the admin session and every generated/exported
file private. Retain the original secret securely; exported secrets can be masked.

```bash
kcadm.sh get identity-provider/instances/schneider-main -r gamestory-sso \
  > identity/generated/ping-uat.before.private.json

bash scripts/render-ping-provider.sh \
  --client-secret-file /secure/path/ping-client-secret \
  --existing-provider-file identity/generated/ping-uat.before.private.json \
  --enable --output identity/generated/ping-uat.enabled.private.json

kcadm.sh update identity-provider/instances/schneider-main -r gamestory-sso \
  -f identity/generated/ping-uat.enabled.private.json
```

For a missing provider, omit the backup argument and use `kcadm.sh create
identity-provider/instances -r gamestory-sso -f ...` instead. Do not import a whole
realm. Preserve local administrator login and leave automatic redirection off.

## Client-site acceptance

Test LogAI → Keycloak → Ping → Keycloak → LogAI with an assigned user. Check the
Keycloak-issued application audience and an existing approved canonical LogAI role
(`as-lead` or `logai-admin`); successful Ping authentication alone grants no role.
Use the existing controlled Keycloak provisioning/mappings. No automatic mapping
is added without an agreed business role. An `openid`-only login may require the
user to complete the normal Keycloak profile form.

If Ping returns `invalid_client`, retry with the POST override after inspecting the
error. If additional profile claims are needed, add only the necessary supported
scope. Never disable signature validation, trust email, or grant admin to bypass a
failed test. Verify unassigned-user denial, explicit account linking, protected API
access, local administrator recovery and application logout. Upstream Ping logout
stays unset unless required. For rollback disable just this provider or restore
its reviewed configuration, retaining existing mappers and local users.
