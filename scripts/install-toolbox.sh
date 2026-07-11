#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANIFEST="$REPO/inventory/public-manifest.json"
TARGET="${HERMES_HOME:-$HOME/.hermes}"
APPLY=0
ALL_SKILLS=0
INSTALL_PERSONALITIES=0
ACTIVATE_VALIDATOR=0
SKILLS=()
PLUGINS=()
PROFILES=()

usage() {
  cat <<'EOF'
Usage: install-toolbox.sh [options]
  --apply                Perform the installation (default: dry-run, no writes)
  --target <dir>         Target Hermes home (default: $HERMES_HOME or ~/.hermes)
  --skill <cat/name>     Install one manifest-listed skill (repeatable)
  --all-skills           Install every manifest-listed skill
  --plugin <name>        Install one manifest-listed plugin package (repeatable)
  --profile <name>       Install one profile package via hermes profile install (repeatable)
  --personalities        Install personality presets without activating them
  --activate-validator   Also activate the validator personality (implies --personalities)
EOF
}

parse_args() {
  while [ "$#" -gt 0 ]; do
    case "$1" in
      --apply) APPLY=1 ;;
      --target) shift; TARGET="${1:?missing target}" ;;
      --skill) shift; SKILLS+=("${1:?missing skill name}") ;;
      --all-skills) ALL_SKILLS=1 ;;
      --plugin) shift; PLUGINS+=("${1:?missing plugin name}") ;;
      --profile) shift; PROFILES+=("${1:?missing profile name}") ;;
      --personalities) INSTALL_PERSONALITIES=1 ;;
      --activate-validator) INSTALL_PERSONALITIES=1; ACTIVATE_VALIDATOR=1 ;;
      -h|--help) usage; exit 0 ;;
      *) echo "unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
    shift
  done
}

manifest_names() {
  python3 - "$MANIFEST" "$1" <<'PY'
import json
import sys
from pathlib import PurePosixPath

entries = json.load(open(sys.argv[1])).get(sys.argv[2], [])
for entry in entries:
    parts = PurePosixPath(entry['path']).parts
    print('/'.join(parts[1:3]) if sys.argv[2] == 'skills' else parts[1])
PY
}

require_listed() {
  if ! manifest_names "$1" | grep -Fxq -- "$2"; then
    echo "unknown $1 selection (not in inventory/public-manifest.json): $2" >&2
    exit 1
  fi
}

validate_selections() {
  local name
  for name in "${SKILLS[@]}"; do require_listed skills "$name"; done
  for name in "${PLUGINS[@]}"; do require_listed plugins "$name"; done
  for name in "${PROFILES[@]}"; do require_listed profiles "$name"; done
}

copy_tree() {
  if [ "$APPLY" = 1 ]; then
    mkdir -p "$3"
    cp -R "$2/." "$3/"
    echo "installed $1 -> $3"
  else
    echo "dry-run: would install $1 -> $3"
  fi
}

install_skills() {
  local name
  for name in "${SKILLS[@]}"; do
    copy_tree "skill $name" "$REPO/skills/$name" "$TARGET/skills/$name"
  done
}

install_plugins() {
  local name
  for name in "${PLUGINS[@]}"; do
    copy_tree "plugin $name" "$REPO/plugins/$name" "$TARGET/plugins/$name"
  done
}

install_one_profile() {
  if [ "$APPLY" != 1 ]; then
    echo "dry-run: would install profile $1 -> $TARGET/profiles/$1 (via hermes profile install)"
    return 0
  fi
  HERMES_HOME="$TARGET" hermes profile install "$REPO/profiles/$1" --name "$1" --yes
  echo "installed profile $1 -> $TARGET/profiles/$1"
}

install_profiles() {
  local name
  for name in "${PROFILES[@]}"; do
    install_one_profile "$name"
  done
}

validator_snippet() {
  python3 - "$REPO/primitives/personalities/validator/config.public.yaml" <<'PY'
import sys
from pathlib import Path

try:
    import yaml
except Exception as exc:
    raise SystemExit(f'PyYAML is required to read personality snippets: {exc}')

data = yaml.safe_load(Path(sys.argv[1]).read_text(encoding='utf-8')) or {}
prompt = (((data.get('agent') or {}).get('personalities') or {}).get('validator') or '').strip()
if not prompt:
    raise SystemExit('validator personality snippet is missing agent.personalities.validator')
print(prompt)
PY
}

require_hermes() {
  if ! command -v hermes >/dev/null 2>&1; then
    echo "hermes command not found; install Hermes Agent first" >&2
    exit 1
  fi
}

install_personalities() {
  if [ "$APPLY" != 1 ]; then
    echo "dry-run: would install personality validator -> $TARGET/config.yaml (agent.personalities.validator)"
    return 0
  fi
  local prompt
  prompt="$(validator_snippet)"
  HERMES_HOME="$TARGET" hermes config set agent.personalities.validator "$prompt" >/dev/null
  echo "installed personality validator -> $TARGET/config.yaml (agent.personalities.validator)"
}

activate_validator() {
  if [ "$APPLY" != 1 ]; then
    echo "dry-run: would activate personality validator -> $TARGET/config.yaml (agent.system_prompt, display.personality)"
    return 0
  fi
  local prompt
  prompt="$(validator_snippet)"
  HERMES_HOME="$TARGET" hermes config set agent.system_prompt "$prompt" >/dev/null
  HERMES_HOME="$TARGET" hermes config set display.personality validator >/dev/null
  echo "activated personality validator -> $TARGET/config.yaml (agent.system_prompt, display.personality)"
}

list_available() {
  echo "Nothing selected; this dry listing installs nothing."
  echo "Skills (--skill <name>, or --all-skills):"
  manifest_names skills | sed 's/^/  /'
  echo "Plugins (--plugin <name>; there is no all-plugins install):"
  manifest_names plugins | sed 's/^/  /'
  echo "Profiles (--profile <name>, installed via hermes profile install):"
  manifest_names profiles | sed 's/^/  /'
  echo "Personalities: --personalities installs presets; --activate-validator activates."
}

main() {
  parse_args "$@"
  echo "Hermes Toolbox installer"
  echo "Target: $TARGET"
  echo "Mode: $([ "$APPLY" = 1 ] && echo apply || echo dry-run)"
  if [ "$ALL_SKILLS" = 1 ]; then
    mapfile -t SKILLS < <(manifest_names skills)
  fi
  local selected=$(( ${#SKILLS[@]} + ${#PLUGINS[@]} + ${#PROFILES[@]} + INSTALL_PERSONALITIES ))
  if [ "$selected" = 0 ]; then
    list_available
    return 0
  fi
  validate_selections
  if [ "$APPLY" = 1 ] && { [ "${#PROFILES[@]}" -gt 0 ] || [ "$INSTALL_PERSONALITIES" = 1 ]; }; then
    require_hermes
  fi
  install_skills
  install_plugins
  install_profiles
  if [ "$INSTALL_PERSONALITIES" = 1 ]; then install_personalities; fi
  if [ "$ACTIVATE_VALIDATOR" = 1 ]; then activate_validator; fi
}

main "$@"
