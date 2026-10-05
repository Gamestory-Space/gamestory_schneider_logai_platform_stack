# Schneider LogAI v0.1.7 handover

Deployment files are extracted at the project root; follow its README.md.
associated_artefacts/ contains the original signed deployment ZIP, checksum and signature.
Its evidence/ folder contains original and expanded identity, API, UI and platform evidence packs.
Each pack includes its CycloneDX SBOM, scan, component inventory, validation,
signature and provenance. manifest.json records SHA-256 checksums and OCI digests.

These files can be checked into the client Git repository. Keep the private runtime compose.env ignored.
