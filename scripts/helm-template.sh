#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
for environment in build release client-local uat prod; do
  echo "Rendering $environment"
  helm template logai "$repo_root/helm/gamestory-schneider-platform" -f "$repo_root/environments/$environment/values.yaml" >/dev/null
done
