#!/usr/bin/env bash
set -euo pipefail
version="${1:?Usage: $0 VERSION [OUTPUT_DIRECTORY]}"
output_dir="${2:-dist}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! "$version" =~ ^v?[0-9]+\.[0-9]+\.[0-9]+([.-][A-Za-z0-9.-]+)?$ ]]; then
  echo "Invalid release version: $version" >&2
  exit 1
fi
case "$output_dir" in /*) output_path="$output_dir" ;; *) output_path="$repo_root/$output_dir" ;; esac
mkdir -p "$output_path"
staging="$(mktemp -d)"
trap 'rm -rf "$staging"' EXIT
bundle="$staging/schneider-logai-platform-$version"
mkdir -p "$bundle"
allowlist="$repo_root/release/client-bundle-allowlist.txt"
while IFS='|' read -r source destination; do
  [[ -n "$source" && "${source:0:1}" != "#" ]] || continue
  [[ -e "$repo_root/$source" ]] || { echo "Allow-listed release input is missing: $source" >&2; exit 1; }
  mkdir -p "$(dirname "$bundle/$destination")"
  cp -R "$repo_root/$source" "$bundle/$destination"
done < "$allowlist"
printf '%s\n' "$version" > "$bundle/VERSION"
git -C "$repo_root" rev-parse HEAD > "$bundle/SOURCE_COMMIT"
"$repo_root/scripts/validate-client-bundle.sh" "$bundle"
archive="$output_path/schneider-logai-platform-$version.zip"
find "$bundle" -exec touch -t 198001010000.00 {} +
if command -v zip >/dev/null; then
  (cd "$staging" && zip -X -q -r "$archive" "schneider-logai-platform-$version")
elif command -v powershell.exe >/dev/null && command -v wslpath >/dev/null; then
  windows_bundle="$(wslpath -w "$bundle")"
  windows_archive="$(wslpath -w "$archive")"
  powershell.exe -NoProfile -NonInteractive -Command "Compress-Archive -LiteralPath '$windows_bundle' -DestinationPath '$windows_archive' -Force" >/dev/null
else
  echo "zip is required." >&2
  exit 1
fi
sha256sum "$archive" > "$archive.sha256"
"$repo_root/scripts/validate-client-archive.sh" "$archive"
