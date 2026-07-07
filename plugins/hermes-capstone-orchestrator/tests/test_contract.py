from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

import yaml

PLUGIN_DIR = Path(__file__).resolve().parents[1]


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
        assert ':' not in name
        assert Path(path).exists()
        self.skills[name] = {'path': Path(path), 'description': description}


def load_plugin():
    spec = importlib.util.spec_from_file_location(f'{PLUGIN_DIR.name}_module', PLUGIN_DIR / '__init__.py')
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_manifest_matches_directory():
    manifest = yaml.safe_load((PLUGIN_DIR / 'plugin.yaml').read_text())
    assert manifest['name'] == PLUGIN_DIR.name
    assert manifest['kind'] == 'standalone'
    assert manifest['version'] == '0.1.0'
    assert isinstance(manifest.get('provides_tools'), list)


def test_register_contract_and_handlers(tmp_path, monkeypatch):
    monkeypatch.setenv('HERMES_HOME', str(tmp_path / 'hermes-home'))
    module = load_plugin()
    ctx = FakeCtx()
    module.register(ctx)
    manifest = yaml.safe_load((PLUGIN_DIR / 'plugin.yaml').read_text())
    assert set(manifest.get('provides_tools', [])) == set(ctx.tools)
    assert ctx.commands
    assert ctx.skills
    for tool_name, entry in ctx.tools.items():
        assert entry['toolset'] == 'tutorial'
        assert entry['schema']['name'] == tool_name
        result = json.loads(entry['handler']({'query': 'profile safety plugin', 'term': 'profile', 'lesson_id': 'test-lesson', 'status': 'completed', 'answer': 'A profile is not a sandbox and plugins need validation.'}))
        assert 'success' in result
        assert result['plugin'] == PLUGIN_DIR.name
        bad = json.loads(entry['handler']('not-an-object'))
        assert bad['success'] is False or bad.get('error') or bad.get('plugin') == PLUGIN_DIR.name
    for command, entry in ctx.commands.items():
        output = entry['handler']('status')
        assert isinstance(output, str)
        assert output.strip()
