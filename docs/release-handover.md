# Complete release handover through Docker Hub

Clients can retrieve the deployment ZIP and all four evidence packs without GitHub access:

```bash
oras pull docker.io/chrismdgs/gamestory_logai_schneider:platform-handover-v0.1.6 --output logai-v0.1.6
cd logai-v0.1.6
sha256sum -c schneider-logai-handover-v0.1.6.zip.sha256
```

The pull retrieves a handover ZIP, its checksum and its Sigstore signature bundle. The ZIP contains:

- `deployment/`: the original deployment ZIP, checksum and signature bundle.
- `evidence/`: identity API, LogAI API, UI and platform evidence ZIPs, including CycloneDX SBOMs, vulnerability scans, component inventories, validation, signatures and provenance.
- `manifest.json`: checksums for every included file and the released OCI digest for each component.
- `README.md`: instructions for using the contents.

Unzip the deployment ZIP separately and follow its README. The existing `platform-v0.1.6` artifact remains available as the deployment-only download. The handover adds evidence without modifying or invalidating the signed deployment ZIP.

Verify the handover signature with Cosign:

```bash
cosign verify-blob \
  --bundle schneider-logai-handover-v0.1.6.zip.sigstore.json \
  --certificate-identity https://github.com/Gamestory-Space/gamestory_schneider_logai_platform_stack/.github/workflows/handover-release.yml@refs/heads/master \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  schneider-logai-handover-v0.1.6.zip
```

## Checkout layout for subsequent releases

Future handover ZIPs extract directly into the client platform project, ready to check into its Git repository:

```text
compose.yaml
README.md
.gitignore
environments/
scripts/
identity/
licensing/
helm/
argocd/
docs/
VERSION
SOURCE_COMMIT
associated_artefacts/
  README.md
  manifest.json
  schneider-logai-platform-<version>.zip
  schneider-logai-platform-<version>.zip.sha256
  schneider-logai-platform-<version>.zip.sigstore.json
  evidence/
    <original evidence ZIPs>
    identity-api/
    logai-api/
    logai-ui/
    platform/
```

Deployment files retain their original paths and script permissions. Evidence is already expanded for inspection, while original evidence ZIPs and the signed deployment ZIP are retained for verification. The root README remains the deployment instructions; `associated_artefacts/README.md` explains the evidence. Its manifest covers every packaged file, including the deployment files at the root.

The generated `.gitignore` excludes private runtime `compose.env` files. Create that file separately after extracting the package. Existing v0.1.6 Docker Hub artifacts retain their published layout and signatures; this change applies to newly generated handovers. The verifier accepts both layouts.

## Local evidence archive

Release evidence is retained in `docs/evidence/release/<version>/` within the platform project. For v0.1.6, this directory contains the published handover ZIP, checksum, signature and publication record; the deployment attachments; and all four evidence packs. Expanded packs are under `evidence/identity-api/`, `evidence/logai-api/`, `evidence/logai-ui/` and `evidence/platform/` for direct access to SBOMs and reports. `manifest.json` records the original artifact digests and checksums.

## Preparing subsequent releases

After all four releases have completed successfully, a maintainer authenticated to the private source repositories collects their published attachments. This avoids requiring a cross-repository token in platform CI.

```bash
version=v0.1.7 # Example: replace with the completed release version.
release_ref="release/$version"
release_dir="docs/evidence/release/$version"
for repo in gamestory-identity-kit gamestory-logai-api logai_ui; do
  gh release download "$version" --repo "Gamestory-Space/$repo" \
    --pattern '*-evidence.zip' --dir "$release_dir/inputs/$repo"
done
gh release download "$version" \
  --repo Gamestory-Space/gamestory_schneider_logai_platform_stack \
  --pattern 'schneider-logai-platform-*' \
  --pattern 'gamestory-schneider-logai-platform-*-evidence.zip' \
  --dir "$release_dir/inputs/gamestory_schneider_logai_platform_stack"
python3 scripts/package-handover.py "$version" --inputs "$release_dir/inputs" \
  --archive "$release_dir/schneider-logai-handover-${version}.zip"
gh release upload "$version" --repo Gamestory-Space/gamestory_schneider_logai_platform_stack \
  "$release_dir/schneider-logai-handover-${version}.zip" \
  "$release_dir/schneider-logai-handover-${version}.zip.sha256"
gh workflow run handover-release.yml --ref "$release_ref" -f "version=$version" \
  --repo Gamestory-Space/gamestory_schneider_logai_platform_stack
```

The workflow validates evidence completeness and versions, matches all four recorded digests against Docker Hub, signs the handover, publishes it under `platform-handover-<version>`, and fresh-pulls it to verify checksums, signature and evidence. Existing handover tags cannot be overwritten.
