#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

EXCLUDED_CATEGORIES = ['env', 'auth', 'tokens', 'memories', 'sessions', 'logs', 'cache', 'state', 'pairing', 'runtime']

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

def copy_tree_public(src: Path, dst: Path):
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for path in src.rglob('*'):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        parts = set(rel.parts)
        if parts & {'.env', 'auth.json', 'mcp-tokens', 'memories', 'sessions', 'logs', 'cache', 'pairing'}:
            continue
        if any(str(part).startswith('state.db') for part in rel.parts):
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)

def ensure_local_info(repo: Path, private_prefix: str | None, public_plugin_profile: str | None, approved_author_line: str | None):
    info = repo / '.git' / 'info'
    info.mkdir(parents=True, exist_ok=True)
    deny_terms = []
    if private_prefix:
        deny_terms.append(private_prefix)
    if public_plugin_profile:
        deny_terms.append(public_plugin_profile)
    write(info / 'private-profile-denylist.txt', '\n'.join([private_prefix or '']) + '\n')
    write(info / 'private-plugin-denylist.txt', '\n'.join([public_plugin_profile or '']) + '\n')
    if approved_author_line:
        write(info / 'approved-authorship.txt', approved_author_line + '\n')
    existing = info / 'identity-denylist.txt'
    if not existing.exists():
        existing.write_text('', encoding='utf-8')

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--hermes-home', default=os.environ.get('HERMES_HOME', str(Path.home() / '.hermes')))
    parser.add_argument('--repo', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--private-profile-prefix', default=os.environ.get('HERMES_PRIVATE_PROFILE_PREFIX', ''))
    parser.add_argument('--public-plugin-profile', default=os.environ.get('HERMES_PUBLIC_PLUGIN_PROFILE', ''))
    parser.add_argument('--approved-author-line', default=os.environ.get('HERMES_TOOLBOX_APPROVED_AUTHOR_LINE', ''))
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    hermes_home = Path(args.hermes_home).resolve()
    ensure_local_info(repo, args.private_profile_prefix, args.public_plugin_profile, args.approved_author_line)

    manifest = {'version': 1, 'skills': [], 'profiles': [], 'plugins': [], 'personalities': []}
    for skill_path in sorted((repo / 'skills').rglob('SKILL.md')):
        manifest['skills'].append({'path': skill_path.relative_to(repo).as_posix(), 'sha256': sha(skill_path)})

    for personality_manifest in sorted((repo / 'primitives' / 'personalities').glob('*/manifest.json')):
        try:
            personality_data = json.loads(personality_manifest.read_text(encoding='utf-8'))
        except json.JSONDecodeError as exc:
            raise SystemExit(f'invalid personality manifest {personality_manifest}: {exc}') from exc
        if personality_data.get('type') != 'personality' or personality_data.get('sanitized') is not True:
            raise SystemExit(f'personality manifest must declare type=personality and sanitized=true: {personality_manifest}')
        config_rel = personality_data.get('config_file')
        config_path = personality_manifest.parent / str(config_rel or '')
        if not config_rel or not config_path.exists():
            raise SystemExit(f'personality manifest references missing config file: {personality_manifest}')
        manifest['personalities'].append({
            'name': personality_data.get('name', personality_manifest.parent.name),
            'path': personality_manifest.parent.relative_to(repo).as_posix(),
            'manifest_sha256': sha(personality_manifest),
            'config_sha256': sha(config_path),
            'sanitized': True,
        })

    # Export sanitized plugin packages from configured source profile when present.
    if args.public_plugin_profile:
        source_root = hermes_home / 'profiles' / args.public_plugin_profile / 'plugins'
        if source_root.exists():
            for plugin_dir in sorted(p for p in source_root.iterdir() if p.is_dir()):
                if args.private_profile_prefix and plugin_dir.name.startswith(args.private_profile_prefix):
                    continue
                dst = repo / 'plugins' / plugin_dir.name
                copy_tree_public(plugin_dir, dst)
                write(dst / 'manifest.json', json.dumps({
                    'package': plugin_dir.name,
                    'type': 'plugin',
                    'source_gate': 'configured-public-plugin-source-profile',
                    'sanitized': True,
                    'included_files': sorted(str(p.relative_to(dst)) for p in dst.rglob('*') if p.is_file()),
                    'excluded_categories': EXCLUDED_CATEGORIES,
                }, indent=2, sort_keys=True) + '\n')
                manifest['plugins'].append({'path': f'plugins/{plugin_dir.name}', 'sanitized': True})

    write(repo / 'inventory' / 'public-manifest.json', json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    fingerprints = {}
    for path in sorted(repo.rglob('*')):
        if not path.is_file() or '.git' in path.parts:
            continue
        rel = path.relative_to(repo).as_posix()
        if rel == 'inventory/source-fingerprints.json':
            continue
        if '__pycache__' in path.parts or rel.endswith(('.pyc', '.pyo')):
            continue
        fingerprints[rel] = sha(path)
    write(repo / 'inventory' / 'source-fingerprints.json', json.dumps(fingerprints, indent=2, sort_keys=True) + '\n')
    subprocess.check_call(['python3', str(repo / 'scripts' / 'validate-public-safety.py')], cwd=repo)
    subprocess.check_call(['python3', str(repo / 'scripts' / 'validate-identity-neutrality.py')], cwd=repo)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
