# Helm overrides

The chart uses this configuration hierarchy:

```text
chart defaults -> environment values -> deployment/CD overrides -> runtime secrets
```

Exactly five canonical overlays are committed:

- `build` and `release`, owned by Gamestory
- `client-local`, `uat`, and `prod`, owned by Schneider/client operations

All five support Helm deployment to GKE. Client-local can also target local Kubernetes/k3s. UAT and production use external Postgres and managed secret references; their example registry, DNS, ingress, database, and secret identifiers must be replaced by Schneider values.

```bash
helm upgrade --install logai ./helm/gamestory-schneider-platform \
  --namespace logai --create-namespace \
  -f environments/<environment>/values.yaml
```

Use CI/CD `--set` or an additional private values file for deployment-specific references. Never store credentials in an environment values file. `remote-build-dev` is deprecated and retained only as migration history.
