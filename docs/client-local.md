# Schneider client-local deployment

Client-local deploys five containers: Postgres, Keycloak, Identity API, LogAI API, and LogAI UI. Application images come from Docker Hub; Keycloak is pinned by Quay digest.

## Podman on WSL2 or client workstation

```bash
cp environments/client-local/compose.env.example environments/client-local/compose.env
# Set unique local POSTGRES_PASSWORD and KEYCLOAK_ADMIN_PASSWORD values.
./scripts/deploy-compose.sh environments/client-local/compose.env
```

In the source repository the equivalent script is `scripts/client/deploy-compose.sh`. It selects Podman when available, otherwise Docker. Deployment always uses `--no-build`; no Gamestory source repository is required.

Check:

```bash
curl --fail http://localhost:8000/health
curl --fail http://localhost:8010/health
curl --fail http://localhost:3000/
curl --fail http://localhost:8080/health/ready
```
