# Gamestory Schneider LogAI Platform Stack

Canonical deployment repository for the five-workload Schneider LogAI first drop: Postgres, Keycloak, Identity API, LogAI API, and LogAI UI.

Helm is authoritative for all environments and supports GKE. Compose is a convenience path only for build, release, and client-local.

| Environment | Owner | Helm | Compose |
| --- | --- | --- | --- |
| build | Gamestory | Yes | Yes |
| release | Gamestory | Yes | Yes |
| client-local | Schneider/local | Yes | Yes |
| uat | Schneider | Yes | No |
| prod | Schneider | Yes | No |

## Validate

```bash
./scripts/helm-lint.sh
./scripts/helm-template.sh

docker compose --env-file environments/build/compose.env.example config
docker compose --env-file environments/release/compose.env.example config
docker compose --env-file environments/client-local/compose.env.example config
```

## Deploy

Build may build local source:

```bash
docker compose --env-file environments/build/compose.env.example build
docker compose --env-file environments/build/compose.env.example up -d
```

Release and client-local must use published artifacts:

```bash
docker compose --env-file environments/release/compose.env up -d --no-build
docker compose --env-file environments/client-local/compose.env up -d --no-build
```

Helm example:

```bash
helm upgrade --install logai ./helm/gamestory-schneider-platform --namespace logai --create-namespace -f environments/client-local/values.yaml
```

See `docs/deployment-model.md`, `docs/local-k3s.md`, and `docs/schneider-handoff.md`. SSO is optional for this delivery; existing `gamestory-sso`, `sample-ui`, and `gamestory-entra` names are retained as defaults without requiring Entra credentials.
