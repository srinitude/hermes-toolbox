"""Publisher-controlled handler policies for real plugin probes."""
from __future__ import annotations

import errno
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

LOCAL_POLICY = Path('.git/info/public-plugin-handler-allowlist.json')
TRACKED_POLICY = Path('inventory/plugin-runtime-probes.json')
POLICY_PATHS = (LOCAL_POLICY, TRACKED_POLICY)
REQUIRED_LISTS = (
    'normal_tools', 'malformed_tools', 'call_commands', 'skip_commands',
)
OPTIONAL_FIELDS = {'payload'}
PLUGIN_NAME = re.compile(r'[a-z0-9](?:[a-z0-9-]*[a-z0-9])?')


def open_component(parent: int, name: str, directory: bool) -> int:
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if directory:
        flags |= os.O_DIRECTORY
    return os.open(name, flags, dir_fd=parent)


def read_policy_at(repo: Path, relative: Path) -> tuple[str | None, str | None]:
    descriptors = []
    try:
        descriptors.append(os.open(repo, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW))
        for part in relative.parts[:-1]:
            descriptors.append(open_component(descriptors[-1], part, True))
        descriptors.append(open_component(descriptors[-1], relative.name, False))
        info = os.fstat(descriptors[-1])
        if not stat.S_ISREG(info.st_mode):
            return None, f'plugin probe policy must be a regular file: {relative}'
        if info.st_nlink > 1:
            return None, f'plugin probe policy must not be a hardlink: {relative}'
        with os.fdopen(descriptors.pop(), encoding='utf-8') as stream:
            return stream.read(), None
    except FileNotFoundError:
        return None, None
    except UnicodeError as exc:
        return None, f'invalid plugin probe policy encoding {relative}: {exc}'
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            return None, f'plugin probe policy path contains a symlink: {relative}'
        return None, f'invalid plugin probe policy path {relative}: {exc}'
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def policy_text(repo: Path) -> tuple[str | None, str | None]:
    for relative in POLICY_PATHS:
        text, error = read_policy_at(repo, relative)
        if error:
            return None, error
        if text is not None:
            return text, None
    return None, 'missing publisher-controlled plugin probe policy'


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate JSON key: {key}')
        result[key] = value
    return result


def checked_names(policy: dict, field: str) -> tuple[list[str] | None, str | None]:
    values = policy.get(field)
    if not isinstance(values, list) or any(
            not isinstance(value, str) or not value for value in values):
        return None, f'plugin probe policy {field} must be a string list'
    if len(values) != len(set(values)):
        return None, f'plugin probe policy {field} contains duplicates'
    return values, None


def validate_policy(policy: object) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(policy, dict):
        return None, 'plugin probe policy entry must be an object'
    unknown = sorted(set(policy) - set(REQUIRED_LISTS) - OPTIONAL_FIELDS)
    if unknown:
        return None, f"plugin probe policy has unknown fields: {', '.join(unknown)}"
    result: dict[str, Any] = {}
    for field in REQUIRED_LISTS:
        values, error = checked_names(policy, field)
        if error:
            return None, error
        result[field] = values
    payload = policy.get('payload', {})
    if not isinstance(payload, dict):
        return None, 'plugin probe policy payload must be an object'
    result['payload'] = payload
    return result, None


def validate_document(data: object) -> tuple[dict[str, Any] | None, str | None]:
    if not isinstance(data, dict):
        return None, 'plugin probe policy must be an object'
    result = {}
    for name, entry in data.items():
        if not isinstance(name, str) or PLUGIN_NAME.fullmatch(name) is None:
            return None, f'invalid plugin probe policy name: {name!r}'
        policy, error = validate_policy(entry)
        if error:
            return None, f'{name}: {error}'
        result[name] = policy
    return result, None


def policy_document(repo: Path) -> tuple[dict[str, Any] | None, str | None]:
    text, error = policy_text(repo)
    if error or text is None:
        return None, error or 'missing plugin probe policy bytes'
    try:
        data = json.loads(text, object_pairs_hook=unique_object)
    except ValueError as exc:
        return None, f'invalid plugin probe policy JSON: {exc}'
    return validate_document(data)


def load_plugin_probe_policy(
    repo: Path, name: str,
) -> tuple[dict[str, Any] | None, str | None]:
    data, error = policy_document(repo)
    if error or data is None:
        return None, error or 'missing plugin probe policy document'
    if name not in data:
        return None, f'missing plugin probe policy for {name!r}'
    return data[name], None
