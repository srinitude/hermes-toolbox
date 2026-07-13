"""Approved package-root locations for public author metadata."""
from __future__ import annotations

from pathlib import Path

METADATA_NAMES = {'SKILL.md', 'plugin.yaml', 'distribution.yaml'}
SUPPORT_PARTS = {'references', 'templates', 'scripts', 'assets'}


def _skill_metadata(parts: tuple[str, ...], start: int) -> bool:
    return (parts[-1] == 'SKILL.md'
            and not set(parts[start:-1]) & SUPPORT_PARTS)


def approved_author_metadata_path(rel: str) -> bool:
    parts = Path(rel).parts
    if len(parts) == 1:
        return parts[0] in METADATA_NAMES
    if len(parts) == 3 and parts[0] == 'plugins':
        return parts[-1] == 'plugin.yaml'
    if len(parts) == 3 and parts[0] == 'profiles':
        return parts[-1] == 'distribution.yaml'
    if len(parts) == 5 and parts[0] == 'profiles' and parts[2] == 'plugins':
        return parts[-1] == 'plugin.yaml'
    if len(parts) > 4 and parts[0] == 'profiles' and parts[2] == 'skills':
        return _skill_metadata(parts, 3)
    if parts and parts[0] == 'skills':
        return _skill_metadata(parts, 1)
    if len(parts) > 3 and parts[:2] == ('tests', 'fixtures'):
        fixture_path = parts[3:]
        if len(fixture_path) == 1:
            return parts[-1] in METADATA_NAMES
        return _skill_metadata(parts, 3)
    return False
