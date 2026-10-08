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
  python3 - "$archive" <<'CHECK_TRANSFER'
import sys
import zipfile
with zipfile.ZipFile(sys.argv[1]) as archive:
    prefix = 'schneider-logai-platform-v0.0.0-policy-test/handover/schneider-argocd/'
    for name in ['README.md', 'values-transfer.yaml', 'templates/45-identity-bootstrap.yaml',
                 'files/gamestory-sso-realm.json', 'files/bootstrap-groups.json']:
        assert prefix + name in archive.namelist(), 'Missing transfer payload: ' + name
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

for forbidden_name in compose.env 'compose.env.example:Zone.Identifier'; do
  leak_bundle="$test_root/runtime-secrets"
  mkdir -p "$leak_bundle/environments/"{client-local,dev-aws,uat,prod}
  touch "$leak_bundle/environments/client-local/$forbidden_name"
  if "$repo_root/scripts/validate-client-bundle.sh" "$leak_bundle" >/dev/null 2>&1; then
    echo "Runtime env or Windows metadata was incorrectly accepted in a client bundle." >&2
    exit 1
  fi
  mv "$leak_bundle" "$test_root/rejected-${forbidden_name//[^a-zA-Z0-9]/_}"
done

printf 'Client release policy tests passed.\n'
