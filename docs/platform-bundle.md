# Client deployment archive

CI publishes a client-only ZIP for each platform release. It is not a runnable container image.

For platform release `v0.1.9`, the Docker Hub generic OCI reference is:

```text
docker.io/chrismdgs/gamestory_logai_schneider:platform-v0.1.9
```

The artifact contains the deployment ZIP, its SHA-256 checksum, and its Sigstore bundle. Pull it with ORAS:

```bash
oras pull docker.io/chrismdgs/gamestory_logai_schneider:platform-v0.1.9
sha256sum --check schneider-logai-platform-v0.1.9.zip.sha256
unzip schneider-logai-platform-v0.1.9.zip
```

The same files and a separate evidence ZIP are attached to the GitHub `v0.1.9` release.

The deployment ZIP contains only:

- Pull-only `compose.yaml`
- Helm chart
- `client-local`, `dev-aws`, `uat`, and `prod` overlays
- Argo CD Application definitions for Dev AWS, UAT, and Production
- Schneider deployment and smoke-test scripts
- Client deployment documentation and identity example
- Supplied central-chart files under `applications/logai` and `transfer_To_schneider.readme`

It excludes the Gamestory `build` and `release` environments, source-build Compose override, source repositories, application source, Git metadata, and CI configuration.

CI evidence includes Helm and Compose validation, shell checks, a CycloneDX filesystem SBOM, component/license inventory, Trivy SARIF, checksum/provenance, policy traceability, and a keyless Sigstore signature.

Platform v0.1.9 includes the credential-recovery central-chart delta and pins
LogAI API v0.1.8; Identity API and UI remain v0.1.7. The supplied central chart
contains only the API workload templates received so far. Merge the three-file
delta described in `transfer_To_schneider.readme` into the complete remote chart;
do not replace that chart with this partial local copy. JFrog image promotion,
ESO verification and actual Schneider deployment acceptance remain separate.
