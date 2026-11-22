#!/usr/bin/env bash
set -euo pipefail
: "${FLYWAY_URL:?Set the reviewed PostgreSQL JDBC URL}"
: "${FLYWAY_USER:?Set the migration role}"
: "${FLYWAY_PASSWORD:?Load the migration credential securely}"
: "${FLYWAY_SCHEMA:?Set the existing shared schema}"
: "${EXPECTED_DATABASE:?Set the reviewed database name}"
: "${BACKUP_REFERENCE:?Set the restored backup reference}"

root="$(cd "$(dirname "$0")" && pwd)"
rollout="$root/../rollouts/ping-policy-studio"
[[ -d "$rollout" ]] || rollout="$root/../../rollouts/ping-policy-studio"
"$root/verify-policy-schema.sh"
[[ "$FLYWAY_SCHEMA" =~ ^[a-z_][a-z0-9_]*$ ]]
[[ "$EXPECTED_DATABASE" =~ ^[a-z_][a-z0-9_]*$ ]]
[[ "$FLYWAY_URL" =~ ^jdbc:postgresql://[a-zA-Z0-9.-]+(:[0-9]+)?/$EXPECTED_DATABASE(\?sslmode=verify-full)?$ ]] || {
  echo "Use an explicit PostgreSQL host and the reviewed database in FLYWAY_URL." >&2
  exit 1
}
export FLYWAY_LOCATIONS="filesystem:$rollout/schema"
export FLYWAY_SCHEMAS="$FLYWAY_SCHEMA" FLYWAY_DEFAULT_SCHEMA="$FLYWAY_SCHEMA"
export FLYWAY_CREATE_SCHEMAS=false FLYWAY_BASELINE_ON_MIGRATE=false
export FLYWAY_CLEAN_DISABLED=true FLYWAY_GROUP=true
export FLYWAY_TABLE=logai_flyway_schema_history
exec flyway migrate
