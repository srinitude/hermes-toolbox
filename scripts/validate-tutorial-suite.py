#!/usr/bin/env python3
"""Validate the public tutorial suite against the real Hermes runtime: real
PluginManager discovery for every tutorial plugin and a real profile install
for the tutorial profile package. No fake contexts."""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from package_checks import check_registration_parity  # noqa: E402
from real_runtime import (  # noqa: E402
    DEFAULT_PAYLOAD, install_profile, probe_plugin_package, require_runtime,
    run_hermes,
)

EXPECTED_PLUGINS = [
    'hermes-tutorial-compass', 'hermes-setup-coach', 'hermes-concept-glossary',
    'hermes-command-lab', 'hermes-accessibility-coach', 'hermes-tools-lab',
    'hermes-config-lab', 'hermes-safety-sandbox-lab', 'hermes-example-gallery',
    'hermes-skills-lab', 'hermes-memory-lab', 'hermes-profiles-lab',
    'hermes-cron-automation-lab', 'hermes-gateway-lab', 'hermes-mcp-lab',
    'hermes-troubleshooting-lab', 'hermes-prompting-lab', 'hermes-profile-builder-lab',
    'hermes-plugin-builder-lab', 'hermes-docs-sync-tutor', 'hermes-assessment-certifier',
    'hermes-capstone-orchestrator', 'hermes-learning-progress',
]
REQUIRED_PLUGIN_FILES = ('README.md', 'plugin.yaml', '__init__.py', 'schemas.py',
                         'tools.py', 'commands.py', 'manifest.json')
REQUIRED_PROFILE_FILES = ('README.md', 'PROFILE.md', 'SOUL.md', 'config.public.yaml',
                          'distribution.yaml', 'manifest.json')
PROFILE_PACKAGE = REPO / 'profiles' / 'hermes-agent-tutorial'


def plugin_static_errors(plugin_dir: Path, rel: str) -> list[str]:
    return [f'{rel}: missing {name}' for name in REQUIRED_PLUGIN_FILES
            if not (plugin_dir / name).is_file()]


def handler_call_errors(name: str, probe: dict, rel: str) -> list[str]:
    errors = []
    for tool, call in probe['tool_calls'].items():
        output = call.get('output') or {}
        if 'success' not in output or output.get('plugin') != name:
            errors.append(f'{rel}: tool {tool} did not return a success/plugin payload')
        if 'success' not in (call.get('bad_input') or {}):
            errors.append(f'{rel}: tool {tool} bad-input path missing success payload')
    for command, call in probe['command_calls'].items():
        if not str(call.get('output') or '').strip():
            errors.append(f'{rel}: command {command} returned empty output')
    return errors


def plugin_runtime_errors(plugin_dir: Path, rel: str) -> list[str]:
    declared = yaml.safe_load((plugin_dir / 'plugin.yaml').read_text(encoding='utf-8'))
    probe = probe_plugin_package(plugin_dir, payload=DEFAULT_PAYLOAD)
    if not probe['plugin'].get('enabled'):
        return [f"{rel}: real manager did not enable plugin: {probe['plugin'].get('error')}"]
    errors = check_registration_parity(declared, probe, rel)
    errors += handler_call_errors(str(declared.get('name') or ''), probe, rel)
    return errors


def profile_errors() -> list[str]:
    errors = [f'profiles/hermes-agent-tutorial: missing {name}'
              for name in REQUIRED_PROFILE_FILES
              if not (PROFILE_PACKAGE / name).is_file()]
    if errors:
        return errors
    with tempfile.TemporaryDirectory(prefix='tutorial-profile-') as tmp:
        home = Path(tmp) / 'home'
        home.mkdir()
        install = install_profile(home, PROFILE_PACKAGE, 'tutorial-suite-check')
        if install.returncode != 0:
            return ['profiles/hermes-agent-tutorial: real install failed: '
                    + (install.stdout + install.stderr).strip()[:300]]
        info = run_hermes(home, 'profile', 'info', 'tutorial-suite-check')
        if info.returncode != 0:
            return ['profiles/hermes-agent-tutorial: profile info failed: '
                    + (info.stdout + info.stderr).strip()[:300]]
    return []


def curriculum_errors() -> list[str]:
    path = REPO / 'plugins' / 'hermes-tutorial-compass' / 'data' / 'curriculum_graph.json'
    if not path.is_file():
        return ['hermes-tutorial-compass: missing data/curriculum_graph.json']
    data = json.loads(path.read_text(encoding='utf-8'))
    plugins = {item.get('plugin') for item in data if isinstance(item, dict)}
    levels = {str(item.get('level_key')) for item in data if isinstance(item, dict)}
    errors = [f'hermes-tutorial-compass curriculum missing plugin {name}'
              for name in EXPECTED_PLUGINS if name not in plugins]
    errors += [f'hermes-tutorial-compass curriculum missing level {level}'
               for level in ('0', '1', '2', '3', '4') if level not in levels]
    return errors


def main() -> int:
    require_runtime()
    errors: list[str] = []
    for name in EXPECTED_PLUGINS:
        plugin_dir = REPO / 'plugins' / name
        rel = f'plugins/{name}'
        if not plugin_dir.is_dir():
            errors.append(f'{rel}: missing plugin directory')
            continue
        static = plugin_static_errors(plugin_dir, rel)
        errors += static or plugin_runtime_errors(plugin_dir, rel)
    errors += profile_errors()
    errors += curriculum_errors()
    if errors:
        print('Tutorial suite validation failed:', file=sys.stderr)
        for error in errors:
            print(f'- {error}', file=sys.stderr)
        return 1
    print(f'Tutorial suite validation passed ({len(EXPECTED_PLUGINS)} plugins, real runtime).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
