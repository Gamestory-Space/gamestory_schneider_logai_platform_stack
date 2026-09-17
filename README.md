# Gamestory Schneider LogAI Platform Stack

Canonical deployment repository for Postgres, Keycloak, Identity API, LogAI API, and LogAI UI. Helm is authoritative across all five source-repository environments. The published client bundle contains only client-local, UAT, and production assets.

| Environment | Owner | Helm | Compose |
| --- | --- | --- | --- |
| build | Gamestory | Yes | Yes, source-build override |
| release | Gamestory | Yes | Yes, pull only |
| client-local | Schneider/local | Yes | Yes, pull only |
| uat | Schneider | Yes | No |
| prod | Schneider | Yes | No |

## Validate

```bash
./scripts/helm-lint.sh
./scripts/helm-template.sh
./scripts/validate-client-bundle.sh

docker compose -f compose.yaml -f compose.build.yaml --env-file environments/build/compose.env.example config
docker compose -f compose.yaml --env-file environments/release/compose.env.example config
docker compose -f compose.yaml --env-file environments/client-local/compose.env.example config
```

## Test

```bash
# WSL2 + Podman local test
cp environments/client-local/compose.env.example environments/client-local/compose.env
./scripts/test-wsl-podman.sh

# Gamestory local Kubernetes release test, after checking the active context
ALLOW_LOCAL_K8S_DEPLOY=yes ./scripts/test-local-kubernetes.sh release
```

## Build or deploy with Compose

```bash
# Gamestory source build
docker compose -f compose.yaml -f compose.build.yaml --env-file environments/build/compose.env.example up -d --build

# Pull-only release or client-local
docker compose -f compose.yaml --env-file environments/release/compose.env up -d --no-build
docker compose -f compose.yaml --env-file environments/client-local/compose.env up -d --no-build
```

## Helm

```bash
helm upgrade --install logai ./helm/gamestory-schneider-platform --namespace logai --create-namespace -f environments/client-local/values.yaml
```

See `docs/testing.md`, `docs/platform-bundle.md`, `docs/deployment-model.md`, and `docs/schneider-handoff.md`.
