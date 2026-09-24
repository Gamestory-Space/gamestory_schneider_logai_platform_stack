#!/usr/bin/env bash
set -euo pipefail

archive="${1:?Usage: $0 CLIENT_ZIP}"
[[ -f "$archive" ]] || { echo "Client archive not found: $archive" >&2; exit 1; }

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
extracted="$(mktemp -d)"
trap 'rm -rf "$extracted"' EXIT
unzip -q "$archive" -d "$extracted"

bundle="$(find "$extracted" -mindepth 1 -maxdepth 1 -type d -name 'schneider-logai-platform-*' -print -quit)"
[[ -n "$bundle" ]] || { echo "Client archive has no expected bundle root." >&2; exit 1; }
"$repo_root/scripts/validate-client-bundle.sh" "$bundle"
