# Schneider handoff

## Delivered artifact

Schneider receives the versioned `platform-bundle-*` image from `docker.io/chrismdgs/gamestory_logai_schneider`. Extract it with Podman or Docker as described in `docs/platform-bundle.md`. The extracted artifact contains no application source or Gamestory build/release environments.

## Client-local

Copy `environments/client-local/compose.env.example` to the ignored `compose.env`, replace local password placeholders, and run `scripts/deploy-compose.sh`. This pulls three released application images and Postgres from Docker Hub plus the pinned Keycloak image from Quay.

## UAT and production

Schneider must provide:

- JFrog-imported application repositories and approved immutable digests
- Kubernetes EKS cluster contexts, namespaces, workload identity, and pull-secret integration
- DNS, ingress configuration, and certificate handling
- AWS RDS for PostgreSQL endpoints, databases, users, CA/TLS requirements, and managed Secrets containing `password` and `databaseUrl`
- Keycloak administrator Secrets containing `username` and `password`
- Identity protocol, public URLs, client identifiers, and optional Entra secret references
- Resource sizing, replica policy, monitoring, backup, and rollback procedures

Create a private override file outside this repository, run `aws eks update-kubeconfig`, confirm the target context, then deploy:

```bash
export ALLOW_SCHNEIDER_DEPLOY=yes
./scripts/deploy-kubernetes.sh uat /secure/path/uat-private-values.yaml
./scripts/deploy-kubernetes.sh prod /secure/path/prod-private-values.yaml
```

Never store credentials in the bundle or environment values files. Production deployment requires Schneider change approval and is not performed by Gamestory packaging CI.
