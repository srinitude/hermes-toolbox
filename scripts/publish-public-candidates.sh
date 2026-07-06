#!/usr/bin/env bash
set -euo pipefail

REPO="${HERMES_TOOLBOX_REPO:-$HOME/hermes-toolbox}"
HERMES_HOME_DIR="${HERMES_HOME:-$HOME/.hermes}"
PRIVATE_PREFIX="${HERMES_PRIVATE_PROFILE_PREFIX:-}"
PUBLIC_PLUGIN_PROFILE="${HERMES_PUBLIC_PLUGIN_PROFILE:-}"
LOCK="${TMPDIR:-/tmp}/hermes-toolbox-publisher.lock"

(
  flock -n 9 || exit 0
  visibility="$(gh repo view srinitude/hermes-toolbox --json visibility --jq .visibility 2>/dev/null || true)"
  if [ "$visibility" != "PUBLIC" ]; then
    echo "public repository visibility check failed" >&2
    exit 1
  fi
  cd "$REPO"
  if git rev-parse --verify origin/main >/dev/null 2>&1; then
    git pull --rebase --autostash origin main >/dev/null 2>&1
  fi
  cmd=(python3 scripts/scan-public-candidates.py --mode publish --hermes-home "$HERMES_HOME_DIR" --repo "$REPO")
  if [ -n "$PRIVATE_PREFIX" ]; then cmd+=(--private-profile-prefix "$PRIVATE_PREFIX"); fi
  if [ -n "$PUBLIC_PLUGIN_PROFILE" ]; then cmd+=(--public-plugin-profile "$PUBLIC_PLUGIN_PROFILE"); fi
  "${cmd[@]}"
) 9>"$LOCK"
