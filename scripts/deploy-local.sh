#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "No reachable Kubernetes cluster. Configure kubectl for local k3s before deploying." >&2
  exit 1
fi
helm upgrade --install logai "$repo_root/helm/gamestory-schneider-platform" --namespace logai --create-namespace -f "$repo_root/environments/client-local/values.yaml" "$@"
kubectl rollout status deployment -n logai --timeout=5m
kubectl get pods -n logai
