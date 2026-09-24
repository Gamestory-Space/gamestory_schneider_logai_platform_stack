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

Question: What are the final client Git URL, chart path, cluster destination, namespaces, Argo project, and sync policies for `logai-uat` and `logai-prod`?

Context: The two-Application promotion model is approved, but client-site manifests were not available for baseline inspection.

Related Discussion: `DISC-DEPLOY-001`  
Decision Required From: Client platform owner / CTO

## SEC-Q001 — Kubernetes workload hardening baseline

Status: OPEN

Question: Which Schneider security baseline must the chart implement for service accounts/RBAC, pod and container security contexts, NetworkPolicies, and admission controls?

Context: These controls are not explicit in the current chart.

Decision Required From: Schneider security/platform owner with CTO
