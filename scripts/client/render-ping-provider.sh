#!/usr/bin/env bash
# Deployment configuration only. Never contacts Keycloak or prints a secret.
set -euo pipefail
secret_file=""; output=""; method=""; scopes=""; existing=""; enabled=false
issuer="https://ping-sso-uat.schneider-electric.com"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --client-secret-file|--output|--client-auth-method|--scopes|--issuer|--existing-provider-file)
      [[ $# -ge 2 ]] || { echo "Missing value for $1" >&2; exit 2; }
      case "$1" in
        --existing-provider-file) existing="$2";;
        --client-secret-file) secret_file="$2";; --output) output="$2";;
        --client-auth-method) method="$2";; --scopes) scopes="$2";; --issuer) issuer="$2";;
      esac
      shift 2;;
    --enable) enabled=true; shift;;
    --help) echo "Usage: $0 --client-secret-file FILE --output FILE --client-auth-method BASIC_OR_POST --scopes SCOPES [--existing-provider-file PRIVATE_BACKUP] [--enable]"; exit 0;;
    *) echo "Unknown option: $1" >&2; exit 2;;
  esac
done
[[ -f "$secret_file" && -n "$output" && -n "$scopes" ]] || { echo "Provide --client-secret-file, --output, --scopes and --client-auth-method." >&2; exit 2; }
case "$method" in client_secret_basic|client_secret_post) ;; *) echo "Confirm this client's Basic or POST authentication method." >&2; exit 2;; esac
[[ "$issuer" == https://ping-sso-uat.schneider-electric.com ]] || { echo "This renderer targets Schneider Ping UAT only." >&2; exit 2; }
command -v jq >/dev/null || { echo "jq is required." >&2; exit 2; }
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
template=""
for root in "$script_dir/.." "$script_dir/../.."; do
  if [[ -f "$root/identity/ping-uat.json" ]]; then template="$root/identity/ping-uat.json"; break; fi
done
[[ -n "$template" ]] || { echo "Cannot find the public UAT provider template." >&2; exit 2; }
umask 077
temporary="$(mktemp "$(dirname "$output")/.ping-render.XXXXXXXX")"
trap 'rm -f "$temporary"' EXIT
base_args=(--argjson previous "[]")
if [[ -n "$existing" ]]; then
  [[ -f "$existing" ]] || { echo "Existing provider backup is missing." >&2; exit 2; }
  base_args=(--slurpfile previous "$existing")
fi
jq "${base_args[@]}" --rawfile secret "$secret_file" --arg issuer "$issuer" --arg scopes "$scopes" \
  --arg method "$method" --argjson enabled "$enabled" '
  . as $template |
  if ($previous | length)>0 then
    if ($previous | length) != 1 or $previous[0].alias != "schneider-main"
      or $previous[0].providerId != "oidc"
      or $previous[0].config.clientId != "logai_68225_uat"
    then error("Existing provider identity must be reviewed before update") else . * $previous[0] end
  else . end |
  if .alias != "schneider-main" or .config.clientId != "logai_68225_uat" then error("Unexpected UAT provider identity") else . end |
  if ($scopes | test("(^|\\s)openid(\\s|$)")) then . else error("Scopes must include openid") end |
  ($secret | sub("[\\r\\n]+$";"")) as $credential |
  if ($credential | test("\\S")) then . else error("Client secret is empty") end |
  .enabled=$enabled | .authenticateByDefault=false | .linkOnly=false | .addReadTokenRoleOnCreate=false | .trustEmail=false | .storeToken=false |
  .config.authorizationUrl=$template.config.authorizationUrl | .config.tokenUrl=$template.config.tokenUrl |
  .config.userInfoUrl=$template.config.userInfoUrl | .config.jwksUrl=$template.config.jwksUrl |
  .config.issuer=$issuer | .config.defaultScope=$scopes | .config.clientAuthMethod=$method |
  .config.clientSecret=$credential | .config.validateSignature="true" | .config.useJwksUrl="true" | .config.hideOnLoginPage="false"
' "$template" > "$temporary"
# Atomic no-clobber publication: refuses existing files and symlinks.
ln "$temporary" "$output"
echo "Private Ping provider configuration written; Keycloak has not been changed."
