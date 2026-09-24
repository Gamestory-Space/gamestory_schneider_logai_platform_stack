#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_ref="${1:-$(git -C "$repo_root" symbolic-ref --quiet --short HEAD || true)}"
source_sha="${2:-$(git -C "$repo_root" rev-parse HEAD)}"

[[ -n "$source_ref" ]] || { echo "Unable to identify the release source ref." >&2; exit 1; }

case "$source_ref" in
  project-direction|refs/heads/project-direction|refs/remotes/origin/project-direction)
    echo "project-direction is internal and can never be a client release source." >&2
    exit 1
    ;;
  master|main|refs/heads/master|refs/heads/main|refs/remotes/origin/master|refs/remotes/origin/main)
    exit 0
    ;;
  refs/tags/v*|v*)
    ;;
  *)
    echo "Unapproved client release source ref: $source_ref" >&2
    exit 1
    ;;
esac

for approved_ref in refs/remotes/origin/master refs/remotes/origin/main refs/heads/master refs/heads/main; do
  if git -C "$repo_root" show-ref --verify --quiet "$approved_ref" \
    && git -C "$repo_root" merge-base --is-ancestor "$source_sha" "$approved_ref"; then
    exit 0
  fi
done

echo "Release tag commit $source_sha is not contained in an approved implementation branch." >&2
exit 1
