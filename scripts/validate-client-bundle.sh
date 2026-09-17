#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dockerfile="$repo_root/packaging/client-bundle.Dockerfile"
for required in client-local uat prod; do grep -q "COPY environments/$required " "$dockerfile"; done
for forbidden in 'environments/build' 'environments/release' 'compose.build.yaml'; do
  if grep -q "$forbidden" "$dockerfile"; then echo "Forbidden client-bundle content: $forbidden" >&2; exit 1; fi
done
if grep -Eq '(^|[[:space:]])build:' "$repo_root/compose.yaml"; then
  echo "Client Compose topology must not contain source build definitions" >&2
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
  echo "Client bundle references a Gamestory source repository or build context." >&2
  exit 1
fi
