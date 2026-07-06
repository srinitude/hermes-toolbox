#!/usr/bin/env bash
set -euo pipefail

APPLY=0
TARGET="${HERMES_HOME:-$HOME/.hermes}"
INSTALL_PLUGINS=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --target) shift; TARGET="${1:?missing target}" ;;
    --plugins) INSTALL_PLUGINS=1 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Hermes Toolbox installer"
echo "Target: $TARGET"
echo "Mode: $([ "$APPLY" = 1 ] && echo apply || echo dry-run)"

if [ -d "$REPO/skills" ]; then
  echo "Public skills:"
  find "$REPO/skills" -name SKILL.md -type f | sort | sed "s#^$REPO/##"
  if [ "$APPLY" = 1 ]; then
    mkdir -p "$TARGET/skills"
    rsync -a "$REPO/skills/" "$TARGET/skills/"
  fi
fi

if [ -d "$REPO/plugins" ]; then
  echo "Sanitized plugin packages:"
  find "$REPO/plugins" -mindepth 1 -maxdepth 1 -type d | sort | sed "s#^$REPO/plugins/##" || true
  if [ "$APPLY" = 1 ] && [ "$INSTALL_PLUGINS" = 1 ]; then
    mkdir -p "$TARGET/plugins"
    rsync -a --exclude '.env' --exclude 'auth.json' --exclude 'memories' --exclude 'sessions' --exclude 'logs' --exclude 'cache' --exclude 'state.db*' "$REPO/plugins/" "$TARGET/plugins/"
  fi
fi

if [ -d "$REPO/profiles" ]; then
  echo "Sanitized profile packages are listed only and are not installed as live profiles by default."
  find "$REPO/profiles" -mindepth 1 -maxdepth 1 -type d | sort | sed "s#^$REPO/profiles/##" || true
fi
