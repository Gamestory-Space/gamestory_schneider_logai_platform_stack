# Identity deployment parity — local v0.1.6

One compiled reconciliation implementation lives in the Identity API package: `app.bootstrap` and `app.identity_bootstrap`. Platform operator tooling contains only container-launch adapters. Compose, standalone Helm and Argo CD execute `python -c "from app.bootstrap import main; main()"` from that same image.

| Environment | Compose trigger | Helm chart trigger |
| --- | --- | --- |
| build | Deployment wrapper reruns finite job after Keycloak readiness | post-install/post-upgrade |
| release | Deployment wrapper reruns finite job after Keycloak readiness | post-install/post-upgrade |
| client-local | Deployment wrapper reruns finite job after Keycloak readiness | post-install/post-upgrade |
| uat | Not the deployed path | Helm hook mapped to Argo PostSync |
| prod | Not the deployed path | Helm hook mapped to Argo PostSync |

UAT/Prod explicitly retain `hookMode: helm`. Their Argo Application definitions contain no duplicate bootstrap hook. A full Argo sync is required; selective sync skips hooks. An ordinary unchanged Compose `up` is not a guaranteed rerun: use `scripts/client/deploy-compose.sh` (client archive: `scripts/deploy-compose.sh`). The wrapper stops on bootstrap failure before starting/updating applications.

## Verification

- Helm render tests: all five requested environments plus legacy dev-aws; same entry point, lifecycle annotations, canonical configuration, mounted Secrets and restricted runtime.
- Three Compose lifecycle regression tests: fresh job on each deployment, application gate and failure propagation.
- Sixteen tests passed against the compiled Identity API image, including seven account/realm/client reconciliation contracts.
- Disposable real Compose acceptance: creates all users, stable IDs after rerun, preserves disabled account state, repairs removed memberships/group-role mappings, incorrect redirects and realm settings, rejects missing initial credentials.
- Real Keycloak/browser acceptance: first-login password changes and API access for all four users, expected role boundaries, logout/revocation and private changed passwords surviving reconciliation.
- Compiled image inspection: no proprietary source or prohibited credential values in any image layer. Vulnerability gate: zero fixable HIGH/CRITICAL findings using the local cached vulnerability database. CycloneDX SBOM retained.
- Workflow syntax, shell syntax and client bundle policy checked.

[Sanitized evidence](evidence/identity-parity-v0.1.6-local/tested-images.json) records actual local image IDs. The Identity API image tested is `8e152079a32d08b7ddc336e789629a68262b39fde9b0651113cad498954be492`.

Membership repair remains additive: existing extra privileges and known direct assignments are preserved. Explicit administrative operations are required to remove privileges or reset passwords. User account state, unrelated clients and external IdPs are preserved; declared application-owned realm settings and user-profile configuration are repaired.

No image publication, Git push, running client-stack change or EKS/Argo deployment was performed. Client registry availability, real DNS/TLS, Secrets and a full site Argo sync still require deployment acceptance. The v0.1.6 candidate must be published/mirrored and pinned by approved digest before client rollout.
