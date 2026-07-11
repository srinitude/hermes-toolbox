#!/usr/bin/env python3
"""Build the public inventory manifest and source fingerprints."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from toolbox_common import require_child_file, sha, write

INVENTORY_SKIP_PARTS = {
    '.env', 'auth.json', 'mcp-tokens', 'memories', 'sessions', 'logs',
    'cache', 'pairing', 'checkpoints', 'backups',
}


def _personality_entry(repo: Path, manifest_path: Path) -> dict:
    try:
        data = json.loads(manifest_path.read_text(encoding='utf-8'))
    except json.JSONDecodeError as exc:
        raise SystemExit(f'invalid personality manifest {manifest_path}: {exc}') from exc
    if data.get('type') != 'personality' or data.get('sanitized') is not True:
        raise SystemExit(f'personality manifest must declare type=personality and sanitized=true: {manifest_path}')
    config_path = require_child_file(
        manifest_path.parent, data.get('config_file'), f'{manifest_path}: config_file')
    return {
        'name': data.get('name', manifest_path.parent.name),
        'path': manifest_path.parent.relative_to(repo).as_posix(),
        'manifest_sha256': sha(manifest_path),
        'config_sha256': sha(config_path),
        'sanitized': True,
    }


def _profile_entries(repo: Path) -> list[dict]:
    entries = []
    root = repo / 'profiles'
    if not root.exists():
        return entries
    for profile_dir in sorted(p for p in root.iterdir() if p.is_dir()):
        manifest_file = profile_dir / 'manifest.json'
        if not manifest_file.exists():
            continue
        try:
            data = json.loads(manifest_file.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            raise SystemExit(f'invalid profile manifest {manifest_file}: {exc}') from exc
        if data.get('sanitized') is not True:
            raise SystemExit(f'profile manifest must declare sanitized=true: {manifest_file}')
        entries.append({'path': f'profiles/{profile_dir.name}', 'sanitized': True})
    return entries


def _plugin_entries(repo: Path) -> list[dict]:
    root = repo / 'plugins'
    if not root.exists():
        return []
    return [
        {'path': f'plugins/{child.name}', 'sanitized': True}
        for child in sorted(root.iterdir())
        if child.is_dir() and (child / 'manifest.json').is_file()
    ]


def build_public_manifest(repo: Path) -> dict:
    manifest: dict = {'version': 1, 'skills': [], 'profiles': [], 'plugins': [], 'personalities': []}
    for skill_path in sorted((repo / 'skills').rglob('SKILL.md')):
        manifest['skills'].append({'path': skill_path.relative_to(repo).as_posix(), 'sha256': sha(skill_path)})
    for personality_manifest in sorted((repo / 'primitives' / 'personalities').glob('*/manifest.json')):
        manifest['personalities'].append(_personality_entry(repo, personality_manifest))
    manifest['plugins'] = _plugin_entries(repo)
    manifest['profiles'] = _profile_entries(repo)
    return manifest


def skip_inventory_file(repo: Path, path: Path) -> bool:
    """Return true for local/private files that must not enter public inventory."""
    if not path.is_file() or '.git' in path.parts:
        return True
    rel = path.relative_to(repo).as_posix()
    parts = Path(rel).parts
    if '.hermes' in parts or set(parts) & INVENTORY_SKIP_PARTS:
        return True
    if any(part.startswith('state.db') for part in parts):
        return True
    if rel == 'inventory/source-fingerprints.json':
        return True
    return '__pycache__' in parts or rel.endswith(('.pyc', '.pyo'))


def _tracked_files(repo: Path) -> list[Path] | None:
    """List files under version control; None when repo is not a git worktree."""
    try:
        out = subprocess.check_output(['git', 'ls-files', '--cached', '-z'],
                                      cwd=repo, text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        return None
    return [repo / rel for rel in out.split('\0') if rel]


def _walk_fallback(repo: Path) -> list[Path]:
    """Non-git fallback: visible files only, keeping caches like .serena out."""
    return [path for path in sorted(repo.rglob('*')) if path.is_file()
            and not any(part.startswith('.') for part in path.relative_to(repo).parts)]


def _package_roots(repo: Path, manifest: dict) -> list[Path]:
    roots = [repo / Path(entry['path']).parent for entry in manifest['skills']]
    for key in ('plugins', 'profiles', 'personalities'):
        roots.extend(repo / entry['path'] for entry in manifest[key])
    return roots


def fingerprint_files(repo: Path, manifest: dict) -> list[Path]:
    """Exactly the tracked files plus files under manifest-listed package roots."""
    files = _tracked_files(repo)
    if files is None:
        files = _walk_fallback(repo)
    for root in _package_roots(repo, manifest):
        files.extend(path for path in root.rglob('*') if path.is_file())
    return sorted(set(files))


def write_inventory(repo: Path) -> None:
    manifest = build_public_manifest(repo)
    write(repo / 'inventory' / 'public-manifest.json', json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    fingerprints = {}
    for path in fingerprint_files(repo, manifest):
        if skip_inventory_file(repo, path):
            continue
        fingerprints[path.relative_to(repo).as_posix()] = sha(path)
    write(repo / 'inventory' / 'source-fingerprints.json', json.dumps(fingerprints, indent=2, sort_keys=True) + '\n')
