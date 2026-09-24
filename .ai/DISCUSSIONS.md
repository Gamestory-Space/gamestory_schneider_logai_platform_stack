# Schneider LogAI — Discussions

Classification: **GAMESTORY CONFIDENTIAL INTERNAL ENGINEERING MATERIAL**

## DISC-DB-001 — Database migration lifecycle

Status: ACTIVE  
Started: 2026-09-24

Context: LogAI currently ships raw SQL and can apply it during API startup, but startup application is disabled in UAT/production. Every release is expected to carry controlled DDL and potentially DML.

Options considered: application-startup migration; external/manual database execution; Flyway in a dedicated immutable migration image invoked as an Argo CD `PreSync` Job.

Current Direction: Flyway/PreSync is approved. Releases use expand/migrate/deploy/verify/contract and preserve data. Implementation details still needed include migration image build, credentials, locking, backup verification, timeouts, rollback/recovery, and conversion of current SQL into a baseline.

Related Decisions: `DB-001` through `DB-006`

## DISC-DB-002 — Keycloak / LogAI PostgreSQL isolation

Status: ACTIVE  
Started: 2026-09-24

Context: Current Helm configuration appears to give Keycloak and LogAI the same PostgreSQL database, username, and Secret. LogAI tables use a `logai_` prefix; Keycloak manages its own schema objects.

Options considered:

- separate logical databases and users in one RDS instance;
- separate schemas and users in one database;
- retain shared database and credentials.

Considerations: least privilege, Flyway ownership, Keycloak-managed schema, credential rotation, backup/restore boundaries, RDS operational overhead, and migration blast radius.

Current Direction: Separation appears preferable, but no topology is approved.

Related Decision: `DB-007`  
Related Open Question: `DB-Q001`

## DISC-AGENT-001 — ChatGPT / Codex shared project context

Status: RESOLVED  
Started: 2026-09-24

Context: ChatGPT and Codex have separate conversational context and require a durable handoff mechanism.

Options considered: conversation transcripts; external state service; structured state on an internal Git branch.

Current Direction: `project-direction` holds concise state, decisions, discussions, questions, and the latest handoff. Code remains authoritative for implementation facts and the CTO remains authoritative for direction.

Related Decision: `RELEASE-001`

## DISC-RELEASE-001 — Separation of Gamestory engineering state from Schneider release

Status: RESOLVED  
Started: 2026-09-24

Context: Internal architecture reasoning and agent instructions must never enter Schneider artifacts or Git history.

Options considered: package everything then exclude known files; dedicated internal branch plus explicit allow-list and final-artifact scan; mirroring repository history.

Current Direction: Use defence in depth: internal branch, absence from implementation branch, prohibited source ref, explicit release allow-list, clean export/new client history, recursive final-artifact scan, and existing IP controls.

Related Decision: `RELEASE-001`

## DISC-DEPLOY-001 — Argo CD environment promotion

Status: RESOLVED  
Started: 2026-09-24

Context: The client intends Argo CD—not GitHub Actions—to deploy the platform to EKS.

Options considered: GitHub Actions directly deploying Helm; GitHub Actions invoking Argo CD; manual Argo synchronization; two continuously reconciling Applications with Git promotion.

Current Direction: UAT watches `main`; production watches protected `production`. A reviewed `main` to `production` merge promotes the exact validated state. Argo CD remains independent of CI.

Related Decision: `DEPLOY-001`
