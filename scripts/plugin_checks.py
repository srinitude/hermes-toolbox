"""Canonical completeness and structure checks for public plugin packages."""
from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path

import yaml

from package_checks import (
    check_package_manifest, check_registration_parity, find_placeholders,
)
from real_runtime import probe_plugin_package
from toolbox_common import check_child_file

SCRIPTS = Path(__file__).parent
REQUIRED_PLUGIN_FILES = ('README.md', 'plugin.yaml', '__init__.py', 'manifest.json')


@lru_cache(maxsize=1)
def load_structure_checker():
    spec = importlib.util.spec_from_file_location(
        'verify_python_structure', SCRIPTS / 'verify-python-structure.py')
    if spec is None or spec.loader is None:
        raise RuntimeError('could not load Python structure checker')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plugin_yaml_errors(pkg: Path, rel: str) -> list[str]:
    try:
        data = yaml.safe_load((pkg / 'plugin.yaml').read_text(encoding='utf-8'))
    except (OSError, yaml.YAMLError) as exc:
        return [f'{rel}/plugin.yaml: invalid YAML: {exc}']
    if not isinstance(data, dict):
        return [f'{rel}/plugin.yaml: must be a mapping']
    errors = []
    if data.get('name') != Path(rel).name:
        errors.append(f'{rel}/plugin.yaml: name must match directory')
    if data.get('kind') != 'standalone':
        errors.append(f'{rel}/plugin.yaml: kind must be standalone')
    for skill in data.get('provides_skills') or []:
        _, error = check_child_file(pkg, f'skills/{skill}/SKILL.md', 'bundled skill')
        if error:
            errors.append(
                f'{rel}: bundled skill {skill!r} missing skills/{skill}/SKILL.md')
    return errors


def structure_errors(pkg: Path, repo: Path) -> list[str]:
    checker = load_structure_checker()
    errors: list[str] = []
    for path in sorted(pkg.rglob('*.py')):
        if '__pycache__' not in path.parts:
            errors.extend(checker.check_file(path.resolve(), repo.resolve()))
    return errors


def base_call_error(call: dict) -> str | None:
    if call.get('error'):
        return str(call['error'])
    if not call.get('registered'):
        return 'was not callable'
    return None


def tool_behavior_error(call: dict, expected: str) -> str | None:
    output = call.get('output')
    bad_input = call.get('bad_input')
    if not isinstance(output, dict) or output.get('success') is not True:
        return 'normal input did not return JSON success=true'
    if not isinstance(bad_input, dict) or bad_input.get('success') is not False:
        return 'bad input did not return JSON success=false'
    identities = [item.get('plugin') for item in (output, bad_input) if 'plugin' in item]
    if any(identity != expected for identity in identities):
        return f'did not report declared plugin identity {expected}'
    return None


def command_behavior_error(call: dict, expected: str) -> str | None:
    output = call.get('output')
    return None if isinstance(output, str) and output.strip() else 'returned empty output'


def call_errors(calls: dict, label: str, rel: str, behavior,
                expected: str) -> list[str]:
    errors = []
    for name, call in calls.items():
        error = base_call_error(call) or behavior(call, expected)
        if error:
            errors.append(f'{rel}: {label} {name} {error}')
    return errors


def handler_errors(probe: dict, rel: str, expected: str) -> list[str]:
    return (call_errors(probe.get('tool_calls') or {}, 'tool', rel,
                        tool_behavior_error, expected)
            + call_errors(probe.get('command_calls') or {}, 'command', rel,
                          command_behavior_error, expected))


def registration_errors(pkg: Path, rel: str) -> list[str]:
    declared = yaml.safe_load((pkg / 'plugin.yaml').read_text(encoding='utf-8'))
    try:
        probe = probe_plugin_package(pkg)
    except (Exception, SystemExit) as exc:
        return [f'{rel}: real manager probe failed: {exc}']
    plugin = probe.get('plugin') or {}
    if not plugin.get('enabled'):
        return [f"{rel}: real manager did not enable plugin: {plugin.get('error')}"]
    expected = str(declared.get('name', ''))
    return (check_registration_parity(declared, probe, rel)
            + handler_errors(probe, rel, expected))


def plugin_static_errors(pkg: Path, rel: str, repo: Path) -> list[str]:
    errors = [f'{rel}: missing {name}' for name in REQUIRED_PLUGIN_FILES
              if not (pkg / name).is_file()]
    if errors:
        return errors
    errors += plugin_yaml_errors(pkg, rel)
    errors += check_package_manifest(pkg, rel, 'plugin')
    errors += [f'{rel}/{error}' for error in find_placeholders(pkg)]
    return errors + structure_errors(pkg, repo)


def plugin_package_errors(pkg: Path, rel: str, repo: Path) -> list[str]:
    errors = plugin_static_errors(pkg, rel, repo)
    return errors or registration_errors(pkg, rel)
