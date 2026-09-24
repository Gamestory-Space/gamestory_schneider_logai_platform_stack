# Helm overrides

The chart uses this configuration hierarchy:

```text
chart defaults -> environment values -> deployment/CD overrides -> runtime secrets
```

Exactly five canonical overlays are committed:

- `build` and `release`, owned by Gamestory
- `client-local`, `uat`, and `prod`, owned by Schneider/client operations

All five support Helm deployment. Build and release target local Kubernetes in WSL2; client-local may also target local Kubernetes; UAT and production target AWS EKS and use Schneider-managed AWS RDS for PostgreSQL and managed secret references; their example registry, DNS, ingress, database, and secret identifiers must be replaced by Schneider values.

```bash
helm upgrade --install logai ./helm/gamestory-schneider-platform \
  --namespace logai --create-namespace \
  -f environments/<environment>/values.yaml
```

Use CI/CD `--set` or an additional private values file for deployment-specific references. Never store credentials in an environment values file. `remote-build-dev` is deprecated and retained only as migration history.

## GitHub Actions deployment to EKS

The `Deploy Platform to EKS` workflow pulls a versioned platform ZIP from Docker Hub, verifies its SHA-256 checksum, assumes an AWS role using GitHub OIDC, and deploys the selected UAT or production overlay with Helm. Configure GitHub environments named `uat` and `prod`; use required reviewers on `prod`.

Set these variables in each GitHub environment:

- `AWS_REGION`: AWS region containing the EKS cluster
- `EKS_CLUSTER_NAME`: target EKS cluster name
- `HELM_NAMESPACE`: optional; defaults to `logai-uat` or `logai-prod`

Set these environment secrets:

- `AWS_ROLE_ARN`: IAM role trusted by this repository's GitHub OIDC identity and authorized for the EKS cluster
- `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN`: read-only access to the generic OCI artifact
- `HELM_PRIVATE_VALUES`: complete private Helm values YAML containing the real registry, ingress, RDS, and existing Kubernetes Secret references

Run the workflow manually and select the environment and released platform version. The workflow deploys the resolved OCI digest and uses Helm `--atomic`, so a failed upgrade is rolled back automatically.
