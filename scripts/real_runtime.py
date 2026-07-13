#!/usr/bin/env python3
"""Real Hermes runtime access for package validation: discovery via the
installed PluginManager and profile installs via the hermes CLI. No fakes."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

DEFAULT_HERMES_SRC = Path.home() / '.hermes' / 'hermes-agent'
HERMES_SRC = Path(os.environ.get('HERMES_RUNTIME_SRC', DEFAULT_HERMES_SRC))
HERMES_VENV_PYTHON = HERMES_SRC / 'venv' / 'bin' / 'python'
HERMES_BIN = shutil.which('hermes') or str(Path.home() / '.local' / 'bin' / 'hermes')
PROBE_SCRIPT = Path(__file__).resolve().parent / 'plugin_probe.py'
DEFAULT_PAYLOAD = {
    'message': 'probe message', 'query': 'profile safety plugin',
    'term': 'profile', 'lesson_id': 'test-lesson', 'status': 'completed',
    'answer': 'A profile is not a sandbox and plugins need validation.',
}


def runtime_blocker() -> str | None:
    """Return why the real Hermes runtime is unavailable, or None if usable."""
    if not HERMES_VENV_PYTHON.is_file():
        return f'missing Hermes virtualenv python: {HERMES_VENV_PYTHON}'
    if not (HERMES_SRC / 'hermes_cli' / 'plugins.py').is_file():
        return f'missing Hermes Agent source tree: {HERMES_SRC}'
    if not Path(HERMES_BIN).is_file():
        return 'missing hermes CLI executable on PATH'
    return None


def require_runtime() -> None:
    blocker = runtime_blocker()
    if blocker:
        raise SystemExit(f'real Hermes runtime unavailable: {blocker}')


def hermes_env(home: Path) -> dict[str, str]:
    env = dict(os.environ)
    env['HERMES_HOME'] = str(home)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    return env


def write_enabled_config(home: Path, enabled: list[str]) -> None:
    (home / 'config.yaml').write_text(
        yaml.safe_dump({'plugins': {'enabled': enabled}}), encoding='utf-8')


def run_probe(home: Path, spec: dict) -> dict:
    require_runtime()
    spec = {'hermes_src': str(HERMES_SRC), **spec}
    with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as fh:
        json.dump(spec, fh)
        spec_path = fh.name
    try:
        result = subprocess.run(
            [str(HERMES_VENV_PYTHON), str(PROBE_SCRIPT), spec_path],
            capture_output=True, text=True, env=hermes_env(home))
    finally:
        os.unlink(spec_path)
    if result.returncode != 0:
        raise SystemExit(f'plugin probe failed: {result.stderr.strip()[:500]}')
    return json.loads(result.stdout)


def _unique_names(values, label: str) -> list[str]:
    names = list(values or [])
    duplicates = sorted({name for name in names if names.count(name) > 1})
    if duplicates:
        raise SystemExit(f"duplicate {label} selection: {', '.join(duplicates)}")
    return names


def _validate_declarations(declared: dict) -> None:
    fields = (
        ('provides_tools', 'tool'), ('provides_commands', 'command'),
        ('provides_hooks', 'hook'), ('provides_cli_commands', 'CLI command'),
        ('provides_skills', 'skill'),
    )
    for field, label in fields:
        _unique_names(declared.get(field), f'declared {label}')


def _selected_calls(
    declared: dict,
    normal_tools: list[str] | None,
    malformed_tools: list[str] | None,
    call_commands: list[str] | None,
) -> tuple[list[str], list[str], list[str]]:
    legacy = normal_tools is None and malformed_tools is None and call_commands is None
    tools = _unique_names(declared.get('provides_tools'), 'declared tool')
    commands = _unique_names(declared.get('provides_commands'), 'declared command')
    normal = tools if legacy else _unique_names(normal_tools, 'normal tool')
    malformed = tools if legacy else _unique_names(malformed_tools, 'malformed tool')
    selected_commands = commands if legacy else _unique_names(call_commands, 'command')
    return normal, malformed, selected_commands


def probe_plugin_package(
    pkg_dir: Path,
    payload: dict | None = None,
    *,
    normal_tools: list[str] | None = None,
    malformed_tools: list[str] | None = None,
    call_commands: list[str] | None = None,
) -> dict:
    """Probe one package twice with real discovery: disabled, then enabled."""
    pkg_dir = Path(pkg_dir)
    declared = yaml.safe_load((pkg_dir / 'plugin.yaml').read_text(encoding='utf-8'))
    _validate_declarations(declared)
    name = str(declared['name'])
    normal, malformed, command_calls = _selected_calls(
        declared, normal_tools, malformed_tools, call_commands)
    with tempfile.TemporaryDirectory(prefix='hermes-probe-') as tmp:
        home = Path(tmp) / 'home'
        (home / 'plugins').mkdir(parents=True)
        shutil.copytree(pkg_dir, home / 'plugins' / name)
        write_enabled_config(home, [])
        baseline = run_probe(home, {})
        write_enabled_config(home, [name])
        enabled = run_probe(home, {
            'normal_tools': normal,
            'malformed_tools': malformed,
            'call_commands': command_calls,
            'payload': payload or DEFAULT_PAYLOAD,
        })
    return _probe_report(name, baseline, enabled)


def _probe_report(name: str, baseline: dict, enabled: dict) -> dict:
    missing = {'enabled': False, 'error': 'not discovered'}
    return {
        'plugin': enabled['plugins'].get(name) or dict(missing),
        'baseline_plugin': baseline['plugins'].get(name) or dict(missing),
        'baseline': baseline,
        'new_tools': sorted(set(enabled['tools']) - set(baseline['tools'])),
        'new_commands': sorted(set(enabled['commands']) - set(baseline['commands'])),
        'new_hooks': sorted(set(enabled['hooks']) - set(baseline['hooks'])),
        'new_cli_commands': sorted(
            command for command, owner in enabled['cli_commands'].items()
            if owner.get('key') == name
            and baseline['cli_commands'].get(command) != owner),
        'skills': {qualified: entry for qualified, entry in enabled['skills'].items()
                   if entry.get('plugin') == name},
        'tool_calls': enabled['tool_calls'],
        'command_calls': enabled['command_calls'],
    }


def run_hermes(home: Path, *args: str) -> subprocess.CompletedProcess:
    require_runtime()
    return subprocess.run([HERMES_BIN, *args], capture_output=True, text=True,
                          env=hermes_env(home))


def install_profile(home: Path, package: Path, name: str) -> subprocess.CompletedProcess:
    return run_hermes(home, 'profile', 'install', str(package),
                      '--name', name, '--yes')
