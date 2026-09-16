# Client-local deployment

Compose on Docker Desktop:

```bash
cp environments/client-local/compose.env.example environments/client-local/compose.env
docker compose --env-file environments/client-local/compose.env pull
docker compose --env-file environments/client-local/compose.env up -d --no-build
```

Helm on local Kubernetes or GKE:

```bash
helm upgrade --install logai ./helm/gamestory-schneider-platform --namespace logai --create-namespace -f environments/client-local/values.yaml
```

Replace example image references and local-only placeholder passwords outside source control.
