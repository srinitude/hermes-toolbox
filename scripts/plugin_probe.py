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


def hook_states(manager) -> list[str]:
    return sorted({
        hook
        for loaded in manager._plugins.values()
        if getattr(loaded.manifest, 'source', '') == 'user'
        for hook in getattr(loaded, 'hooks_registered', [])
    })


def module_registration_key(module: str, module_keys: list[tuple[str, str]]) -> str:
    matches = {
        key for root, key in module_keys
        if module == root or module.startswith(f'{root}.')
    }
    return next(iter(matches)) if len(matches) == 1 else ''


def cli_registration_key(entry: dict, module_keys: list[tuple[str, str]]) -> str:
    modules = [
        getattr(entry.get(field), '__module__', '')
        for field in ('setup_fn', 'handler_fn') if entry.get(field) is not None
    ]
    keys = [module_registration_key(module, module_keys) for module in modules]
    return keys[0] if keys and all(keys) and len(set(keys)) == 1 else ''


def cli_command_states(manager) -> dict[str, dict[str, str]]:
    module_keys = [
        (loaded.module.__name__, key)
        for key, loaded in manager._plugins.items() if loaded.module is not None
    ]
    return {
        name: {'plugin': str(entry.get('plugin') or ''),
               'key': cli_registration_key(entry, module_keys)}
        for name, entry in sorted(manager._cli_commands.items())
    }


def parse_json_output(raw) -> dict:
    if not isinstance(raw, str):
        return {'raw': repr(raw)[:400]}
    try:
        parsed = json.loads(raw)
    except ValueError:
        return {'raw': raw[:400]}
    return parsed if isinstance(parsed, dict) else {'raw': raw[:400]}


def call_tool(registry, name: str, payload: dict,
              call_normal: bool, call_malformed: bool) -> dict:
    entry = registry.get_entry(name)
    if entry is None:
        return {'registered': False}
    result = {'registered': True, 'toolset': entry.toolset,
              'schema_name': (entry.schema or {}).get('name')}
    if call_normal:
        try:
            result['output'] = parse_json_output(entry.handler(dict(payload)))
        except Exception as exc:
            result['error'] = f'{type(exc).__name__}: {exc}'
            return result
    if call_malformed:
        try:
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


def unique_names(spec: dict, key: str) -> list[str]:
    names = list(spec.get(key) or [])
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise ValueError(f"duplicate {key} selection: {', '.join(duplicates)}")
    return names


def build_report(manager, registry, spec: dict) -> dict:
    payload = spec.get('payload') or {}
    command_args = spec.get('command_args', 'status')
    legacy = set(unique_names(spec, 'call_tools'))
    normal = set(unique_names(spec, 'normal_tools')) | legacy
    malformed = set(unique_names(spec, 'malformed_tools')) | legacy
    commands = unique_names(spec, 'call_commands')
    tools = sorted(normal | malformed)
    return {
        'plugins': plugin_states(manager),
        'tools': sorted(manager._plugin_tool_names),
        'commands': sorted(manager._plugin_commands),
        'hooks': hook_states(manager),
        'cli_commands': cli_command_states(manager),
        'skills': skill_states(manager),
        'tool_calls': {name: call_tool(registry, name, payload,
                                      name in normal, name in malformed)
                       for name in tools},
        'command_calls': {name: call_command(manager, name, command_args)
                          for name in commands},
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
