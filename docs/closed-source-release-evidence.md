# LogAI v0.1.5 closed-source implementation evidence

Status: local implementation and validation complete; Docker publication explicitly deferred by the user. No registry push, release tag, release workflow dispatch, signing or post-publish acceptance was performed.

The PRD is saved as [PRD-003](prd/PRD-003-v0.1.5-nuitka-closed-source-release.md). The Schneider handover is [the runtime contract](closed-source-runtime-contract.md). Changes span `gamestory-identity-kit`, `gamestory-logai-api`, `logai_ui` and this platform repository. They remain uncommitted working-tree changes; the baseline Git revisions in the candidate metadata are not release source SHAs.

## Local acceptance

| Check | Identity API | LogAI API | UI |
|---|---|---|---|
| Production image builds | Pass | Pass | Pass |
| Final-image layers contain no proprietary source/bytecode/maps | Pass | Pass | Pass |
| Numeric UID and read-only root filesystem | 10001, pass | 10001, pass | 1000, pass |
| Runtime configuration and smoke endpoints | Pass | Pass | Pass |
| Database/schema/sample-data integration | No direct DB dependency | Pass; 8 shipments, 16 chutes | Browser runtime config verified |
| Fixable HIGH/CRITICAL Trivy findings | 0 | 0 | 0 |
| CycloneDX SBOM from final image | Generated | Generated | Generated |
| ELF/debug/build-path inspection | Pass | Pass | Not applicable |
| Existing authentication/unit tests against compiled app | 9 passed | No pre-existing suite | Production build/type checking passed |

Six artifact-gate regression tests pass, including source deleted in later layers, numeric UID enforcement, missing compiled artifacts and correct treatment of third-party runtime dependencies. All three modified workflows pass actionlint; Python validation scripts and YAML parse successfully. Platform bundle-input and release-policy checks pass. The policy suite's ZIP-specific check was skipped because native `zip` is absent on this host; no new platform ZIP was produced or published.

Acceptance ran under rootless Podman on amd64 with capabilities dropped and no-new-privileges. UI runtime-config storage uses the documented Podman-compatible dedicated tmpfs; Docker CI uses explicit uid/gid ownership. `/app/.next/cache` was not mounted and no read-only errors occurred. APIs shut down with exit 0. Next.js handles SIGTERM with exit 143; the UI gate accepts that normal termination and rejects forced-kill exit 137.

The scan policy matches the existing release gate: fixable HIGH/CRITICAL findings fail; unfixed findings are excluded using `--ignore-unfixed`. The UI lockfile was updated to compatible fixed dependencies (Next.js 16.3.8), and Node 22 satisfies their engine requirement. Identity PyJWT was updated from 2.12.0 to 2.14.0 after final-image scanning found fixable vulnerabilities. Authentication tests pass against the fixed compiled image.

## Performance review

See the saved per-API baseline/candidate reports, raw latency samples, CPU/memory snapshots and image sizes. Baselines are the existing published v0.1.4 images. Candidate and baseline use the same Uvicorn transport selection. Each endpoint has 100 sequential local requests; startup is one observation including container launch. These are diagnostic measurements, not a production load-test conclusion.

API image size increased less than 1%. Startup was faster in the final local observations and memory snapshots were lower. Database-backed median latencies remained around 8 ms. Tail changes are retained in full rather than hidden: identity `/config` p95 increased from about 0.80 to 1.16 ms, and LogAI Chutes p99 from about 10.57 to 11.82 ms. These small absolute differences and short samples do not establish a sustained regression. CPU percentage snapshots depend on container lifetime; accumulated CPU nanoseconds are also retained. Repeat on a controlled representative workload before production approval if these differences matter to the acceptance budget.

## Pending release work

User authorization to resume Docker publication is required. Commit and review the component changes, run the authenticated CI release gates, publish the exact validated image without rebuilding, fresh-pull each digest, repeat artifact/runtime verification, sign the images and record immutable published digests, release source SHAs, CI links and final evidence packs. CI support for these steps is implemented, but their execution is deferred.

Do not promote the proposed v0.1.5 references to Schneider until the published acceptance record is complete. No Helm files were changed.

Raw local evidence: [candidate metadata and evidence](evidence/closed-source-v0.1.5-local/candidate-images.json).
