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

HERMES_SRC = Path.home() / '.hermes' / 'hermes-agent'
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


def probe_plugin_package(pkg_dir: Path, payload: dict | None = None) -> dict:
    """Probe one package twice with real discovery: disabled, then enabled."""
    pkg_dir = Path(pkg_dir)
    declared = yaml.safe_load((pkg_dir / 'plugin.yaml').read_text(encoding='utf-8'))
    name = str(declared['name'])
    with tempfile.TemporaryDirectory(prefix='hermes-probe-') as tmp:
        home = Path(tmp) / 'home'
        (home / 'plugins').mkdir(parents=True)
        shutil.copytree(pkg_dir, home / 'plugins' / name)
        write_enabled_config(home, [])
        baseline = run_probe(home, {})
        write_enabled_config(home, [name])
        enabled = run_probe(home, {
            'call_tools': declared.get('provides_tools') or [],
            'call_commands': declared.get('provides_commands') or [],
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
