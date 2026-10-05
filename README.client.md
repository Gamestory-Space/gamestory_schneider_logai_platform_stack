# v0.1.7 credential behavior

See [login defaults](docs/login-defaults.md) for the current default passwords and overrides. The earlier shared temporary-password requirements below apply only when shared mode is selected.

# Schneider LogAI deployment bundle

This client-only release archive contains four environments:

- `client-local`: Podman or Docker Compose with bundled Postgres
- `dev-aws`: Helm/Kubernetes with AWS RDS PostgreSQL
- `uat`: Helm/Kubernetes with AWS RDS PostgreSQL
- `prod`: Helm/Kubernetes with AWS RDS PostgreSQL

It is distributed as a ZIP, not a runnable image. It contains no application source, source build contexts, Gamestory build environment, or Gamestory release environment. Application images are pulled from Docker Hub. Keycloak is pulled from Quay at a pinned digest.

Start with `docs/client-local.md` for workstation deployment and `docs/schneider-handoff.md` for UAT/production prerequisites.

Initial authentication uses Keycloak local users. Deployment automatically reconciles the realm, clients, roles, groups and configured bootstrap users through the shared compiled reconciler. Supply the runtime bootstrap password and follow [the identity runtime contract](docs/keycloak-bootstrap-runtime-contract.md). Existing passwords and account state are preserved.

For UAT and production rollout, follow [the deployment runbook](docs/uat-prod-deployment-runbook.md).

See [image licensing](docs/image-licensing.md): LogAI-owned code uses the proprietary licence; Keycloak, PostgreSQL and dependencies retain their upstream licences.

For Schneider site configuration, see [UAT/production configuration requirements](docs/client-uat-prod-configuration.md).
