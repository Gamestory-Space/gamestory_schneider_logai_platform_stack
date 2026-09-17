#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
environment="${1:-release}"
namespace="${NAMESPACE:-logai-${environment}}"
case "$environment" in build|release) ;; *) echo "Use build or release for Gamestory local Kubernetes testing." >&2; exit 1;; esac
for command in kubectl helm; do command -v "$command" >/dev/null || { echo "$command is required." >&2; exit 1; }; done
context="$(kubectl config current-context)"
if [[ "${ALLOW_LOCAL_K8S_DEPLOY:-}" != "yes" ]]; then echo "Set ALLOW_LOCAL_K8S_DEPLOY=yes after confirming local context: $context" >&2; exit 1; fi
kubectl cluster-info >/dev/null
helm lint "$repo_root/helm/gamestory-schneider-platform" -f "$repo_root/environments/$environment/values.yaml"
helm upgrade --install logai "$repo_root/helm/gamestory-schneider-platform" --namespace "$namespace" --create-namespace -f "$repo_root/environments/$environment/values.yaml" "${@:2}"
kubectl rollout status deployment -n "$namespace" --timeout=10m
NAMESPACE="$namespace" "$repo_root/scripts/smoke-test.sh"
