# Schneider LogAI — Current Project State

Classification: **GAMESTORY CONFIDENTIAL INTERNAL ENGINEERING MATERIAL**

Last Updated: 2026-09-24  
Implementation Commit: `196507ca096430f211ac0c58dc9f3762401919b5` (`master`)  
Direction Commit: `project-direction` HEAD containing this revision

## Platform

The platform repository is the consolidated deployment repository. Its implemented runtime contains PostgreSQL, Keycloak, Identity API, LogAI API, and LogAI UI. SignalAutobahn, Agentic Core, Teams Interface/bot, and Schneider adapters are described as future integrations but are not deployed by the current chart. No Teams bot repository is present in the inspected local repository set.

## Runtime Architecture

The UI calls the LogAI API and Identity API. The Identity API integrates with Keycloak. Both LogAI API and Keycloak connect to PostgreSQL. Helm is authoritative; Compose supports build, release, and client-local use.

## EKS / Kubernetes

UAT and production overlays target Schneider-owned Kubernetes/EKS operationally, but no EKS cluster definition is managed here. UAT and production disable in-cluster PostgreSQL and reference external RDS endpoints and existing Secrets. Placeholder ingress class and host values still require client configuration.

## Helm

Chart `gamestory-schneider-platform` version `0.1.4` deploys Identity API, LogAI API, LogAI UI, Keycloak, optional PostgreSQL, Services, ConfigMap, Secrets, and optional Ingress. It does not currently contain Flyway or database-migration Jobs, Argo CD Applications, NetworkPolicies, PodDisruptionBudgets, or explicit pod/container security contexts.

## Argo CD

No Argo CD manifests are implemented in the Gamestory platform repository. Current agreed direction is two client-owned Applications: UAT tracks `main`; production tracks a protected `production` branch. The client-side implementation has not been inspected and is not represented as complete here.

## CI/CD

The platform release workflow validates Helm/Compose assets, constructs a client ZIP, generates SBOM and scan evidence, signs release material, publishes a generic OCI artifact, and attaches release files. As of the implementation commit, release construction uses an explicit allow-list, release refs are checked, `project-direction` is hard-rejected, and the final ZIP is recursively scanned for internal/source leakage. Direct GitHub Actions deployment workflows are absent.

## Container Registry / JFrog

Gamestory release/client-local overlays reference versioned Docker Hub images. UAT and production contain placeholder JFrog repositories and pull-secret names. Production digest fields are placeholders awaiting approved values.

## LogAI API

Inspected repository commit: `7bc6d3d631cd10dbcdc9b58123e987993478ce4f`.

FastAPI uses Psycopg and `DATABASE_URL`. Release and chute endpoints read PostgreSQL tables; orchestration endpoints insert/read/update durable run state. Schema SQL currently lives in the API repository and can be applied on API startup when enabled.

## LogAI UI

Inspected repository commit: `7c7e375b4559b92ef3e05e69e99cf4ccdc8c983d`.

Next.js uses standalone output and integrates with LogAI and Identity API runtime endpoints. The client image build configuration exists in the component repository. No separate observability deployment was found.

## Teams Bot

No deployed Teams workload exists in the current platform chart and no Teams bot repository was present in the inspected local repository set. Teams-related orchestration is future/documented behavior.

## Identity / Keycloak

Inspected identity repository commit: `26d88df8dbe60c587bf8af7f187c0031ceaeb91b`.

Keycloak is deployed as the identity provider/broker and connects to PostgreSQL through JDBC. Identity API is a separate workload. Entra integration is configurable; committed files contain placeholders and Secret references rather than client secrets.

## PostgreSQL / Persistence

LogAI API directly connects through Psycopg using injected `DATABASE_URL`. Verified application tables include `logai_release_shipments`, `logai_chutes`, and `logai_order_orchestration_runs`. Keycloak independently connects through JDBC. Current Helm values route both to the same external database name and username/Secret, so logical database and credential isolation is not implemented.

## Database Migration

The API contains SQL files `001`, `002`, and `003` and an application-startup schema mechanism. Helm defaults `applyDatabaseSchemaOnStartup` to false; UAT and production do not enable it. Flyway, a migration image, and an Argo CD PreSync Job are approved direction but are not implemented by this PRD.

## Observability

Health/readiness/liveness probes exist. No metrics stack, dashboards, centralized logging, tracing, or alerting resources are deployed by this chart.

## Security

Runtime credentials are referenced through Kubernetes Secrets for external database and Keycloak administration. Entra uses Secret references. Production image digests are intended but currently placeholders. Explicit workload security contexts, RBAC/service accounts, NetworkPolicies, and migration-specific least-privilege credentials are not implemented in the chart.

## IP Protection

Client packaging is allow-list based. Final bundle policy rejects `.ai`, `AGENTS.md`, state filenames, Git/GitHub metadata, environment files, Python/TypeScript/source maps, and test directories. The release workflow rejects `project-direction` and unapproved release refs. Component image release controls exist separately; full container-content leakage validation across every component was not changed by this PRD.

## Release Packaging

The platform produces a signed client-only ZIP plus checksum and Sigstore bundle, published as a generic Docker Hub OCI artifact. The ZIP contains client-local/UAT/production deployment material and excludes build/release environments and source repositories. Evidence includes SBOM, vulnerability scan, validation, provenance, and signature outputs.

## Environments

### DEV

No canonical `dev` overlay exists. `build` is the Gamestory source-build environment; deprecated `remote-build-dev` remains only as migration history and is excluded from client releases.

### TEST

No canonical `test` overlay exists. Local validation uses build/release/client-local Compose and local Kubernetes scripts.

### UAT

Uses external PostgreSQL/RDS, JFrog placeholders, one replica per application, managed Secret references, and ingress placeholders. Intended client Argo CD source is `main`, but Argo manifests are not in this repository.

### PROD

Uses external PostgreSQL/RDS, two replicas for applications and Keycloak, managed Secret references, TLS/ingress placeholders, and placeholder approved digests. Intended client Argo CD source is protected branch `production`, but Argo manifests are not in this repository.

## External Dependencies

Schneider EKS, RDS PostgreSQL, JFrog, DNS/ingress/TLS, managed Secrets, Entra configuration, and future SignalAutobahn/Agentic/Teams services.

## Known Implementation Gaps

- Repository implementation branch is named `master`, while the approved direction refers to `main`.
- Client Argo CD Applications are not present or verified here.
- Flyway migration image and PreSync Job are not implemented.
- Keycloak/LogAI database isolation is unresolved.
- UAT/production registry, digest, DNS, ingress, RDS, and Secret identifiers remain placeholders.
- No deployed Teams, SignalAutobahn, or Agentic Core workloads.
- No comprehensive observability stack or explicit Kubernetes workload hardening controls.
