# Gamestory proprietary closed-source licence — v0.1.6 local validation

Canonical licence: [LICENSE](../LICENSE), containing the user-supplied version verbatim. Gamestory approval is recorded in [licensing/approval.json](../licensing/approval.json), including the explicit instruction, timestamp and licence SHA-256. Approval covers wording; image publication remains unauthorized and has not occurred.

Image path: `/licenses/GAMESTORY-LICENSE.txt`. OCI vendor: `Gamestory Ltd`. OCI licence identifier: `LicenseRef-Gamestory-Proprietary`. Separate notice: `/licenses/THIRD_PARTY_NOTICES.txt`.

| Image | Tested local image ID | Default user | Validation |
| --- | --- | --- | --- |
| identity-api | `8ddd51a91c1e458f36beceac5d1d8c31d9dfe95a385f9a14dcbf4e318feb25a6` | 10001:10001 | PASS |
| logai-api | `3e8cc1c1e6cbfb5e308746640330d22676f027c68baa8bdf278ad5b10240e917` | 10001:10001 | PASS |
| logai-ui | `7b65ddedd79167822a8222e93fad4eb5e35bb12dbea5b56386eedf941e6641bf` | 1000:1000 | PASS |

All three local v0.1.6 images were rebuilt with the supplied text. Default non-root/read-only licence extraction matched the canonical file byte-for-byte. Image metadata, source/credential protection, restricted-runtime acceptance and zero-fixable-HIGH/CRITICAL vulnerability gates passed. Vulnerability checks used the local cached database; CycloneDX SBOMs retained. [Sanitized evidence](evidence/gamestory-license-supplied-v0.1.6-local/tested-images.json) records the new image IDs.

Seven licence metadata/filesystem regression cases and four approval regression cases pass. Changed licence bytes cannot reuse an earlier approval; pending approvals remain blocked. The new canonical text and approval records match all application build contexts. The actual approval gate passes for this exact user-selected version.

The release archive includes root LICENSE and THIRD_PARTY_NOTICES; archive/canonical equality is checked. The previous draft validation remains historical evidence, superseded by this supplied version.

Keycloak/PostgreSQL upstream images remain unmodified and retain their original licence coverage. Third-party notice/SBOM mechanisms remain separate. No runtime licence enforcement is introduced. Existing running containers and databases were not recreated or changed; local image tags alone do not update them. No Git push, image push, client deployment or EKS/Argo sync was performed.
