#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
test_root="$(mktemp -d)"
trap 'rm -rf "$test_root"' EXIT

if "$repo_root/scripts/validate-release-source.sh" project-direction HEAD >/dev/null 2>&1; then
  echo "project-direction was incorrectly accepted as a release source." >&2
  exit 1
fi

if command -v zip >/dev/null; then
  "$repo_root/scripts/package-client-release.sh" v0.0.0-policy-test "$test_root/dist"
  archive="$test_root/dist/schneider-logai-platform-v0.0.0-policy-test.zip"
  "$repo_root/scripts/validate-client-archive.sh" "$archive"
  expected_name="$(basename "$archive")"
  actual_name="$(awk '{print $2}' "$archive.sha256")"
  [[ "$actual_name" == "$expected_name" ]] || { echo "Archive checksum must use a portable basename." >&2; exit 1; }
  (cd "$test_root/dist" && sha256sum --check "$expected_name.sha256")
  python3 - "$archive" <<'CHECK_TRANSFER'
import sys
import zipfile
with zipfile.ZipFile(sys.argv[1]) as archive:
    prefix = 'schneider-logai-platform-v0.0.0-policy-test/handover/schneider-argocd/'
    for name in ['README.md', 'values-transfer.yaml', 'templates/45-identity-bootstrap.yaml',
                 'files/gamestory-sso-realm.json', 'files/bootstrap-groups.json']:
        assert prefix + name in archive.namelist(), 'Missing transfer payload: ' + name
    central = 'schneider-logai-platform-v0.0.0-policy-test/applications/logai/'
    for name in ['Chart.yaml', 'values.yaml', 'values-eu-west-3-eks-shared-dev.yaml',
                 'templates/20-logai-api.yaml', 'templates/_helpers.tpl']:
        assert central + name in archive.namelist(), 'Missing central chart payload: ' + name
    assert 'schneider-logai-platform-v0.0.0-policy-test/transfer_To_schneider.readme' in archive.namelist()
    root = 'schneider-logai-platform-v0.0.0-policy-test/'
    for name in ['identity/ping-uat.json', 'scripts/render-ping-provider.sh',
                 'scripts/verify-policy-schema.sh', 'docs/ping-uat-integration.md',
                 'rollouts/ping-policy-studio/preflight.psql', 'scripts/migrate-policy-schema.sh',
                 'rollouts/ping-policy-studio/grant-runtime.psql', 'rollouts/ping-policy-studio/schema.sha256',
                 'rollouts/ping-policy-studio/schema/V011__four_section_policy.sql']:
        assert root + name in archive.namelist(), 'Missing rollout payload: ' + name
    assert not any('.private.json' in name or '/identity/generated/' in name for name in archive.namelist())
CHECK_TRANSFER
else
  echo "SKIP: final ZIP test requires zip; CI runners execute this check."
fi

mkdir -p "$test_root/leak/environments/client-local" "$test_root/leak/environments/dev-aws" "$test_root/leak/environments/uat" "$test_root/leak/environments/prod" "$test_root/leak/.ai"
printf 'internal\n' > "$test_root/leak/.ai/PROJECT_STATE.md"
if "$repo_root/scripts/validate-client-bundle.sh" "$test_root/leak" >/dev/null 2>&1; then
  echo "Internal project state was incorrectly accepted in a client bundle." >&2
  exit 1
fi

for forbidden_name in compose.env 'compose.env.example:Zone.Identifier' ping-uat.enabled.private.json pg_service.conf '.pg_service.conf'; do
  leak_bundle="$test_root/runtime-secrets"
  mkdir -p "$leak_bundle/environments/"{client-local,dev-aws,uat,prod}
  cp "$repo_root/LICENSE" "$leak_bundle/LICENSE"
  cp "$repo_root/THIRD_PARTY_NOTICES" "$leak_bundle/THIRD_PARTY_NOTICES"
  touch "$leak_bundle/environments/client-local/$forbidden_name"
  if "$repo_root/scripts/validate-client-bundle.sh" "$leak_bundle" >/dev/null 2>&1; then
    echo "Runtime env or Windows metadata was incorrectly accepted in a client bundle." >&2
    exit 1
  fi
  mv "$leak_bundle" "$test_root/rejected-${forbidden_name//[^a-zA-Z0-9]/_}"
done

printf 'Client release policy tests passed.\n'
