#!/usr/bin/env python3
"""Probe user plugins with the real Hermes PluginManager.

Runs inside the Hermes Agent virtualenv with HERMES_HOME pointing at a
prepared temporary home. Reads a JSON spec file (argv[1]) carrying the
Hermes source path, the tools/commands to exercise, and the call payload,
then prints a JSON discovery report to stdout.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def plugin_states(manager) -> dict:
    states = {}
    for key, loaded in manager._plugins.items():
        manifest = loaded.manifest
        if getattr(manifest, 'source', '') != 'user':
            continue
        states[key] = {'name': manifest.name, 'enabled': bool(loaded.enabled),
                       'error': getattr(loaded, 'error', None)}
    return states


def skill_states(manager) -> dict:
    states = {}
    for qualified, meta in manager._plugin_skills.items():
        path = Path(str(meta.get('path', '')))
        states[qualified] = {
            'path': str(path), 'plugin': meta.get('plugin'),
            'is_skill_file': path.is_file() and path.name == 'SKILL.md',
        }
    return states


def parse_json_output(raw) -> dict:
    if not isinstance(raw, str):
        return {'raw': repr(raw)[:400]}
    try:
        parsed = json.loads(raw)
    except ValueError:
        return {'raw': raw[:400]}
    return parsed if isinstance(parsed, dict) else {'raw': raw[:400]}


def call_tool(registry, name: str, payload: dict) -> dict:
    entry = registry.get_entry(name)
    if entry is None:
        return {'registered': False}
    result = {'registered': True, 'toolset': entry.toolset,
              'schema_name': (entry.schema or {}).get('name')}
    try:
        result['output'] = parse_json_output(entry.handler(dict(payload)))
        result['bad_input'] = parse_json_output(entry.handler('not-an-object'))
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
    return result


def call_command(manager, name: str, args: str) -> dict:
    entry = manager._plugin_commands.get(name)
    if entry is None:
        return {'registered': False}
    try:
        output = entry['handler'](args)
    except Exception as exc:
        return {'registered': True, 'error': f'{type(exc).__name__}: {exc}'}
    return {'registered': True,
            'output': output if isinstance(output, str) else ''}


def build_report(manager, registry, spec: dict) -> dict:
    payload = spec.get('payload') or {}
    command_args = spec.get('command_args', 'status')
    return {
        'plugins': plugin_states(manager),
        'tools': sorted(manager._plugin_tool_names),
        'commands': sorted(manager._plugin_commands),
        'skills': skill_states(manager),
        'tool_calls': {name: call_tool(registry, name, payload)
                       for name in spec.get('call_tools') or []},
        'command_calls': {name: call_command(manager, name, command_args)
                          for name in spec.get('call_commands') or []},
    }


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
    sys.path.insert(0, spec['hermes_src'])
    from hermes_cli.plugins import PluginManager
    from tools.registry import registry
    manager = PluginManager()
    manager.discover_and_load()
    json.dump(build_report(manager, registry, spec), sys.stdout)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
