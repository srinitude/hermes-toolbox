#!/usr/bin/env python3
"""Transactional per-package public exports preserving last-known-good artifacts."""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import yaml

from candidate_policy import PolicyConfig, decide_plugin, plugin_candidate
from safety_checks import skill_reference_errors, validate_public_skill
from sanitize_rules import sanitize_public_text
from source_safety import reject_source_symlinks
from toolbox_common import (
    EXCLUDED_CATEGORIES, RUNTIME_PARTS, SECRET_RE, frontmatter_author, read_text_or_skip,
    tree_sha, write,
)
ALLOWED_SKILL_SUPPORT_DIRS = {'references', 'templates', 'scripts', 'assets'}
REQUIRED_PLUGIN_FILES = ('README.md', 'plugin.yaml', '__init__.py')


def _plugin_file_included(rel: Path) -> bool:
    if set(rel.parts) & RUNTIME_PARTS or '__pycache__' in rel.parts:
        return False
    if rel.suffix in {'.pyc', '.pyo'} or rel.as_posix() == 'manifest.json':
        return False
    return not any(part.startswith('state.db') for part in rel.parts)


def _skill_file_included(rel: Path) -> bool:
    if rel.name.startswith('.') or '__pycache__' in rel.parts or rel.suffix in {'.pyc', '.pyo'}:
        return False
    return rel.name == 'SKILL.md' or (bool(rel.parts) and rel.parts[0] in ALLOWED_SKILL_SUPPORT_DIRS)


def _stage_file(path: Path, target: Path, rel: Path, repo: Path, author: str | None,
                private_prefix: str | None, public_plugin_profile: str | None) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    text = read_text_or_skip(path)
    if text is None:
        shutil.copy2(path, target)
        return
    if rel.name == 'SKILL.md':
        author = frontmatter_author(text) or author
    write(target, sanitize_public_text(text, rel, repo, author,
                                       private_prefix, public_plugin_profile))


def stage_tree(src: Path, staging: Path, repo: Path, author: str | None,
               private_prefix: str | None, public_plugin_profile: str | None, included) -> None:
    reject_source_symlinks(src)
    staging.mkdir(parents=True)
    for path in sorted(src.rglob('*')):
        rel = path.relative_to(src)
        if path.is_file() and included(rel):
            _stage_file(path, staging / rel, rel, repo, author,
                        private_prefix, public_plugin_profile)


def plugin_package_manifest(dst: Path, name: str) -> str:
    return json.dumps({
        'package': name,
        'type': 'plugin',
        'source_gate': 'configured-public-plugin-source-profile',
        'sanitized': True,
        'included_files': sorted(str(p.relative_to(dst)) for p in dst.rglob('*') if p.is_file()),
        'excluded_categories': EXCLUDED_CATEGORIES,
    }, indent=2, sort_keys=True) + '\n'


def staged_text_errors(staging: Path) -> list[str]:
    errors = []
    for path in sorted(p for p in staging.rglob('*') if p.is_file()):
        rel = path.relative_to(staging).as_posix()
        text = read_text_or_skip(path)
        if text is None:
            errors.append(f'{rel}: binary or non-UTF-8 file is not public-safe')
        elif SECRET_RE.search(text):
            errors.append(f'{rel}: credential-like assignment survived sanitization')
    return errors


def _manifest_errors(staging: Path, name: str) -> list[str]:
    data = json.loads((staging / 'manifest.json').read_text(encoding='utf-8'))
    try:
        declared = yaml.safe_load((staging / 'plugin.yaml').read_text(encoding='utf-8'))
    except yaml.YAMLError as exc:
        return [f'{name}/plugin.yaml: invalid YAML: {exc}']
    if not isinstance(declared, dict):
        return [f'{name}/plugin.yaml: must be a mapping']
    errors = []
    if declared.get('name') != data.get('package'):
        errors.append(f'{name}: plugin.yaml name {declared.get("name")!r} does not match package manifest {data.get("package")!r}')
    actual = sorted(p.relative_to(staging).as_posix() for p in staging.rglob('*')
                    if p.is_file() and p.relative_to(staging).as_posix() != 'manifest.json')
    if data.get('included_files') != actual:
        errors.append(f'{name}: manifest file list does not match staged package contents')
    return errors


def _plugin_staging_errors(staging: Path, name: str) -> list[str]:
    missing = [f'{name}: staged package is missing required file {fname}'
               for fname in REQUIRED_PLUGIN_FILES if not (staging / fname).is_file()]
    return missing or _manifest_errors(staging, name) + staged_text_errors(staging)


def _skill_staging_errors(staging: Path, rel: Path) -> list[str]:
    skill_md = staging / 'SKILL.md'
    if not skill_md.is_file():
        return [f'{rel}: staged skill is missing SKILL.md']
    rel_md = (Path('skills') / rel / 'SKILL.md').as_posix()
    errors = validate_public_skill(rel_md, skill_md.read_text(encoding='utf-8'))
    errors += skill_reference_errors(rel_md, staging)
    return errors + staged_text_errors(staging)


def _replace_package(staging: Path, destination: Path) -> None:
    """Swap staging into place; restore the previous package if the swap fails."""
    backup = destination.parent / f'.lkg.{destination.name}'
    if backup.exists():
        shutil.rmtree(backup)
    if destination.exists():
        os.rename(destination, backup)
    try:
        os.rename(staging, destination)
    except OSError:
        if backup.exists():
            os.rename(backup, destination)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def run_transaction(destination: Path, build, label: str) -> bool:
    """Stage via build, validate, then publish atomically; True when bytes changed."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.parent / f'.staging.{destination.name}'
    if staging.exists():
        shutil.rmtree(staging)
    try:
        errors = build(staging)
        if errors:
            raise SystemExit(f'{label} failed staging validation: ' + '; '.join(errors))
        if destination.exists() and tree_sha(staging) == tree_sha(destination):
            return False
        _replace_package(staging, destination)
        return True
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def export_one_plugin(hermes_home: Path, repo: Path, name: str, cfg: PolicyConfig) -> bool:
    candidate = plugin_candidate(hermes_home, repo, name, cfg.public_plugin_profile)
    decision = decide_plugin(candidate, cfg)
    if not decision.accepted:
        raise SystemExit(f'public plugin candidate {name!r} rejected: ' + '; '.join(decision.reasons))

    def build(staging: Path) -> list[str]:
        stage_tree(candidate.source, staging, repo, None, cfg.private_profile_prefix,
                   cfg.public_plugin_profile, _plugin_file_included)
        write(staging / 'manifest.json', plugin_package_manifest(staging, name))
        return _plugin_staging_errors(staging, name)

    return run_transaction(candidate.destination, build, f'public plugin candidate {name!r}')


def export_one_skill(source_skills: Path, repo: Path, rel: Path, private_prefix: str | None,
                     public_plugin_profile: str | None) -> bool:
    src = source_skills / rel
    if not (src / 'SKILL.md').is_file():
        raise SystemExit(f'missing public skill source: {src / "SKILL.md"}')
    author = frontmatter_author((src / 'SKILL.md').read_text(encoding='utf-8'))

    def build(staging: Path) -> list[str]:
        stage_tree(src, staging, repo, author, private_prefix, public_plugin_profile,
                   _skill_file_included)
        return _skill_staging_errors(staging, rel)

    return run_transaction(repo / 'skills' / rel, build, f'public skill candidate {rel}')


def export_public_skills(hermes_home: Path, repo: Path, skill_rels: list[Path],
                         private_prefix: str | None, public_plugin_profile: str | None) -> list[Path]:
    source_skills = hermes_home / 'skills'
    return [repo / 'skills' / rel for rel in skill_rels
            if export_one_skill(source_skills, repo, rel, private_prefix, public_plugin_profile)]


def export_selected_plugins(hermes_home: Path, repo: Path, cfg: PolicyConfig) -> list[Path]:
    return [repo / 'plugins' / name for name in cfg.public_plugins
            if export_one_plugin(hermes_home, repo, name, cfg)]


def write_change_list(path: Path, repo: Path, destinations: list[Path]) -> None:
    """Record accepted repo-relative destinations, NUL-delimited, for staging."""
    rels = sorted(dest.relative_to(repo).as_posix() for dest in destinations)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(rel + '\0' for rel in rels), encoding='utf-8')
