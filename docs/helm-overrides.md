# Helm overrides

The chart uses this configuration hierarchy:

```text
chart defaults -> environment values -> deployment/CD overrides -> runtime secrets
```

Exactly six canonical overlays are committed:

- `build` and `release`, owned by Gamestory
- `client-local`, `dev-aws`, `uat`, and `prod`, owned by Schneider/client operations

All six support Helm deployment. Build and release target local Kubernetes in WSL2; client-local may also target local Kubernetes; Dev AWS, UAT, and production target AWS EKS and use Schneider-managed AWS RDS for PostgreSQL and managed secret references; their example registry, DNS, ingress, database, and secret identifiers must be replaced by Schneider values.

```bash
helm upgrade --install logai ./helm/gamestory-schneider-platform \
  --namespace logai --create-namespace \
  -f environments/<environment>/values.yaml
```

Use CI/CD `--set` or an additional private values file for deployment-specific references. Never store credentials in an environment values file. `remote-build-dev` is deprecated and retained only as migration history.

## Existing service account

Set `global.serviceAccountName` to an existing Kubernetes ServiceAccount in the release namespace. It applies to the application Deployments, Keycloak, the PostgreSQL StatefulSet when enabled, and the identity bootstrap Job. An empty value omits `serviceAccountName`, retaining the Kubernetes default. The chart does not create or annotate the account or grant AWS permissions. UAT selects `logai-srv-uat`; production remains unset pending its account name. Existing token automount settings are preserved. Selecting an account alone does not fetch Secrets Manager values or synchronize a Kubernetes Secret; configure that integration separately.
