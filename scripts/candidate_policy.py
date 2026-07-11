#!/usr/bin/env python3
"""Explicit, fail-closed selection policy for public toolbox candidates."""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from toolbox_common import git_info_dir, read_terms

DEFAULT_PUBLIC_SKILLS = [
    'autonomous-ai-agents/openrouter-mcp-server',
    'hermes-agent/honcho-memory-provider',
    'hermes-agent/hermes-config-audits',
    'hermes-agent/profile-builder',
    'software-development/prompt-enhancer',
    'software-development/plugin-builder',
]


@dataclass(frozen=True)
class Candidate:
    kind: str
    name: str
    source: Path
    destination: Path
    source_profile: str | None


@dataclass(frozen=True)
class Decision:
    accepted: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class PolicyConfig:
    public_plugins: tuple[str, ...]
    public_plugin_profile: str | None
    private_profile_prefix: str | None


def _check_entry(entry: str, label: str) -> None:
    path = Path(entry)
    if path.is_absolute() or '..' in path.parts:
        raise SystemExit(f'{label} allowlist entry must be a safe relative name: {entry}')


def read_allowlist(path: Path, label: str) -> tuple[str, ...]:
    entries = read_terms(path)
    seen: set[str] = set()
    for entry in entries:
        if entry in seen:
            raise SystemExit(f'{label} allowlist has a duplicate entry: {entry}')
        seen.add(entry)
        _check_entry(entry, label)
    return tuple(entries)


def merged_allowlist(repo: Path, cli_values: list[str], filename: str, label: str) -> tuple[str, ...]:
    from_cli = read_allowlist_values(cli_values, label)
    from_file = read_allowlist(git_info_dir(repo) / filename, label)
    merged = list(from_cli) + [entry for entry in from_file if entry not in from_cli]
    return tuple(merged)


def read_allowlist_values(values: list[str], label: str) -> tuple[str, ...]:
    seen: set[str] = set()
    for entry in values:
        if entry in seen:
            raise SystemExit(f'{label} allowlist has a duplicate entry: {entry}')
        seen.add(entry)
        _check_entry(entry, label)
    return tuple(values)


def plugin_candidate(hermes_home: Path, repo: Path, name: str, profile: str | None) -> Candidate:
    source_root = hermes_home / 'profiles' / (profile or '') / 'plugins'
    return Candidate(kind='plugin', name=name, source=source_root / name,
                     destination=repo / 'plugins' / name, source_profile=profile)


def _plugin_reasons(candidate: Candidate, cfg: PolicyConfig) -> list[str]:
    reasons = []
    if not cfg.public_plugin_profile:
        reasons.append('no public plugin source profile is configured (--public-plugin-profile)')
    elif candidate.source_profile != cfg.public_plugin_profile:
        reasons.append(f'source profile {candidate.source_profile!r} is not the configured public plugin source profile')
    if candidate.name not in cfg.public_plugins:
        reasons.append('plugin is not in the explicit public plugin allowlist')
    if cfg.private_profile_prefix and candidate.name.startswith(cfg.private_profile_prefix):
        reasons.append('plugin name carries the private prefix')
    if len(Path(candidate.name).parts) != 1 or candidate.name in {'.', '..'}:
        reasons.append('plugin name must be a single safe path segment')
    return reasons + _plugin_source_reasons(candidate)


def _plugin_source_reasons(candidate: Candidate) -> list[str]:
    if not (candidate.source / 'plugin.yaml').is_file():
        return ['plugin source is missing (no plugin.yaml at the source path)']
    if not any(candidate.source.glob('tests/test_*.py')):
        return ['plugin source has no real tests (tests/test_*.py)']
    return []


def decide_plugin(candidate: Candidate, cfg: PolicyConfig) -> Decision:
    reasons = _plugin_reasons(candidate, cfg)
    return Decision(accepted=not reasons, reasons=tuple(reasons))


def stale_plugin_destinations(repo: Path, allowed: tuple[str, ...]) -> list[str]:
    root = repo / 'plugins'
    if not root.exists():
        return []
    return sorted(child.name for child in root.iterdir()
                  if child.is_dir() and child.name not in allowed)


def public_skill_rels(repo: Path, cli_values: list[str]) -> list[Path]:
    raw: list[str] = list(cli_values)
    env = os.environ.get('HERMES_TOOLBOX_PUBLIC_SKILLS', '')
    if env:
        raw.extend(part.strip() for part in env.split(',') if part.strip())
    raw.extend(read_allowlist(git_info_dir(repo) / 'public-skill-allowlist.txt', 'public skill'))
    if not raw:
        raw = DEFAULT_PUBLIC_SKILLS
        print('no public skill allowlist configured; falling back to the tracked default skill list',
              file=sys.stderr)
    rels = []
    for item in raw:
        rel = Path(item)
        if rel.is_absolute() or '..' in rel.parts or not item.strip():
            raise SystemExit(f'public skill path must be relative and stay under skills/: {item}')
        rels.append(rel)
    return sorted(set(rels), key=lambda p: p.as_posix())
