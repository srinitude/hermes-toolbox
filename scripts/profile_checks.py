#!/usr/bin/env python3
"""Native completeness checks for public profile distribution packages."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from credential_policy import credential_key
from package_checks import check_package_manifest, check_profile_hygiene, find_placeholders

REQUIRED_PROFILE_FILES = ('distribution.yaml', 'SOUL.md', 'config.yaml',
                          'README.md', 'manifest.json')
REQUIRED_MANIFEST_FIELDS = ('name', 'version', 'description', 'hermes_requires',
                            'author', 'license')
RUNTIME_NAME_RE = re.compile(
    r'(?i)^(\.env(\..+)?|auth\.(json|lock)|mcp-tokens|memories|sessions|logs|cache|'
    r'(audio|image|document)_cache|pairing|cron|runtime|backups?|checkpoints|'
    r'workspace|home|plans|private|hooks|\.hermes_history|.+\.db(-shm|-wal)?)$')


def load_profile_manifest(pkg: Path) -> tuple[dict | None, str | None]:
    path = pkg / 'distribution.yaml'
    if not path.is_file():
        return None, 'missing distribution.yaml'
    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
    except yaml.YAMLError as exc:
        return None, f'invalid YAML: {exc}'
    if not isinstance(data, dict):
        return None, 'distribution manifest must be a mapping'
    return data, None


def manifest_field_errors(pkg: Path, rel: str) -> list[str]:
    data, error = load_profile_manifest(pkg)
    if error:
        return [f'{rel}/distribution.yaml: {error}']
    errors = [f'{rel}/distribution.yaml: missing or empty required field {field!r}'
              for field in REQUIRED_MANIFEST_FIELDS
              if not isinstance(data.get(field), str) or not data[field].strip()]
    name = data.get('name')
    if isinstance(name, str) and name.strip() and name != Path(rel).name:
        errors.append(f'{rel}/distribution.yaml: name {name!r} does not match the package directory')
    return errors


def owned_path_errors(pkg: Path, rel: str) -> list[str]:
    data, error = load_profile_manifest(pkg)
    if error:
        return []
    owned = data.get('distribution_owned')
    if not isinstance(owned, list) or not owned:
        return [f'{rel}/distribution.yaml: distribution_owned must list the reusable package paths']
    errors = []
    for entry in owned:
        entry_path = Path(str(entry))
        if entry_path.is_absolute() or '..' in entry_path.parts:
            errors.append(f'{rel}: distribution_owned entry escapes the package: {entry}')
        elif not (pkg / entry_path).exists():
            errors.append(f'{rel}: distribution_owned path {entry!r} is missing from the package')
    return errors


def runtime_state_errors(pkg: Path, rel: str) -> list[str]:
    errors = []
    for path in sorted(pkg.rglob('*')):
        parts = path.relative_to(pkg).parts
        bad = next((part for part in parts if RUNTIME_NAME_RE.match(part)), None)
        if bad:
            errors.append(f'{rel}/{"/".join(parts)}: runtime/private state {bad!r} is not distributable')
    return errors


def _secret_key_paths(node, prefix: str = ''):
    if isinstance(node, dict):
        for key, value in node.items():
            path = f'{prefix}.{key}' if prefix else str(key)
            if credential_key(str(key)):
                yield path
            yield from _secret_key_paths(value, path)
    elif isinstance(node, list):
        for item in node:
            yield from _secret_key_paths(item, prefix)


def config_key_errors(pkg: Path, rel: str) -> list[str]:
    path = pkg / 'config.yaml'
    if not path.is_file():
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding='utf-8'))
    except yaml.YAMLError as exc:
        return [f'{rel}/config.yaml: invalid YAML: {exc}']
    return [f'{rel}/config.yaml: credential-like config key {key!r} is not reusable public config'
            for key in _secret_key_paths(data)]


def profile_package_errors(pkg: Path, rel: str) -> list[str]:
    errors = [f'{rel}: missing required file {name}'
              for name in REQUIRED_PROFILE_FILES if not (pkg / name).is_file()]
    if errors:
        return errors
    errors = manifest_field_errors(pkg, rel) + owned_path_errors(pkg, rel)
    errors += runtime_state_errors(pkg, rel) + config_key_errors(pkg, rel)
    errors += check_profile_hygiene(pkg, rel) + check_package_manifest(pkg, rel, 'profile')
    errors += [f'{rel}/{error}' for error in find_placeholders(pkg)]
    return errors
