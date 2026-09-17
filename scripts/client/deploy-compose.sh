#!/usr/bin/env bash
set -euo pipefail
bundle_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${1:-$bundle_root/environments/client-local/compose.env}"
if [[ ! -f "$env_file" ]]; then echo "Copy compose.env.example to compose.env and set local passwords." >&2; exit 1; fi
if command -v podman >/dev/null; then engine=(podman compose); elif command -v docker >/dev/null; then engine=(docker compose); else echo "Podman or Docker is required." >&2; exit 1; fi
"${engine[@]}" --env-file "$env_file" -f "$bundle_root/compose.yaml" config >/dev/null
"${engine[@]}" --env-file "$env_file" -f "$bundle_root/compose.yaml" pull
"${engine[@]}" --env-file "$env_file" -f "$bundle_root/compose.yaml" up -d --no-build
"${engine[@]}" --env-file "$env_file" -f "$bundle_root/compose.yaml" ps
