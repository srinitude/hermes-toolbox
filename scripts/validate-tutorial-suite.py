#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
import py_compile
import re
import sys
import tempfile
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
REQUIRED_EXCLUDED = {'env', 'auth', 'tokens', 'memories', 'sessions', 'logs', 'cache', 'state', 'pairing', 'runtime'}
EXPECTED_PLUGINS = [
    'hermes-tutorial-compass', 'hermes-setup-coach', 'hermes-concept-glossary', 'hermes-command-lab', 'hermes-accessibility-coach',
    'hermes-tools-lab', 'hermes-config-lab', 'hermes-safety-sandbox-lab', 'hermes-example-gallery', 'hermes-skills-lab',
    'hermes-memory-lab', 'hermes-profiles-lab', 'hermes-cron-automation-lab', 'hermes-gateway-lab', 'hermes-mcp-lab',
    'hermes-troubleshooting-lab', 'hermes-prompting-lab', 'hermes-profile-builder-lab', 'hermes-plugin-builder-lab',
    'hermes-docs-sync-tutor', 'hermes-assessment-certifier', 'hermes-capstone-orchestrator', 'hermes-learning-progress',
]
REQUIRED_PLUGIN_FILES = {'README.md', 'plugin.yaml', '__init__.py', 'schemas.py', 'tools.py', 'commands.py', 'manifest.json'}
FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.S)


class FakeCtx:
    def __init__(self):
        self.tools = {}
        self.commands = {}
        self.skills = {}

    def register_tool(self, name, toolset, schema, handler, **kwargs):
        self.tools[name] = {'toolset': toolset, 'schema': schema, 'handler': handler}

    def register_command(self, name, handler, description='', args_hint=''):
        self.commands[name] = {'handler': handler, 'description': description, 'args_hint': args_hint}

    def register_skill(self, name, path, description=''):
        self.skills[name] = {'path': Path(path), 'description': description}


def parse_frontmatter(path: Path) -> dict[str, str] | None:
    text = path.read_text(encoding='utf-8')
    match = FRONTMATTER_RE.search(text)
    if not match:
        return None
    data = {}
    for line in match.group(1).splitlines():
        if ':' in line and not line.startswith(' '):
            key, value = line.split(':', 1)
            data[key.strip()] = value.strip().strip('"\'')
    return data


def load_plugin(plugin_dir: Path):
    spec = importlib.util.spec_from_file_location(f'{plugin_dir.name}_module', plugin_dir / '__init__.py')
    if not spec or not spec.loader:
        raise RuntimeError(f'cannot load {plugin_dir}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_plugin(plugin_dir: Path, errors: list[str]) -> None:
    rel = plugin_dir.relative_to(REPO).as_posix()
    for filename in REQUIRED_PLUGIN_FILES:
        if not (plugin_dir / filename).is_file():
            errors.append(f'{rel}: missing {filename}')
    if errors and any(e.startswith(rel + ': missing') for e in errors):
        return
    manifest = json.loads((plugin_dir / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('sanitized') is not True:
        errors.append(f'{rel}/manifest.json: sanitized must be true')
    if manifest.get('type') != 'plugin':
        errors.append(f'{rel}/manifest.json: type must be plugin')
    if not REQUIRED_EXCLUDED.issubset(set(manifest.get('excluded_categories', []))):
        errors.append(f'{rel}/manifest.json: missing required excluded categories')
    if not manifest.get('source_gate'):
        errors.append(f'{rel}/manifest.json: missing source_gate')
    plugin_yaml = yaml.safe_load((plugin_dir / 'plugin.yaml').read_text(encoding='utf-8')) or {}
    if plugin_yaml.get('name') != plugin_dir.name:
        errors.append(f'{rel}/plugin.yaml: name must match directory')
    if plugin_yaml.get('kind') != 'standalone':
        errors.append(f'{rel}/plugin.yaml: kind must be standalone')
    for py in plugin_dir.glob('*.py'):
        py_compile.compile(str(py), doraise=True)
    for skill_md in plugin_dir.glob('skills/*/SKILL.md'):
        fm = parse_frontmatter(skill_md)
        srel = skill_md.relative_to(REPO).as_posix()
        if not fm:
            errors.append(f'{srel}: missing YAML frontmatter')
            continue
        for key in ['name', 'description', 'version', 'author', 'license']:
            if not fm.get(key):
                errors.append(f'{srel}: missing frontmatter key {key}')
        text = skill_md.read_text(encoding='utf-8')
        if '## When to Use' not in text and '## When to use' not in text:
            errors.append(f'{srel}: missing When to Use section')
        if len(text.splitlines()) < 40:
            errors.append(f'{srel}: skill too short')
    with tempfile.TemporaryDirectory(prefix='hermes-tutorial-suite-') as tmp:
        old_home = os.environ.get('HERMES_HOME')
        os.environ['HERMES_HOME'] = tmp
        try:
            module = load_plugin(plugin_dir)
            ctx = FakeCtx()
            module.register(ctx)
            expected_tools = set(plugin_yaml.get('provides_tools') or [])
            if expected_tools != set(ctx.tools):
                errors.append(f'{rel}: registered tools do not match plugin.yaml')
            for tool_name, entry in ctx.tools.items():
                schema = entry['schema']
                if schema.get('name') != tool_name:
                    errors.append(f'{rel}: schema name mismatch for {tool_name}')
                result = json.loads(entry['handler']({'query': 'profile safety plugin', 'term': 'profile', 'lesson_id': 'test-lesson', 'status': 'completed', 'answer': 'A profile is not a sandbox and plugins need validation.'}))
                if 'success' not in result or result.get('plugin') != plugin_dir.name:
                    errors.append(f'{rel}: handler output missing success/plugin for {tool_name}')
                bad = json.loads(entry['handler']('not-an-object'))
                if 'success' not in bad:
                    errors.append(f'{rel}: bad-input output missing success for {tool_name}')
            if set(plugin_yaml.get('provides_commands') or []) != set(ctx.commands):
                errors.append(f'{rel}: registered commands do not match plugin.yaml')
            for command, entry in ctx.commands.items():
                output = entry['handler']('status')
                if not isinstance(output, str) or not output.strip():
                    errors.append(f'{rel}: command {command} returned empty output')
            for skill, entry in ctx.skills.items():
                if not entry['path'].is_file():
                    errors.append(f'{rel}: registered skill path missing for {skill}')
        finally:
            if old_home is None:
                os.environ.pop('HERMES_HOME', None)
            else:
                os.environ['HERMES_HOME'] = old_home


def validate_profile(errors: list[str]) -> None:
    root = REPO / 'profiles' / 'hermes-agent-tutorial'
    required = {'README.md', 'PROFILE.md', 'SOUL.md', 'config.public.yaml', 'distribution.yaml', 'manifest.json'}
    for filename in required:
        if not (root / filename).is_file():
            errors.append(f'profiles/hermes-agent-tutorial: missing {filename}')
    if (root / 'manifest.json').is_file():
        manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
        if manifest.get('sanitized') is not True or manifest.get('type') != 'profile':
            errors.append('profiles/hermes-agent-tutorial/manifest.json: invalid sanitized profile manifest')
        if not REQUIRED_EXCLUDED.issubset(set(manifest.get('excluded_categories', []))):
            errors.append('profiles/hermes-agent-tutorial/manifest.json: missing required excluded categories')


def validate_compass(errors: list[str]) -> None:
    path = REPO / 'plugins' / 'hermes-tutorial-compass' / 'data' / 'curriculum_graph.json'
    if not path.is_file():
        errors.append('hermes-tutorial-compass: missing data/curriculum_graph.json')
        return
    data = json.loads(path.read_text(encoding='utf-8'))
    plugins = {item.get('plugin') for item in data if isinstance(item, dict)}
    levels = {str(item.get('level_key')) for item in data if isinstance(item, dict)}
    missing = [plugin for plugin in EXPECTED_PLUGINS if plugin not in plugins]
    if missing:
        errors.append(f'hermes-tutorial-compass curriculum missing plugins: {missing}')
    for level in {'0', '1', '2', '3', '4'}:
        if level not in levels:
            errors.append(f'hermes-tutorial-compass curriculum missing level {level}')


def main() -> int:
    errors: list[str] = []
    for plugin in EXPECTED_PLUGINS:
        plugin_dir = REPO / 'plugins' / plugin
        if not plugin_dir.is_dir():
            errors.append(f'plugins/{plugin}: missing plugin directory')
        else:
            validate_plugin(plugin_dir, errors)
    validate_profile(errors)
    validate_compass(errors)
    if errors:
        print('Tutorial suite validation failed:', file=sys.stderr)
        for err in errors:
            print(f'- {err}', file=sys.stderr)
        return 1
    print('Tutorial suite validation passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
