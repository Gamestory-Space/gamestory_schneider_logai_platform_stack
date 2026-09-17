#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file="${1:-$repo_root/environments/client-local/compose.env}"
if ! grep -qiE '(microsoft|wsl)' /proc/version; then
  echo "This test is intended to run inside WSL2." >&2
  exit 1
fi
command -v podman >/dev/null || { echo "Podman is required." >&2; exit 1; }
podman info >/dev/null
podman compose version >/dev/null
if [[ ! -f "$env_file" ]]; then
  echo "Create $env_file from compose.env.example and set local passwords first." >&2
  exit 1
fi
podman compose --env-file "$env_file" -f "$repo_root/compose.yaml" config >/dev/null
podman compose --env-file "$env_file" -f "$repo_root/compose.yaml" pull
podman compose --env-file "$env_file" -f "$repo_root/compose.yaml" up -d --no-build
for url in http://localhost:8000/health http://localhost:8010/health http://localhost:3000/ http://localhost:8080/health/ready; do
  curl --fail --retry 30 --retry-delay 5 --retry-all-errors "$url" >/dev/null
done
podman compose --env-file "$env_file" -f "$repo_root/compose.yaml" ps
