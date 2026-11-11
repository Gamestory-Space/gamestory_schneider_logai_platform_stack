# IREP Policy Traceability

- Image identity: image metadata and immutable commit SHA.
- SBOM: CycloneDX JSON generated from the built image.
- Third-party component inventory: component CSV derived from SBOM.
- Prohibited component check: vulnerability and component scan evidence.
- Vulnerability scan: Trivy SARIF report for Critical and High findings.
- License/open-source governance: license summary derived from SBOM.
- Secure build evidence: GitHub Actions run and Docker build logs.
- Image authenticity: GHCR image signing on release builds.
- Provenance evidence: immutable source and platform image digests with signed image references on release builds.
- Validation evidence: container smoke test logs plus health and config responses.
- Release documentation: workflow evidence pack and image metadata.
