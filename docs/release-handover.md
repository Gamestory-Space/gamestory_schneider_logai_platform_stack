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

## Preparing subsequent releases

After all four releases have completed successfully, a maintainer authenticated to the private source repositories collects their published attachments. This avoids requiring a cross-repository token in platform CI.

```bash
version=v0.1.6
for repo in gamestory-identity-kit gamestory-logai-api logai_ui; do
  gh release download "$version" --repo "Gamestory-Space/$repo" \
    --pattern '*-evidence.zip' --dir "handover-inputs/$repo"
done
gh release download "$version" \
  --repo Gamestory-Space/gamestory_schneider_logai_platform_stack \
  --pattern 'schneider-logai-platform-*' \
  --pattern 'gamestory-schneider-logai-platform-*-evidence.zip' \
  --dir handover-inputs/gamestory_schneider_logai_platform_stack
python3 scripts/package-handover.py "$version" --inputs handover-inputs \
  --archive "dist/schneider-logai-handover-${version}.zip"
gh release upload "$version" --repo Gamestory-Space/gamestory_schneider_logai_platform_stack \
  "dist/schneider-logai-handover-${version}.zip" \
  "dist/schneider-logai-handover-${version}.zip.sha256"
gh workflow run handover-release.yml --ref master -f "version=$version" \
  --repo Gamestory-Space/gamestory_schneider_logai_platform_stack
```

The workflow validates evidence completeness and versions, matches all four recorded digests against Docker Hub, signs the handover, publishes it under `platform-handover-<version>`, and fresh-pulls it to verify checksums, signature and evidence. Existing handover tags cannot be overwritten.
