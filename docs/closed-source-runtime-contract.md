# LogAI v0.1.5 runtime contract

The implementation PRD is [PRD-003](prd/PRD-003-v0.1.5-nuitka-closed-source-release.md).
Schneider owns JFrog ingestion, Helm, Argo CD, namespaces, runtime secrets and EKS configuration. This change does not modify Helm.

| Component | Docker Hub tag in `chrismdgs/gamestory_logai_schneider` | UID:GID | Port | Health | Writable mounts |
|---|---|---|---|---|---|
| Identity API | `identity-api-v0.1.5` | 10001:10001 | 8000 | `/health` | `/tmp` |
| LogAI API | `logai-api-v0.1.5` | 10001:10001 | 8000 | `/health`, `/ready` | `/tmp` |
| UI | `logai-ui-v0.1.5` | 1000:1000 | 3000 | `/` | `/tmp`, `/app/runtime-config` |

Every application supports a read-only root filesystem, no privilege escalation and all Linux capabilities dropped. `/app/runtime-config` must be writable by UID/GID 1000 (for example an emptyDir with the appropriate fsGroup). No writable `.next/cache` mount was needed in acceptance testing. Rootless Podman lacks Docker's tmpfs uid/gid options; Compose and local Podman tests use a dedicated mode-1777 tmpfs, while Docker CI uses uid=1000,gid=1000,mode=0700.

## Configuration

LogAI reads `DATABASE_URL`, `ENVIRONMENT`, `API_CORS_ORIGINS`, `APPLY_DATABASE_SCHEMA_ON_STARTUP`, `SEED_SAMPLE_DATA_ON_STARTUP` and its existing integration/identity environment settings at runtime. PostgreSQL must be reachable. SQL resources are packaged at `/app/schema`, selected by `LOGAI_SCHEMA_DIRECTORY`; they are not Python source. Client-local sample seeding defaults to false. Seeded Release/Chutes rows use the current Europe/Amsterdam business date.

Identity reads its existing `KEYCLOAK_PUBLIC_URL`, `KEYCLOAK_REALM`, `KEYCLOAK_ISSUER_URL`, `KEYCLOAK_JWKS_FETCH_URL`, `KEYCLOAK_AUDIENCE`, `API_CORS_ORIGINS`, `SERVICE_NAME` and `ENVIRONMENT`. It connects to Keycloak's JWKS service, not directly to a database. Keycloak owns its PostgreSQL connection. Identity tests exercise successful JWT validation and rejection of invalid tokens.

UI reads `AUTH_MODE`, `AUTH_URL`, `AUTH_REALM`, `AUTH_CLIENT_ID`, `AUTH_IDP_HINT`, `AUTH_CALLBACK_URL`, `IDENTITY_API_BASE_URL` and `LOGAI_API_BASE_URL`. These are public browser configuration, not secret inputs. The entrypoint generates `/app/runtime-config/config.json`; the dynamic `/config.json` route serves it with `Cache-Control: no-store`. Use browser-accessible endpoint URLs. Compose's existing `NEXT_PUBLIC_AUTH_MODE` env-file variable is mapped to the runtime `AUTH_MODE` environment name for compatibility. SSO and local fallback behavior now use runtime authentication state.

## Build and release

Python release Dockerfiles compile only the known application package with Nuitka 2.8.10 (`--module app --include-package=app --nofollow-imports --no-pyi-file --file-reference-choice=runtime`). The official package-compilation architecture retains unmodified third-party packages and their reflection/dynamic imports. No standalone plugins are needed. CPython 3.12 is shared by compilation and runtime. Final images copy only the stripped application extension, runtime dependencies and necessary SQL resources. Development uses `--target development` or ordinary Python; `Dockerfile.source` exists for source-baseline benchmarking and must never be published.

UI ships Next.js standalone output, static files, public assets and the config entrypoint. Source maps and TypeScript are removed before copying to runtime layers. No application source, Nuitka, C intermediates, compiler or tests are copied into final API layers.

Existing release workflows retain CycloneDX SBOM generation, Trivy scanning, signing and evidence archives. All PR and release scans fail on fixable HIGH/CRITICAL vulnerabilities. Final-image verification examines every saved image layer so deleting source in a later layer cannot bypass the gate. API ELF artifacts are checked for debug sections, developer paths and private-key markers. Existing identity tests run against compiled code; runtime checks use real disposable PostgreSQL for LogAI and verify seeded data, date validation, runtime configuration, restricted filesystems and shutdown.

The workflow builds its candidate once, validates it, then tags and pushes that image without rebuilding. It refuses existing version tags. It fresh-pulls by digest and repeats source-leak and runtime acceptance checks before signing and completing evidence. A failed post-publish gate does not mark the release accepted. Do not promote an incomplete release.

## Evidence and promotion

Each component's workflow evidence includes source revision, CI run, immutable image digest, CycloneDX SBOM, Trivy results, source-leak inspection, ELF metadata, runtime logs, resource snapshots and raw latency samples. API baseline/candidate comparison reports startup, p50/p95/p99, image size and CPU/memory snapshots; results are diagnostic, with material changes reviewed before release. Promote the same digest to JFrog, client-local, UAT and production without rebuilding.

Published digests and acceptance status must be recorded in `closed-source-release-evidence.md` after all three release workflows succeed. An implementation or successful local build alone is not a published release.

Nuitka package compilation reference: https://nuitka.net/user-documentation/use-cases.html#package-compilation
Next.js standalone reference: https://nextjs.org/docs/app/api-reference/config/next-config-js/output

The combined v0.1.5 authentication contract is [Keycloak bootstrap](keycloak-bootstrap-runtime-contract.md): EKS uses SSO, real LogAI clients/audience and canonical roles. Current final candidate validation is recorded in [Keycloak release evidence](keycloak-bootstrap-release-evidence.md); earlier hardening image evidence is historical.
