#!/usr/bin/env bash
set -euo pipefail
bundle_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# In the source checkout scripts live one directory deeper than in the client bundle.
[[ -f "$bundle_root/compose.yaml" ]] || bundle_root="$(cd "$bundle_root/.." && pwd)"
env_file="${1:-$bundle_root/environments/client-local/compose.env}"
mode="${2:-release}"
if [[ ! -f "$env_file" ]]; then echo "Copy compose.env.example to compose.env and set runtime passwords." >&2; exit 1; fi
if command -v podman >/dev/null; then engine=(podman compose); elif command -v docker >/dev/null; then engine=(docker compose); else echo "Podman or Docker is required." >&2; exit 1; fi
compose=("${engine[@]}" --env-file "$env_file" -f "$bundle_root/compose.yaml")
case "$mode" in
  build) compose+=(-f "$bundle_root/compose.build.yaml");;
  release) ;;
  *) echo "Usage: deploy-compose.sh [ENV_FILE] [release|build]" >&2; exit 1;;
esac
"${compose[@]}" config --quiet
if [[ "$mode" == build ]]; then
  "${compose[@]}" build identity-bootstrap identity-api logai-api logai-ui
  "${compose[@]}" pull postgres keycloak
else
  "${compose[@]}" pull
fi
"${compose[@]}" up -d postgres keycloak
# Always create a fresh finite job, including redeployment of unchanged images.
"${compose[@]}" run --rm --no-deps identity-bootstrap
# The successful run above is the gate; do not reuse an old completed job as evidence.
"${compose[@]}" up -d --no-deps identity-api logai-api logai-ui
"${compose[@]}" ps
