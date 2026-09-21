# Deployment model

## Source repository

| Environment | Owner/location | Helm | Compose |
| --- | --- | --- | --- |
| build | Gamestory WSL2 | Local Kubernetes | Yes, source-build override |
| release | Gamestory WSL2 | Local Kubernetes | Yes, pull only |
| client-local | Schneider AWS validation host | Optional | Yes, pull only |
| uat | Schneider AWS | EKS | No |
| prod | Schneider AWS | EKS | No |

## Client bundle

The Docker Hub generic OCI deployment archive deliberately contains only `client-local`, `uat`, and `prod`. Client-local deploys Postgres as a container. UAT and production deploy no Postgres pod and connect to Schneider-managed AWS RDS PostgreSQL through runtime Secret references.

Configuration precedence is chart defaults, environment values, Schneider/private delivery overrides, then runtime Secrets.
