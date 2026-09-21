#!/usr/bin/env bash
set -euo pipefail
namespace="${NAMESPACE:-logai}"
release="${RELEASE_NAME:-logai}"
chart="gamestory-schneider-platform"
base="$release-$chart"
kubectl wait --for=condition=Ready pods --all -n "$namespace" --timeout=5m
for service_path in "${base}-identity-api:/health" "${base}-logai-api:/health" "${base}-logai-ui:/" "${base}-keycloak:9000/health/ready"; do
  service="${service_path%%:*}"
  path="${service_path#*:}"
  kubectl run "smoke-$RANDOM" -n "$namespace" --rm -i --restart=Never --image=curlimages/curl:8.10.1 -- "http://${service}${path}"
done
