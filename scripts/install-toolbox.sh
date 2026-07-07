#!/usr/bin/env bash
set -euo pipefail

APPLY=0
TARGET="${HERMES_HOME:-$HOME/.hermes}"
INSTALL_PLUGINS=0
INSTALL_PERSONALITIES=0
ACTIVATE_VALIDATOR=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1 ;;
    --target) shift; TARGET="${1:?missing target}" ;;
    --plugins) INSTALL_PLUGINS=1 ;;
    --personalities) INSTALL_PERSONALITIES=1 ;;
    --activate-validator) INSTALL_PERSONALITIES=1; ACTIVATE_VALIDATOR=1 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Hermes Toolbox installer"
echo "Target: $TARGET"
echo "Mode: $([ "$APPLY" = 1 ] && echo apply || echo dry-run)"

install_validator_personality() {
  local config_file="$REPO/primitives/personalities/validator/config.public.yaml"
  if ! command -v hermes >/dev/null 2>&1; then
    echo "hermes command not found; install Hermes before applying personality primitives" >&2
    return 1
  fi
  local validator_prompt
  validator_prompt="$(python3 - "$config_file" <<'PY'
import sys
from pathlib import Path

try:
    import yaml
except Exception as exc:
    raise SystemExit(f"PyYAML is required to read personality snippets: {exc}")

data = yaml.safe_load(Path(sys.argv[1]).read_text(encoding='utf-8')) or {}
prompt = (((data.get('agent') or {}).get('personalities') or {}).get('validator') or '').strip()
if not prompt:
    raise SystemExit('validator personality snippet is missing agent.personalities.validator')
print(prompt)
PY
)"
  HERMES_HOME="$TARGET" hermes config set agent.personalities.validator "$validator_prompt" >/dev/null
  echo "Installed personality: validator"
  if [ "$ACTIVATE_VALIDATOR" = 1 ]; then
    HERMES_HOME="$TARGET" hermes config set agent.system_prompt "$validator_prompt" >/dev/null
    HERMES_HOME="$TARGET" hermes config set display.personality validator >/dev/null
    echo "Activated personality: validator"
  fi
}

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

if [ -d "$REPO/primitives/personalities" ]; then
  echo "Personality primitives:"
  find "$REPO/primitives/personalities" -mindepth 1 -maxdepth 1 -type d | sort | sed "s#^$REPO/primitives/personalities/##" || true
  if [ "$APPLY" = 1 ] && [ "$INSTALL_PERSONALITIES" = 1 ]; then
    install_validator_personality
  elif [ "$INSTALL_PERSONALITIES" = 1 ]; then
    echo "Dry-run only: rerun with --apply to install personality primitives."
  else
    echo "Use --personalities to install custom /personality presets."
  fi
fi
