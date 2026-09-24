# Schneider LogAI — Decisions

Classification: **GAMESTORY CONFIDENTIAL INTERNAL ENGINEERING MATERIAL**

## DB-001 — Controlled database migrations

Status: APPROVED  
Date: 2026-09-24

Decision: UAT and production schema evolution uses explicit version-controlled migrations, not application-pod automatic schema creation.

Rationale: Schema evolution must be controlled, repeatable, auditable, and separate from horizontally scaled application startup.

Consequences: Startup schema application remains disabled in UAT/production; migrations become a release prerequisite.

Related Discussions: `DISC-DB-001`

## DB-002 — Migration engine

Status: APPROVED  
Date: 2026-09-24

Decision: Use Flyway.

Consequences: Migration versions and Flyway schema history govern execution order and repeatability.

Related Discussions: `DISC-DB-001`

## DB-003 — Migration artifact

Status: APPROVED  
Date: 2026-09-24

Decision: Package migrations in a dedicated immutable OCI image associated with the LogAI release.

Consequences: UAT and production promote the same migration artifact digest.

Related Discussions: `DISC-DB-001`

## DB-004 — Migration execution

Status: APPROVED  
Date: 2026-09-24

Decision: Execute Flyway through an Argo CD `PreSync` Kubernetes Job before application rollout. Migration failure prevents rollout.

Consequences: The Job must be idempotent and use externally available database credentials; application pods do not own migration execution.

Related Discussions: `DISC-DB-001`

## DB-005 — Migration repository ownership

Status: APPROVED  
Date: 2026-09-24

Decision: Migration source belongs to the Schneider platform release mechanism. Do not create a separate database repository at this stage.

Related Discussions: `DISC-DB-001`

## DB-006 — Production data preservation

Status: APPROVED  
Date: 2026-09-24

Decision: Progressive releases preserve operational data by default using expand, migrate/backfill, compatible application deployment, verification, and later contract. Destructive changes require explicit recovery planning.

Related Discussions: `DISC-DB-001`

## DB-007 — Keycloak and LogAI database isolation

Status: PROPOSED  
Date: 2026-09-24

Decision: Consider separate databases or schemas and separate credentials for Keycloak and LogAI within the same RDS infrastructure.

Rationale: Separate ownership and least privilege appear preferable, but the CTO has not approved a topology.

Related Discussions: `DISC-DB-002`

## DEPLOY-001 — Git-driven UAT and production promotion

Status: APPROVED  
Date: 2026-09-24

Decision: Use two client-owned Argo CD Applications. UAT automatically tracks `main`; production automatically tracks protected branch `production`. Promote the validated implementation from `main` to `production` through an approved merge.

Consequences: GitHub Actions does not deploy or call Argo CD. Git review is the production promotion gate.

Related Discussions: `DISC-DEPLOY-001`

## RELEASE-001 — Internal direction isolation

Status: APPROVED  
Date: 2026-09-24

Decision: Keep agent/project context only on `project-direction`; never merge it to implementation/release branches or transfer Gamestory Git history to Schneider. Construct client delivery from an explicit allow-list and hard-fail on leakage.

Related Discussions: `DISC-AGENT-001`, `DISC-RELEASE-001`
