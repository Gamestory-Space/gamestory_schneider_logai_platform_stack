#!/usr/bin/env bash
# Read-only image/input check. Run after rendering the COMPLETE client chart.
set -euo pipefail
manifest="${1:?Usage: $0 MANIFEST_JSON FINAL_RENDERED_YAML}"
rendered="${2:?Usage: $0 MANIFEST_JSON FINAL_RENDERED_YAML}"
[[ $# == 2 && -s "$manifest" && -s "$rendered" ]] || { echo "Provide the release manifest and final chart render." >&2; exit 1; }
command -v jq >/dev/null || { echo "jq is required." >&2; exit 1; }
jq -e '.policy_content_schema == 4 and .generator == "four-section-policy-v5"
  and (.api_source_commit | test("^[0-9a-f]{40}$"))
  and (.ui_source_commit | test("^[0-9a-f]{40}$"))' "$manifest" >/dev/null || {
  echo "Release source/schema provenance is incomplete." >&2; exit 1;
}
for service in api ui; do
  reference="$(jq -er --arg key "${service}_release_image" '.[$key] // empty' "$manifest")" || {
    echo "Missing $service release image; previous release pins cannot be used." >&2; exit 1;
  }
  [[ "$reference" =~ ^[a-zA-Z0-9./:_-]+@sha256:[0-9a-f]{64}$ ]] || {
    echo "The $service image requires an immutable sha256 reference." >&2; exit 1;
  }
  case "$reference" in
    *:logai-api-v0.1.8@*|*:logai-ui-v0.1.7@*) echo "Previous application release is not this rollout." >&2; exit 1;;
  esac
  digest="${reference##*@}"
  # Repository names can change on promotion; the full image digest must survive.
  if ! awk '/^[[:space:]]*image:/ {gsub(/["\047]/, ""); sub(/^[[:space:]]*image:[[:space:]]*/, ""); print $1}' "$rendered" \
    | grep -Eq "@${digest}$"; then
    echo "Final chart is missing the approved $service image digest. Render the complete client chart with release values." >&2; exit 1;
  fi
done
if grep -Eq 'example\.invalid|<SCHNEIDER_|<LOGAI_|<APPROVED_PLATFORM_RELEASE>|targetRevision:[[:space:]]*rel2_v0\.1\.7' "$rendered"; then
  echo "Final render still contains site placeholders or the historical Argo revision." >&2; exit 1;
fi
echo "Release source/image inputs match the render. Client DB, privileges, SSO and registry access still require on-site acceptance."
