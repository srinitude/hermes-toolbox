#!/usr/bin/env bash
set -euo pipefail

export PATH="/usr/local/bin:/usr/bin:/bin:${PATH:-}"

REPO="${HERMES_TOOLBOX_REPO:-$HOME/hermes-toolbox}"
HERMES_HOME_DIR="${HERMES_HOME:-$HOME/.hermes}"
PRIVATE_PREFIX="${HERMES_PRIVATE_PROFILE_PREFIX:-}"
PUBLIC_PLUGIN_PROFILE="${HERMES_PUBLIC_PLUGIN_PROFILE:-}"
LOCK="${HERMES_TOOLBOX_LOCK:-${TMPDIR:-/tmp}/hermes-toolbox-publisher.lock}"

fail() {
  echo "publish blocked: $1" >&2
  exit 1
}

require_public_visibility() {
  local origin_url slug visibility
  origin_url="$(git -C "$REPO" remote get-url origin)" || fail "no origin remote is configured"
  case "$origin_url" in
    *github.com*) ;;
    *) return 0 ;;
  esac
  slug="${origin_url#*github.com}"
  slug="${slug#[:/]}"
  slug="${slug%.git}"
  visibility="$(gh repo view "$slug" --json visibility --jq .visibility 2>/dev/null)" \
    || fail "public repository visibility check failed for $slug"
  [ "$visibility" = "PUBLIC" ] || fail "repository $slug visibility is not PUBLIC"
}

run_publish() {
  require_public_visibility
  git -C "$REPO" fetch --quiet origin
  local cmd=(python3 "$REPO/scripts/scan-public-candidates.py" --mode publish
             --hermes-home "$HERMES_HOME_DIR" --repo "$REPO")
  if [ -n "$PRIVATE_PREFIX" ]; then
    cmd+=(--private-profile-prefix "$PRIVATE_PREFIX")
  fi
  if [ -n "$PUBLIC_PLUGIN_PROFILE" ]; then
    cmd+=(--public-plugin-profile "$PUBLIC_PLUGIN_PROFILE")
  fi
  "${cmd[@]}"
}

(
  flock -n 9 || exit 0
  run_publish
) 9>"$LOCK"
