# Client deployment archive

CI publishes a client-only ZIP for each platform release. It is not a runnable container image.

For release `v0.1.4`, the Docker Hub generic OCI reference is:

```text
docker.io/chrismdgs/gamestory_logai_schneider:platform-v0.1.4
```

The artifact contains the deployment ZIP, its SHA-256 checksum, and its Sigstore bundle. Pull it with ORAS:

```bash
oras pull docker.io/chrismdgs/gamestory_logai_schneider:platform-v0.1.4
sha256sum --check schneider-logai-platform-v0.1.4.zip.sha256
unzip schneider-logai-platform-v0.1.4.zip
```

The same files and a separate evidence ZIP are attached to the GitHub `v0.1.4` release.

The deployment ZIP contains only:

- Pull-only `compose.yaml`
- Helm chart
- `client-local`, `uat`, and `prod` overlays
- Schneider deployment and smoke-test scripts
- Client deployment documentation and identity example

It excludes the Gamestory `build` and `release` environments, source-build Compose override, source repositories, application source, Git metadata, and CI configuration.

CI evidence includes Helm and Compose validation, shell checks, a CycloneDX filesystem SBOM, component/license inventory, Trivy SARIF, checksum/provenance, policy traceability, and a keyless Sigstore signature.
