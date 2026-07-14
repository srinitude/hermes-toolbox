#!/usr/bin/env python3
"""Validate the optional public tutorial suite against the real Hermes runtime.

The suite is valid when it is entirely absent from the public manifest, or when
all tutorial plugins and the tutorial profile are present and pass real runtime
checks. Partial publication fails closed.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from plugin_checks import governed_registration_errors  # noqa: E402
from real_runtime import install_profile, require_runtime, run_hermes  # noqa: E402

EXPECTED_PLUGINS = {
    'hermes-tutorial-compass', 'hermes-setup-coach', 'hermes-concept-glossary',
    'hermes-command-lab', 'hermes-accessibility-coach', 'hermes-tools-lab',
    'hermes-config-lab', 'hermes-safety-sandbox-lab', 'hermes-example-gallery',
    'hermes-skills-lab', 'hermes-memory-lab', 'hermes-profiles-lab',
    'hermes-cron-automation-lab', 'hermes-gateway-lab', 'hermes-mcp-lab',
    'hermes-troubleshooting-lab', 'hermes-prompting-lab', 'hermes-profile-builder-lab',
    'hermes-plugin-builder-lab', 'hermes-docs-sync-tutor', 'hermes-assessment-certifier',
    'hermes-capstone-orchestrator', 'hermes-learning-progress',
}
REQUIRED_PLUGIN_FILES = ('README.md', 'plugin.yaml', '__init__.py', 'schemas.py',
                         'tools.py', 'commands.py', 'manifest.json')
REQUIRED_PROFILE_FILES = ('README.md', 'PROFILE.md', 'SOUL.md', 'config.public.yaml',
                          'distribution.yaml', 'manifest.json')
PROFILE_NAME = 'hermes-agent-tutorial'


def manifest_names(kind: str) -> set[str]:
    data = json.loads((REPO / 'inventory/public-manifest.json').read_text(encoding='utf-8'))
    names = set()
    for entry in data.get(kind, []):
        parts = Path(entry['path']).parts
        if len(parts) > 1:
            names.add(parts[1])
    return names


def plugin_static_errors(plugin_dir: Path, rel: str) -> list[str]:
    return [f'{rel}: missing {name}' for name in REQUIRED_PLUGIN_FILES
            if not (plugin_dir / name).is_file()]


def plugin_runtime_errors(name: str) -> list[str]:
    plugin_dir = REPO / 'plugins' / name
    rel = f'plugins/{name}'
    static = plugin_static_errors(plugin_dir, rel)
    return static or governed_registration_errors(plugin_dir, rel, REPO)


def profile_errors() -> list[str]:
    package = REPO / 'profiles' / PROFILE_NAME
    errors = [f'profiles/{PROFILE_NAME}: missing {name}' for name in REQUIRED_PROFILE_FILES
              if not (package / name).is_file()]
    if errors:
        return errors
    with tempfile.TemporaryDirectory(prefix='tutorial-profile-') as tmp:
        home = Path(tmp) / 'home'
        home.mkdir()
        install = install_profile(home, package, 'tutorial-suite-check')
        if install.returncode != 0:
            return [f'profiles/{PROFILE_NAME}: real install failed: '
                    + (install.stdout + install.stderr).strip()[:300]]
        info = run_hermes(home, 'profile', 'info', 'tutorial-suite-check')
    return [] if info.returncode == 0 else [f'profiles/{PROFILE_NAME}: profile info failed']


def curriculum_errors() -> list[str]:
    path = REPO / 'plugins/hermes-tutorial-compass/data/curriculum_graph.json'
    if not path.is_file():
        return ['hermes-tutorial-compass: missing data/curriculum_graph.json']
    data = json.loads(path.read_text(encoding='utf-8'))
    plugins = {item.get('plugin') for item in data if isinstance(item, dict)}
    levels = {str(item.get('level_key')) for item in data if isinstance(item, dict)}
    errors = [f'curriculum missing plugin {name}' for name in EXPECTED_PLUGINS
              if name not in plugins]
    errors += [f'curriculum missing level {level}' for level in ('0', '1', '2', '3', '4')
               if level not in levels]
    return errors


def publication_errors(plugins: set[str], profiles: set[str]) -> list[str]:
    tutorial_plugins = plugins & EXPECTED_PLUGINS
    tutorial_profile = PROFILE_NAME in profiles
    if not tutorial_plugins and not tutorial_profile:
        return []
    errors = [f'tutorial suite is partial; missing plugin {name}'
              for name in sorted(EXPECTED_PLUGINS - tutorial_plugins)]
    if not tutorial_profile:
        errors.append(f'tutorial suite is partial; missing profile {PROFILE_NAME}')
    return errors


def main() -> int:
    plugins, profiles = manifest_names('plugins'), manifest_names('profiles')
    errors = publication_errors(plugins, profiles)
    if not errors and not (plugins & EXPECTED_PLUGINS):
        print('Tutorial suite validation passed (suite intentionally unpublished).')
        return 0
    if not errors:
        require_runtime()
        for name in sorted(EXPECTED_PLUGINS):
            errors += plugin_runtime_errors(name)
        errors += profile_errors() + curriculum_errors()
    if errors:
        print('Tutorial suite validation failed:', file=sys.stderr)
        for error in errors:
            print(f'- {error}', file=sys.stderr)
        return 1
    print(f'Tutorial suite validation passed ({len(EXPECTED_PLUGINS)} plugins, real runtime).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
