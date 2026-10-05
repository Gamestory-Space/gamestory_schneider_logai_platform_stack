# PRD — Gamestory Proprietary License Packaging for Release Images

**Target release:** LogAI v0.1.6
**Owner:** Gamestory Ltd
**Scope:** LogAI API, Identity API, LogAI UI and release artefacts

## 1. Objective
Add a standard Gamestory proprietary software licence to the LogAI release process. The licence must identify the software as proprietary to Gamestory Ltd, travel with every Gamestory-owned runtime image, be included in release/handover artefacts, coexist with third-party/open-source notices, not expose source-protection details, not change runtime behaviour, and be validated by CI.

This is licence packaging and release metadata, not runtime licence enforcement.

## 2. Legal boundary
Do not invent Schneider-specific commercial rights or obligations in code. Include a precedence clause:

> Where the Software is supplied under a separate written agreement between Gamestory Ltd and the recipient, that agreement governs to the extent of any conflict with this licence.

Do not encode customer names, fees, expiry dates, seat counts or environment restrictions into images unless explicitly required. The final licence wording requires Gamestory approval before release.

## 3. Canonical licence
Add one version-controlled plain-text canonical file, preferably `LICENSE` or `LICENSE-GAMESTORY`, identifying:

- Gamestory Ltd
- Gamestory Proprietary Software License
- Copyright © Gamestory Ltd
- All rights reserved.

Do not use an image or PDF as the canonical licence.

## 4. Licence content
Draft an initial proprietary licence covering:
- limited, non-exclusive, non-transferable, non-sublicensable permitted use under the applicable Gamestory agreement;
- restrictions on unauthorised copying, modification, distribution, sublicensing, resale, disclosure, reverse engineering, decompilation, disassembly, source derivation and removal of proprietary notices, subject to applicable law;
- Gamestory/its licensors retaining IP ownership;
- third-party/open-source components remaining under their respective licences;
- appropriate confidentiality language;
- conservative warranty/liability wording subordinate to the applicable commercial agreement;
- termination consequences subordinate to the applicable agreement;
- England and Wales governing law unless an existing agreement provides otherwise;
- explicit contract-precedence wording.

Do not invent contractual liability caps.

## 5. Container-image packaging
Every Gamestory-owned distributable runtime image must contain:

`/licenses/GAMESTORY-LICENSE.txt`

Apply to:
- `logai-api`
- `identity-api`
- `logai-ui`

Do not modify upstream Keycloak or PostgreSQL images.

Copy the licence into the final runtime stage, e.g.:

```dockerfile
COPY LICENSE /licenses/GAMESTORY-LICENSE.txt
```

Adapt paths to actual build contexts. Preserve non-root/read-only operation.

## 6. OCI metadata
Add to each Gamestory-owned image:

```dockerfile
LABEL org.opencontainers.image.vendor="Gamestory Ltd"
LABEL org.opencontainers.image.licenses="LicenseRef-Gamestory-Proprietary"
```

Preserve existing OCI metadata and integrate with existing CI metadata mechanisms. Do not put the full licence text in a label.

## 7. Third-party notices
Inspect the existing SBOM/licence process first. Preserve any existing third-party notice mechanism. Otherwise establish an appropriate `THIRD_PARTY_NOTICES` or generated licence-report artefact.

Do not manually invent third-party attribution. Third-party notices must remain distinct from the Gamestory proprietary licence. Do not block proprietary licence packaging solely because automated third-party notice generation needs follow-up; report the gap.

## 8. Release artefact
Include the canonical licence alongside existing release evidence, conceptually:

```text
release-v0.1.6/
├── LICENSE
├── THIRD_PARTY_NOTICES
├── image-digests.*
├── SBOM/
└── deployment/
```

Adapt to the existing release structure. The release licence and image licence must derive from the same canonical source file.

## 9. CI validation
Extend existing release validation. For every Gamestory final image verify:
- `/licenses/GAMESTORY-LICENSE.txt` exists and is non-empty;
- OCI vendor and licence labels exist;
- where practical, the image licence matches the canonical repository licence.

A release image missing the licence must fail release validation.

## 10. Source-protection interaction
Do not weaken existing closed-source hardening. The change must not reintroduce proprietary Python, TS/TSX, source maps, dev tooling or source trees; alter Nuitka packaging; change non-root operation; or require a writable root filesystem.

The licence is intentionally visible. Do not describe internal source-protection mechanisms in it.

## 11. Runtime behaviour
No runtime functionality may depend on the licence file. Do not add licence servers, activation, keys, call-home, expiry checks, customer locking or runtime cryptographic enforcement.

For v0.1.6 this is strictly: **legal notice + image metadata + release packaging + CI verification.**

## 12. Acceptance tests
For each Gamestory image, prove:

```bash
docker run --rm --entrypoint cat <image> /licenses/GAMESTORY-LICENSE.txt
```

returns the expected licence.

Inspect OCI metadata and confirm for `logai-api`, `identity-api` and `logai-ui`. Do not apply this test to upstream Keycloak/PostgreSQL images.

## 13. Documentation
Minimally update release documentation/runbook to state that Gamestory-owned images contain the proprietary licence at `/licenses/GAMESTORY-LICENSE.txt` and third-party components remain governed by their respective licences.

Do not expose internal IP-protection implementation in client-facing documentation.

## 14. Implementation approach
Before changing code inspect:
- all three Dockerfiles;
- multi-stage builds;
- CI/release workflows;
- existing OCI labels;
- SBOM generation;
- third-party licence/notices generation;
- release artefact structure.

Implement the smallest consistent change. Avoid independent implementations that can drift.

## 15. Required Codex report
After implementation report:

```text
Canonical licence file:
<path>

Images updated:
- logai-api
- identity-api
- logai-ui

Image licence path:
/licenses/GAMESTORY-LICENSE.txt

OCI metadata:
<actual labels>

Third-party notice mechanism:
<existing/new/gap>

CI validation:
<tests added>

Release packaging:
<location>

Validation:
PASS / FAIL
```

Include the drafted licence text for review.

## 16. Definition of Done
Complete when:
- one canonical Gamestory proprietary licence exists;
- licence wording has been presented for Gamestory review;
- all three Gamestory runtime images contain it;
- OCI vendor/licence metadata is present;
- Keycloak/Postgres images remain untouched;
- release artefacts contain the licence;
- third-party licensing remains separate;
- CI detects a missing licence;
- source-protection checks still pass;
- non-root/read-only tests still pass;
- application functionality is unchanged.

**Do not publish the updated release solely on the basis of Codex-generated legal wording. Stop for approval of the final licence text before treating it as the approved Gamestory licence.**


## Implementation update — user-supplied final wording

The initially generated draft is superseded by the complete GAMESTORY PROPRIETARY CLOSED-SOURCE SOFTWARE LICENSE expressly supplied and selected by the user. Platform root LICENSE is canonical; synchronized application build contexts and all three runtime images contain that exact text at /licenses/GAMESTORY-LICENSE.txt. Wording approval is bound to the SHA-256 in licensing/approval.json. No further wording approval is pending for this version; publication remains separately unauthorized. Validation and new local image IDs are recorded in docs/gamestory-license-release-evidence.md.
