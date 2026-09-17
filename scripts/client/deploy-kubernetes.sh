#!/usr/bin/env bash
set -euo pipefail
bundle_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
environment="${1:-}"
private_values="${2:-}"
case "$environment" in uat|prod) ;; *) echo "Usage: $0 uat|prod /path/to/private-values.yaml" >&2; exit 1;; esac
[[ -f "$private_values" ]] || { echo "A Schneider-controlled private values file is required." >&2; exit 1; }
for command in aws kubectl helm; do command -v "$command" >/dev/null || { echo "$command is required." >&2; exit 1; }; done
context="$(kubectl config current-context)"
if [[ "$context" != arn:aws:eks:* ]]; then echo "Current context is not AWS EKS: $context" >&2; exit 1; fi
if [[ "${ALLOW_SCHNEIDER_DEPLOY:-}" != "yes" ]]; then echo "Set ALLOW_SCHNEIDER_DEPLOY=yes after confirming EKS context: $context" >&2; exit 1; fi
aws sts get-caller-identity >/dev/null
namespace="${NAMESPACE:-logai-$environment}"
helm lint "$bundle_root/helm/gamestory-schneider-platform" -f "$bundle_root/environments/$environment/values.yaml" -f "$private_values"
helm upgrade --install logai "$bundle_root/helm/gamestory-schneider-platform" --namespace "$namespace" --create-namespace -f "$bundle_root/environments/$environment/values.yaml" -f "$private_values"
kubectl rollout status deployment -n "$namespace" --timeout=10m
