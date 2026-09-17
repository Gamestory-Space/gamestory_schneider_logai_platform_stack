#!/usr/bin/env bash
set -euo pipefail
image="${1:?Usage: $0 IMAGE_REFERENCE OUTPUT_DIRECTORY}"
output="${2:?Usage: $0 IMAGE_REFERENCE OUTPUT_DIRECTORY}"
mkdir -p "$output"
if command -v podman >/dev/null; then engine=podman; elif command -v docker >/dev/null; then engine=docker; else echo "Podman or Docker is required." >&2; exit 1; fi
"$engine" pull "$image"
container="$($engine create "$image")"
trap '"$engine" rm "$container" >/dev/null 2>&1 || true' EXIT
"$engine" cp "$container:/bundle/." "$output"
