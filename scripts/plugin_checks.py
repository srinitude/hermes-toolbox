"""Canonical completeness and structure checks for public plugin packages."""
from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path

import yaml

from package_checks import (
    check_package_manifest, check_registration_parity, find_placeholders,
)
from plugin_probe_policy import load_plugin_probe_policy
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


def tool_behavior_error(
    call: dict, expected: str, check_normal: bool, check_malformed: bool,
) -> str | None:
    error = base_call_error(call)
    if error:
        return error
    output = call.get('output')
    bad_input = call.get('bad_input')
    if check_normal and (
            not isinstance(output, dict) or output.get('success') is not True):
        return 'normal input did not return JSON success=true'
    if check_malformed and (
            not isinstance(bad_input, dict) or bad_input.get('success') is not False):
        return 'bad input did not return JSON success=false'
    normal_identity = output.get('plugin') if isinstance(output, dict) else None
    malformed_identity = bad_input.get('plugin') if isinstance(bad_input, dict) else None
    if check_normal and normal_identity != expected:
        return f'normal result did not report declared plugin identity {expected}'
    if check_malformed and malformed_identity != expected:
        return f'malformed result did not report declared plugin identity {expected}'
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


def tool_call_errors(probe: dict, rel: str, expected: str,
                     policy: dict) -> list[str]:
    normal = set(policy['normal_tools'])
    malformed = set(policy['malformed_tools'])
    errors = []
    for name, call in (probe.get('tool_calls') or {}).items():
        error = tool_behavior_error(
            call, expected, name in normal, name in malformed)
        if error:
            errors.append(f'{rel}: tool {name} {error}')
    return errors


def handler_errors(probe: dict, rel: str, expected: str,
                   policy: dict) -> list[str]:
    return (tool_call_errors(probe, rel, expected, policy)
            + call_errors(probe.get('command_calls') or {}, 'command', rel,
                          command_behavior_error, expected))


def registration_errors(pkg: Path, rel: str,
                        policy: dict | None = None) -> list[str]:
    declared = yaml.safe_load((pkg / 'plugin.yaml').read_text(encoding='utf-8'))
    selected = policy or {
        'normal_tools': [], 'malformed_tools': [], 'call_commands': [],
        'payload': {},
    }
    try:
        probe = probe_plugin_package(
            pkg, payload=selected['payload'],
            normal_tools=selected['normal_tools'],
            malformed_tools=selected['malformed_tools'],
            call_commands=selected['call_commands'])
    except (Exception, SystemExit) as exc:
        return [f'{rel}: real manager probe failed: {exc}']
    plugin = probe.get('plugin') or {}
    if not plugin.get('enabled'):
        return [f"{rel}: real manager did not enable plugin: {plugin.get('error')}"]
    expected = str(declared.get('name', ''))
    return (check_registration_parity(declared, probe, rel)
            + handler_errors(probe, rel, expected, selected))


def selection_errors(declared: set, selected: set, label: str, rel: str) -> list[str]:
    missing = declared - selected
    extra = selected - declared
    errors = []
    if missing:
        errors.append(f"{rel}: unprobed {label}: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"{rel}: policy selects undeclared {label}: {', '.join(sorted(extra))}")
    return errors


def policy_declaration_errors(declared: dict, policy: dict, rel: str) -> list[str]:
    tools = set(declared.get('provides_tools') or [])
    selected_tools = set(policy['normal_tools']) | set(policy['malformed_tools'])
    commands = set(declared.get('provides_commands') or [])
    called_commands = set(policy['call_commands'])
    skipped_commands = set(policy['skip_commands'])
    errors = selection_errors(tools, selected_tools, 'tools', rel)
    errors += selection_errors(commands, called_commands | skipped_commands, 'commands', rel)
    overlap = called_commands & skipped_commands
    if overlap:
        errors.append(f"{rel}: commands both called and skipped: {', '.join(sorted(overlap))}")
    return errors


def governed_registration_errors(pkg: Path, rel: str, repo: Path) -> list[str]:
    name = Path(rel).name
    policy, error = load_plugin_probe_policy(repo, name)
    if error or policy is None:
        return [f'{rel}: {error or "missing plugin probe policy"}']
    declared = yaml.safe_load((pkg / 'plugin.yaml').read_text(encoding='utf-8'))
    errors = policy_declaration_errors(declared, policy, rel)
    return errors or registration_errors(pkg, rel, policy)


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
    return errors or governed_registration_errors(pkg, rel, repo)
