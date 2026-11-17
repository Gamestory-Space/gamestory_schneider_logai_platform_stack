#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rollout=""
for root in "$script_dir/.." "$script_dir/../.."; do
  if [[ -f "$root/rollouts/ping-policy-studio/schema.sha256" ]]; then rollout="$root/rollouts/ping-policy-studio"; break; fi
done
[[ -n "$rollout" ]] || { echo "Cannot locate the rollout manifest." >&2; exit 1; }
(cd "$rollout" && sha256sum --check schema.sha256)
if [[ $# -gt 1 ]]; then echo "Usage: $0 [schema-directory-extracted-from-approved-api-image]" >&2; exit 1; fi
if [[ $# -eq 1 ]]; then
  while read -r expected relative; do
    source_file="$1/${relative#schema/}"
    [[ -f "$source_file" ]] || { echo "Approved API image is missing ${relative#schema/}." >&2; exit 1; }
    actual="$(sha256sum "$source_file")"; actual="${actual%% *}"
    [[ "$actual" == "$expected" ]] || { echo "Schema differs from the reviewed rollout: ${relative#schema/}." >&2; exit 1; }
  done < "$rollout/schema.sha256"
  for source_file in "$1"/*.sql; do
    [[ -e "$source_file" ]] || continue
    name="${source_file##*/}"
    case "$name" in 002_seed_schneider_sample_read_models.sql|004_policy_persistence.down.sql|005_policy_lifecycle.down.sql) continue;; esac
    if ! awk '{print $2}' "$rollout/schema.sha256" | grep -Fxq -- "schema/$name"; then
      echo "Approved API image contains unreviewed SQL: $name." >&2; exit 1
    fi
  done
  echo "Approved API image schema matches the reviewed rollout."
fi
