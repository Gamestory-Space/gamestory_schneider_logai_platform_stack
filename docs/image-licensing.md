# Image licensing

| Component | Primary software licence | Delivery |
| --- | --- | --- |
| LogAI API | Gamestory proprietary closed-source licence | Image `/licenses/GAMESTORY-LICENSE.txt` and OCI licence metadata |
| Identity API and bootstrap Job | Same Gamestory proprietary closed-source licence | Same image and licence file |
| LogAI UI | Same Gamestory proprietary closed-source licence | Image `/licenses/GAMESTORY-LICENSE.txt` and OCI licence metadata |
| Keycloak | Apache-2.0 | Existing `/opt/keycloak/LICENSE.txt`; unchanged upstream image; additional release/mounted copy |
| PostgreSQL | PostgreSQL License | Unchanged upstream image; release/mounted licence copy |
| Official PostgreSQL container scripts | MIT | Release/mounted `CONTAINER-LICENSE` |

The closed-source licence covers LogAI-owned code only. It does not relicense third-party code in application/base images, Keycloak, PostgreSQL or the official container scripts. Dependency notices remain in their installed locations; release SBOMs and component inventories record dependency licence declarations.

Compose mounts upstream licences read-only under `/usr/share/licenses/logai-platform/<component>`. Helm supplies the same exact files through a ConfigMap and read-only mounts. Existing upstream image references/digests are preserved; these deployment mounts supplement their filesystem and do not modify or relabel the published upstream images. For externally managed PostgreSQL in UAT/production, no PostgreSQL container is deployed by this chart; its licence remains documented in the handover.

The platform root `LICENSE` is the canonical plain-text Gamestory Proprietary Closed-Source Software License. Each application build context contains a byte-identical snapshot (Identity API: `backend/LICENSE`). The final image carries it at `/licenses/GAMESTORY-LICENSE.txt`, alongside `/licenses/THIRD_PARTY_NOTICES.txt`. OCI labels identify vendor `Gamestory Ltd` and `LicenseRef-Gamestory-Proprietary`. Licence text is not placed in image labels.

The text is the user-supplied version expressly selected by Gamestory in this session. `licensing/approval.json` binds legal approval to its SHA-256 digest. Publication workflows reject pending approval or a text/approval digest mismatch. Approval of the licence wording does not authorize image publication; local builds and validation do not push images. An existing written Gamestory agreement prevails over conflicting licence terms. No runtime activation, customer restrictions, expiry checks or licence server is introduced.

Existing release SBOMs and their generated component inventories provide the third-party licence-report mechanism. Unknown declarations remain explicitly unknown; no attribution is invented. Package-specific notices are retained. No claim of complete legal review of every dependency is made by the packaging checks.

Upstream references: https://www.apache.org/licenses/LICENSE-2.0 , https://www.postgresql.org/about/licence/ , https://github.com/docker-library/postgres/blob/master/LICENSE .
