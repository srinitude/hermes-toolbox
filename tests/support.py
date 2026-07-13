"""Shared real-environment helpers for the toolbox test suite."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / 'scripts'
FIXTURES = Path(__file__).resolve().parent / 'fixtures'
HERMES_BIN = shutil.which('hermes') or str(Path.home() / '.local' / 'bin' / 'hermes')
HERMES_VENV_PYTHON = str(Path.home() / '.hermes' / 'hermes-agent' / 'venv' / 'bin' / 'python')


def add_scripts_path() -> None:
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))


def make_repo(base: Path) -> Path:
    """Create a real temporary git repository carrying the current scripts."""
    repo = base / 'repo'
    (repo / 'skills').mkdir(parents=True)
    (repo / 'inventory').mkdir()
    shutil.copytree(SCRIPTS, repo / 'scripts',
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
    subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
    return repo


def make_home(base: Path, profile: str = 'pub-src',
              plugins: dict[str, Path] | None = None) -> Path:
    """Create a temporary Hermes-home-shaped source tree."""
    home = base / 'hermes-home'
    (home / 'skills').mkdir(parents=True)
    plugin_root = home / 'profiles' / profile / 'plugins'
    plugin_root.mkdir(parents=True)
    for name, source in (plugins or {}).items():
        shutil.copytree(source, plugin_root / name)
        rename_plugin(plugin_root / name, name)
    return home


def rename_plugin(plugin_dir: Path, name: str) -> None:
    manifest = plugin_dir / 'plugin.yaml'
    text = manifest.read_text(encoding='utf-8')
    manifest.write_text(text.replace('name: complete-plugin', f'name: {name}', 1),
                        encoding='utf-8')
    plugin = plugin_dir / '__init__.py'
    source = plugin.read_text(encoding='utf-8')
    plugin.write_text(source.replace("PLUGIN_NAME = 'complete-plugin'",
                                     f"PLUGIN_NAME = '{name}'"), encoding='utf-8')


PROVENANCE = ("source: /tmp/hermes-dist-stage/extracted/demo\n"
              "installed_at: '2026-07-11T08:19:57+00:00'\n")


def add_profile(home: Path, name: str = 'pub-demo') -> Path:
    """Copy the complete-profile fixture into home as a live installed profile."""
    profile = home / 'profiles' / name
    shutil.copytree(FIXTURES / 'complete-profile', profile)
    manifest = profile / 'distribution.yaml'
    text = manifest.read_text(encoding='utf-8')
    manifest.write_text(text.replace('name: complete-profile', f'name: {name}', 1)
                        + PROVENANCE, encoding='utf-8')
    _add_runtime_state(profile)
    return profile


def _add_runtime_state(profile: Path) -> None:
    (profile / '.env').write_text('DEMO_SERVICE_URL=http://127.0.0.1:9\n', encoding='utf-8')
    (profile / 'auth.json').write_text('{}\n', encoding='utf-8')
    (profile / 'state.db').write_bytes(b'\x00runtime-state\x00')
    for rel in ['memories/notes.md', 'sessions/last-session.json', 'logs/run.log',
                'cache/blob.txt', 'cron/outputs/last-run.txt']:
        path = profile / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('runtime state that must never be exported\n', encoding='utf-8')


def profile_export_sources(base: Path, name: str = 'pub-demo') -> tuple[Path, Path]:
    """Build a repo plus a Hermes home carrying one exportable profile fixture."""
    repo = make_repo(base)
    home = make_home(base)
    shutil.copytree(FIXTURES / 'complete-skill', home / 'skills' / 'fixtures' / 'complete-skill')
    add_profile(home, name)
    return repo, home


def clean_env() -> dict[str, str]:
    env = dict(os.environ)
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    for key in ['HERMES_TOOLBOX_PUBLIC_SKILLS', 'HERMES_TOOLBOX_DENY_TERMS',
                'HERMES_PRIVATE_PROFILE_PREFIX', 'HERMES_PUBLIC_PLUGIN_PROFILE',
                'HERMES_TOOLBOX_APPROVED_AUTHOR_LINE', 'HERMES_HOME']:
        env.pop(key, None)
    return env


def run_exporter(repo: Path, home: Path, *args: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(repo / 'scripts' / 'export-public-toolbox.py'),
           '--repo', str(repo), '--hermes-home', str(home), *args]
    return subprocess.run(cmd, capture_output=True, text=True, env=clean_env())


def tree_bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob('*')) if p.is_file()}
