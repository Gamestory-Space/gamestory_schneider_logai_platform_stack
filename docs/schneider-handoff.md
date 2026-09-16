# Schneider handoff

Schneider must supply or confirm:

- JFrog image repositories and approved tags/digests
- GKE project, cluster, namespace, workload identity, and pull-secret integration
- UAT/production DNS, GCE ingress annotations, and certificate handling
- External Postgres hosts, databases, users, and managed secret names
- Keycloak administrator secret references
- Identity protocol, public URLs, client identifiers, and optional Entra secret references
- Production resource sizing, replica policy, monitoring, and rollback procedure

No credentials belong in this repository. UAT and production overlays contain placeholders and secret names only.
