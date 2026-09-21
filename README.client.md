# Schneider LogAI deployment bundle

This client-only release archive contains three environments:

- `client-local`: Podman or Docker Compose with bundled Postgres
- `uat`: Helm/Kubernetes with AWS RDS PostgreSQL
- `prod`: Helm/Kubernetes with AWS RDS PostgreSQL

It is distributed as a ZIP, not a runnable image. It contains no application source, source build contexts, Gamestory build environment, or Gamestory release environment. Application images are pulled from Docker Hub. Keycloak is pulled from Quay at a pinned digest.

Start with `docs/client-local.md` for workstation deployment and `docs/schneider-handoff.md` for UAT/production prerequisites.
