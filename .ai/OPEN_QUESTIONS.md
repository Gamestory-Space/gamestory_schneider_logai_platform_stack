# Schneider LogAI — Open Questions

Classification: **GAMESTORY CONFIDENTIAL INTERNAL ENGINEERING MATERIAL**

## DB-Q001 — Keycloak / LogAI database isolation

Status: OPEN

Question: Should Keycloak and LogAI use separate logical databases and users, separate schemas and users, or retain the current shared database/credential model within RDS?

Context: Current platform values appear shared. Flyway ownership and least-privilege design depend on this topology.

Related Discussion: `DISC-DB-002`  
Related Proposed Decision: `DB-007`  
Decision Required From: CTO

## REPO-Q001 — Implementation branch rename

Status: OPEN

Question: Should the Gamestory platform repository’s implementation branch be renamed from `master` to `main` to match the approved operating model?

Context: The PRD and client Argo direction use `main`, but the inspected local and remote Gamestory platform branch is `master`. Release workflows currently target `master`; the source validator temporarily accepts both names.

Decision Required From: CTO/repository owner

## DEPLOY-Q001 — Client Argo CD configuration verification

Status: OPEN

Question: What are the final client Git URL, cluster destinations, namespaces, and Argo project for `logai-dev-aws`, `logai-uat`, and `logai-prod`, and when should automated reconciliation be enabled?

Context: The three Application manifests now exist with verified chart/value paths, manual synchronization, namespace creation disabled, and placeholders for Schneider-owned settings. All initially reference `main`, which differs from the earlier approved protected-production branch direction.

Related Discussion: `DISC-DEPLOY-001`  
Decision Required From: Client platform owner / CTO

## SEC-Q001 — Kubernetes workload hardening baseline

Status: OPEN

Question: Which Schneider security baseline must the chart implement for service accounts/RBAC, pod and container security contexts, NetworkPolicies, and admission controls?

Context: These controls are not explicit in the current chart.

Decision Required From: Schneider security/platform owner with CTO
