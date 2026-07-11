#!/usr/bin/env python3
"""Copy and export primitives for public toolbox packages."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from candidate_policy import PolicyConfig, decide_plugin, plugin_candidate
from sanitize_rules import sanitize_public_text
from toolbox_common import EXCLUDED_CATEGORIES, frontmatter_author, read_text_or_skip, write

ALLOWED_SKILL_SUPPORT_DIRS = {'references', 'templates', 'scripts', 'assets'}
SKIPPED_TREE_PARTS = {
    '.env', 'auth.json', 'mcp-tokens', 'memories', 'sessions', 'logs',
    'cache', 'pairing',
}


def copy_tree_public(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for path in src.rglob('*'):
        if not path.is_file():
            continue
        rel = path.relative_to(src)
        if set(rel.parts) & SKIPPED_TREE_PARTS:
            continue
        if any(str(part).startswith('state.db') for part in rel.parts):
            continue
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)


def _skill_file_included(file_rel: Path) -> bool:
    if file_rel.name.startswith('.') or '__pycache__' in file_rel.parts:
        return False
    if file_rel.suffix in {'.pyc', '.pyo'}:
        return False
    if file_rel.name == 'SKILL.md':
        return True
    return bool(file_rel.parts) and file_rel.parts[0] in ALLOWED_SKILL_SUPPORT_DIRS


def copy_public_skill(source_skills: Path, repo: Path, rel: Path,
                      private_prefix: str | None, public_plugin_profile: str | None) -> None:
    src = source_skills / rel
    skill_md = src / 'SKILL.md'
    if not skill_md.is_file():
        raise SystemExit(f'missing public skill source: {skill_md}')
    author = frontmatter_author(skill_md.read_text(encoding='utf-8'))
    dst = repo / 'skills' / rel
    if dst.exists():
        shutil.rmtree(dst)
    for path in sorted(src.rglob('*')):
        if not path.is_file() or not _skill_file_included(path.relative_to(src)):
            continue
        text = read_text_or_skip(path)
        if text is None:
            continue
        file_rel = path.relative_to(src)
        sanitized = sanitize_public_text(
            text, rel / file_rel, repo, author, private_prefix, public_plugin_profile)
        write(dst / file_rel, sanitized)


def export_public_skills(hermes_home: Path, repo: Path, skill_rels: list[Path],
                         private_prefix: str | None, public_plugin_profile: str | None) -> list[Path]:
    source_skills = hermes_home / 'skills'
    for rel in skill_rels:
        copy_public_skill(source_skills, repo, rel, private_prefix, public_plugin_profile)
    return [repo / 'skills' / rel for rel in skill_rels]


def plugin_package_manifest(dst: Path, name: str) -> str:
    return json.dumps({
        'package': name,
        'type': 'plugin',
        'source_gate': 'configured-public-plugin-source-profile',
        'sanitized': True,
        'included_files': sorted(str(p.relative_to(dst)) for p in dst.rglob('*') if p.is_file()),
        'excluded_categories': EXCLUDED_CATEGORIES,
    }, indent=2, sort_keys=True) + '\n'


def export_selected_plugins(hermes_home: Path, repo: Path, cfg: PolicyConfig) -> list[Path]:
    exported: list[Path] = []
    for name in cfg.public_plugins:
        candidate = plugin_candidate(hermes_home, repo, name, cfg.public_plugin_profile)
        decision = decide_plugin(candidate, cfg)
        if not decision.accepted:
            raise SystemExit(
                f'public plugin candidate {name!r} rejected: ' + '; '.join(decision.reasons))
        copy_tree_public(candidate.source, candidate.destination)
        write(candidate.destination / 'manifest.json',
              plugin_package_manifest(candidate.destination, name))
        exported.append(candidate.destination)
    return exported


def write_change_list(path: Path, repo: Path, destinations: list[Path]) -> None:
    """Record accepted repo-relative destinations, NUL-delimited, for staging."""
    rels = sorted(dest.relative_to(repo).as_posix() for dest in destinations)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(rel + '\0' for rel in rels), encoding='utf-8')
