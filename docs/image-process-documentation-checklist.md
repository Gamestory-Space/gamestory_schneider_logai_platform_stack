# Image Process Documentation Checklist

## Purpose

This checklist defines the process and evidence documents that should exist for each deployable image before it is promoted into a customer-controlled environment.

The same checklist should be applied to every image in the platform stack. The image name, repository location, registry path, and environment-specific values should be supplied by the owning platform or customer configuration repository, not hard-coded into this document.

## Per-Image Documentation Set

Each image should have the following documentation or generated evidence.

| Document | Owner | Source | Purpose |
| --- | --- | --- | --- |
| Image metadata | Platform team | CI-generated evidence | Records service name, image reference, version, commit SHA, source repository, workflow run, and release/build classification. |
| Build provenance | Platform team | CI-generated evidence | Shows where the image came from, which workflow produced it, and which immutable digest was produced for release builds. |
| SBOM | Platform team | CI-generated evidence | Lists operating system and application components in the built image. |
| Component inventory | Platform team | CI-generated evidence | Provides a human-reviewable component and license summary derived from the SBOM. |
| Vulnerability scan | Platform team | CI-generated evidence | Records vulnerability findings for the image, including severity-gated findings. |
| License review | Platform team | CI-generated evidence | Supports open-source and third-party component governance. |
| Smoke test evidence | Platform team | CI-generated evidence | Confirms the image starts and responds to the minimum expected health or runtime check. |
| Configuration contract | Platform team | Platform documentation | Defines required and optional runtime values, expected formats, defaults, and whether each value is secret. |
| Environment mapping | Customer/platform configuration team | Customer configuration repository | Maps image version, runtime configuration, network routes, identity settings, and deployment overrides for each environment. |
| Secret reference list | Customer/platform configuration team | Customer configuration repository | Lists required secret names or paths without exposing secret values. |
| Deployment notes | Customer/platform configuration team | Customer configuration repository | Describes how the image is deployed in the target environment and what dependencies it requires. |
| Rollback notes | Customer/platform configuration team | Customer configuration repository | Identifies how to return to the previous approved image version and which checks confirm recovery. |
| Operational runbook | Customer/platform operations team | Customer configuration repository | Captures health checks, logs, metrics, alerts, and first-response actions for the running service. |

## Minimum CI Evidence Pack

For each image build, the CI evidence pack should include:

```text
image-metadata.md
policy-traceability.md
sbom/
  image.cdx.json
vulnerability-scan/
  scan.sarif
license-review/
  component-inventory.csv
validation/
  health-or-smoke-test-output
  container.log
provenance/
  release-digest.md
signature/
  signed-image-ref.txt
  signing-output.txt
```

Some files only exist for release builds. For example, digest, signature, and attestation evidence may be skipped for pull request builds if the image is not pushed to a registry.

## Pull Request Builds

Pull request builds should validate that the image can be built and smoke tested.

Recommended PR behavior:

- Build the image from the PR branch.
- Run the image smoke test.
- Generate an SBOM.
- Generate vulnerability and license evidence.
- Upload the evidence pack as a workflow artifact.
- Report vulnerability findings without blocking the PR unless the team has agreed that PRs should be vulnerability-gated.
- Avoid pushing release images from PR builds.

## Release Builds

Release builds should be stricter than pull request builds.

Recommended release behavior:

- Build the image from a reviewed source revision.
- Run smoke tests.
- Generate SBOM, component inventory, vulnerability scan, and license evidence.
- Fail the release build on agreed severity gates.
- Push the image to the approved registry.
- Record the immutable image digest.
- Sign the image where required.
- Generate provenance or attestation evidence where required.
- Upload the complete evidence pack.

## Deployment Readiness Gate

An image should be considered ready for environment deployment only when:

- The image version is traceable to a reviewed commit.
- The evidence pack exists for the build.
- The required configuration contract is documented.
- Required secret references are known.
- The target environment has a matching configuration entry.
- Smoke tests have passed.
- Release severity gates have passed or exceptions have been approved.
- Rollback steps are documented.

## Customer Handover View

For customer review, each image should be represented by a concise handover summary:

```text
Image role:
Version:
Immutable digest:
Source commit:
Build workflow run:
Evidence pack:
Required configuration:
Required secret references:
Health check:
Deployment dependencies:
Rollback version:
Known exceptions:
```

The customer-owned configuration repository can then reference this information when selecting which image version is deployed into each environment.
