#!/usr/bin/env python3
"""Package-level manifest and completeness checks for public artifacts."""
from __future__ import annotations

import json
from pathlib import Path

from toolbox_common import REQUIRED_EXCLUDED, check_child_file


def load_json(path: Path) -> tuple[dict | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        return None, f'invalid JSON: {exc}'
    if not isinstance(data, dict):
        return None, 'manifest must be a JSON object'
    return data, None


def check_package_manifest(pkg_dir: Path, rel: str, kind: str) -> list[str]:
    manifest = pkg_dir / 'manifest.json'
    if not manifest.exists():
        return [f'{rel}: missing manifest.json']
    data, error = load_json(manifest)
    if error:
        return [f'{rel}/manifest.json: {error}']
    errors: list[str] = []
    if data.get('sanitized') is not True:
        errors.append(f'{rel}/manifest.json: sanitized must be true')
    if not REQUIRED_EXCLUDED.issubset(set(data.get('excluded_categories', []))):
        errors.append(f'{rel}/manifest.json: missing required excluded categories')
    if kind == 'plugin' and not data.get('source_gate'):
        errors.append(f'{rel}/manifest.json: missing source gate')
    return errors


def check_repo_package_manifests(repo: Path) -> list[str]:
    errors: list[str] = []
    for root_name, kind in [('profiles', 'profile'), ('plugins', 'plugin')]:
        root = repo / root_name
        if not root.exists():
            continue
        for child in sorted(root.iterdir()):
            if child.name == 'README.md' or not child.is_dir():
                continue
            errors.extend(check_package_manifest(child, f'{root_name}/{child.name}', kind))
    return errors


def check_personality_package(pkg_dir: Path, rel: str) -> list[str]:
    manifest = pkg_dir / 'manifest.json'
    if not manifest.exists():
        return [f'{rel}: missing manifest.json']
    data, error = load_json(manifest)
    if error:
        return [f'{rel}/manifest.json: {error}']
    errors: list[str] = []
    if data.get('type') != 'personality':
        errors.append(f'{rel}/manifest.json: type must be personality')
    if data.get('sanitized') is not True:
        errors.append(f'{rel}/manifest.json: sanitized must be true')
    _, config_error = check_child_file(pkg_dir, data.get('config_file'), 'config_file')
    if config_error:
        errors.append(f'{rel}/manifest.json: {config_error}')
    if not REQUIRED_EXCLUDED.issubset(set(data.get('excluded_categories', []))):
        errors.append(f'{rel}/manifest.json: missing required excluded categories')
    return errors


def check_repo_personalities(repo: Path) -> list[str]:
    errors: list[str] = []
    root = repo / 'primitives' / 'personalities'
    if not root.exists():
        return errors
    for child in sorted(root.iterdir()):
        if child.is_dir():
            errors.extend(check_personality_package(child, f'primitives/personalities/{child.name}'))
    return errors
