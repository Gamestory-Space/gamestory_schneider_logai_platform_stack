#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bundle="${1:-}"
if grep -Eq '(^|[[:space:]])build:' "$repo_root/compose.yaml"; then
  echo "Client Compose topology must not contain source build definitions." >&2
  exit 1
fi
client_inputs=(
  "$repo_root/compose.yaml"
  "$repo_root/environments/client-local"
  "$repo_root/environments/uat"
  "$repo_root/environments/prod"
  "$repo_root/scripts/client"
  "$repo_root/README.client.md"
)
if grep -RInE 'gamestory-identity-kit|(^|[/\\])logai_ai([/\\]|$)|_BUILD_CONTEXT=' "${client_inputs[@]}"; then
  echo "Client bundle input references a Gamestory source repository or build context." >&2
  exit 1
fi
if [[ -n "$bundle" ]]; then
  for required in client-local uat prod; do [[ -d "$bundle/environments/$required" ]] || { echo "Missing $required" >&2; exit 1; }; done
  for forbidden in build release remote-build-dev compose.build.yaml packaging .git .github; do
    [[ ! -e "$bundle/environments/$forbidden" && ! -e "$bundle/$forbidden" ]] || { echo "Forbidden bundle content: $forbidden" >&2; exit 1; }
  done
fi
