# Gamestory licence packaging status

Canonical licence: platform root `LICENSE`. Matching snapshots are in the three application build contexts; Identity API also retains its root snapshot. Image path: `/licenses/GAMESTORY-LICENSE.txt`. OCI vendor: `Gamestory Ltd`; licence identifier: `LicenseRef-Gamestory-Proprietary`.

The original draft has been replaced verbatim with the user-supplied closed-source licence, expressly selected for use in this session; `licensing/approval.json` records its SHA-256 digest and `approved` status. Local builds and packaging validate this exact supplied version. Publication workflows refuse pending approval or a text/digest mismatch. The wording is approved by the user; image publication remains unauthorized and has not occurred.

All images also carry separate `/licenses/THIRD_PARTY_NOTICES.txt`. Existing CycloneDX SBOMs and generated component inventories supply dependency licence reports; unknown licences remain flagged for follow-up. Keycloak and PostgreSQL retain upstream licences and unchanged image digests; exact licence texts are included separately in the platform bundle and read-only deployment mounts.

The licence and notices are included at the root of the platform release archive and alongside application image validation evidence. CI checks the final effective image filesystem (including deletion/overwrite layers), exact canonical bytes and OCI metadata. Regression tests cover missing/modified licence files, labels, whiteouts and legal approval/digest changes. No runtime enforcement or activation is introduced.
