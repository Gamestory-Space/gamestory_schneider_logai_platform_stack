# v0.1.7 credential behavior

See [login defaults](login-defaults.md) for the current default passwords and overrides. The earlier shared temporary-password requirements below apply only when shared mode is selected.

# Schneider client-local deployment

Client-local runs five permanent containers: Postgres, Keycloak, Identity API, LogAI API, and LogAI UI, plus a finite identity-bootstrap job on each deployment. Application images come from Docker Hub; Keycloak is pinned by Quay digest.

## Podman on WSL2 or client workstation

```bash
cp environments/client-local/compose.env.example environments/client-local/compose.env
# Set POSTGRES_PASSWORD, KEYCLOAK_ADMIN_PASSWORD and KEYCLOAK_LOGAI_BOOTSTRAP_PASSWORD in this runtime-only file.
./scripts/deploy-compose.sh environments/client-local/compose.env
```

In the source repository the equivalent script is `scripts/client/deploy-compose.sh`. It selects Podman when available, otherwise Docker. Deployment always uses `--no-build`; no Gamestory source repository is required.

Check:

```bash
curl --fail http://localhost:8000/health
curl --fail http://localhost:8010/health
curl --fail http://localhost:3000/
curl --fail http://localhost:8080/realms/gamestory-sso/.well-known/openid-configuration
```

The deployment wrapper always reruns identity reconciliation and stops before starting/updating applications if it fails. Existing user passwords and disabled state are preserved. See [the identity runtime contract](keycloak-bootstrap-runtime-contract.md).
