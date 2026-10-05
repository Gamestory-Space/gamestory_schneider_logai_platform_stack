# IREP Policy Traceability

- Artifact identity: metadata, version, source commit, and SHA-256 checksum.
- SBOM: CycloneDX JSON generated from the extracted deployment ZIP.
- Component inventory: CSV derived from the filesystem SBOM.
- Vulnerability scan: Trivy filesystem SARIF for Critical and High findings.
- Configuration validation: Helm lint, four client Helm renders, Compose config, and shell syntax.
- Client boundary: bundle policy excludes Gamestory environments, build contexts, and source repositories.
- Authenticity: keyless Sigstore signature for the ZIP on release builds.
- Distribution: generic OCI artifact in Docker Hub plus GitHub Release attachments.
