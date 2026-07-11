#!/usr/bin/env python3
"""Explicit, fail-closed selection policy for public toolbox candidates."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

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


def public_skill_rels(cli_values: list[str]) -> list[Path]:
    raw: list[str] = []
    if cli_values:
        raw.extend(cli_values)
    env = os.environ.get('HERMES_TOOLBOX_PUBLIC_SKILLS', '')
    if env:
        raw.extend(part.strip() for part in env.split(',') if part.strip())
    if not raw:
        raw = DEFAULT_PUBLIC_SKILLS
    rels = []
    for item in raw:
        rel = Path(item)
        if rel.is_absolute() or '..' in rel.parts or not item.strip():
            raise SystemExit(f'public skill path must be relative and stay under skills/: {item}')
        rels.append(rel)
    return sorted(set(rels), key=lambda p: p.as_posix())
