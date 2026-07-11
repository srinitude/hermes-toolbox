#!/usr/bin/env python3
"""Text-level public-safety and identity-neutrality checks."""
from __future__ import annotations

import os
import re
from pathlib import Path

from toolbox_common import (
    EMAIL_RE, FORBIDDEN_PARTS, SECRET_RE, TRAILER_RE, USER_HOME_RE,
    git_files, git_info_dir, parse_frontmatter, read_terms, text_file,
)

MIN_PUBLIC_SKILL_LINES = 40


def approved_lines(repo: Path) -> set[str]:
    lines = set(read_terms(git_info_dir(repo) / 'approved-authorship.txt'))
    env = os.environ.get('HERMES_TOOLBOX_APPROVED_AUTHOR_LINE')
    if env:
        lines.add(env.strip())
    return lines


def deny_terms(repo: Path) -> list[str]:
    terms: list[str] = []
    info = git_info_dir(repo)
    for name in ['private-profile-denylist.txt', 'private-plugin-denylist.txt', 'identity-denylist.txt']:
        terms.extend(read_terms(info / name))
    env = os.environ.get('HERMES_TOOLBOX_DENY_TERMS')
    if env:
        terms.extend(x.strip() for x in env.split(',') if x.strip())
    # Sort longest first for clearer diagnostics.
    return sorted(set(terms), key=len, reverse=True)


def skill_author_names(files: list[Path]) -> set[str]:
    names: set[str] = set()
    for path in files:
        if path.name == 'SKILL.md' and path.exists() and text_file(path):
            fm, _ = parse_frontmatter(path.read_text(encoding='utf-8', errors='ignore'))
            if fm and fm.get('author'):
                names.add(fm['author'])
    return names


def author_identity_terms(author_names: set[str]) -> list[str]:
    terms: set[str] = set()
    for name in author_names:
        parts = [p for p in re.split(r'\s+', name.strip()) if p]
        if len(parts) >= 2:
            terms.add(name)
            if len(parts[0]) > 2:
                terms.add(parts[0])
    return sorted(terms, key=len, reverse=True)


def line_allowed(rel: str, line: str, approvals: set[str], author_names: set[str]) -> bool:
    stripped = line.strip()
    if rel.endswith('SKILL.md') and stripped in approvals:
        return True
    if rel.endswith('SKILL.md') and stripped.startswith('author:'):
        value = stripped.split(':', 1)[1].strip().strip('"\'')
        return value in author_names
    return False


def path_is_forbidden(rel: str) -> str | None:
    parts = Path(rel).parts
    if '__pycache__' in parts or rel.endswith(('.pyc', '.pyo')):
        return 'generated Python cache file is not tracked public content'
    for part in FORBIDDEN_PARTS:
        if part in set(parts):
            return f'forbidden runtime/private path component: {part}'
    if any(part.startswith('state.db') for part in parts):
        return 'forbidden runtime/private path component: state.db*'
    if '/private-' in rel or rel.startswith('private-'):
        return 'private package path is not public-safe'
    return None


def validate_public_skill(rel: str, text: str) -> list[str]:
    errors: list[str] = []
    fm, body = parse_frontmatter(text)
    if fm is None or body is None:
        return [f'{rel}: missing valid YAML-style frontmatter block']
    for key in ['name', 'description', 'version', 'author', 'license']:
        if not fm.get(key):
            errors.append(f'{rel}: missing frontmatter key {key}')
    if fm.get('description') and len(fm['description']) > 1024:
        errors.append(f'{rel}: description exceeds 1024 characters')
    if len(text.splitlines()) < MIN_PUBLIC_SKILL_LINES:
        errors.append(f'{rel}: public skill is too short to be a usable exported skill package ({len(text.splitlines())} lines < {MIN_PUBLIC_SKILL_LINES})')
    headings = [line.strip().lower() for line in body.splitlines() if line.startswith('## ')]
    if not any(h.startswith('## when to') for h in headings):
        errors.append(f'{rel}: missing a "When to Use"-style section')
    if not headings:
        errors.append(f'{rel}: missing level-2 body sections')
    return errors


def _line_violation(line: str, terms: list[str], author_terms: list[str]) -> str | None:
    if EMAIL_RE.search(line):
        return 'non-example email address detected'
    if USER_HOME_RE.search(line):
        return 'user-specific absolute home path detected; use $HOME, $HERMES_HOME, or placeholders'
    for term in terms:
        if term and term in line:
            return 'denied private/identity term detected'
    for term in author_terms:
        if term and term in line:
            return 'approved author identity appears outside allowed frontmatter'
    return None


def _scan_text(rel: str, text: str, ctx: dict) -> list[str]:
    errors: list[str] = []
    if rel.endswith('SKILL.md'):
        errors.extend(validate_public_skill(rel, text))
    if SECRET_RE.search(text):
        errors.append(f'{rel}: credential-like assignment detected')
    if TRAILER_RE.search(text):
        errors.append(f'{rel}: generated/co-author trailer detected')
    for idx, line in enumerate(text.splitlines(), 1):
        if line_allowed(rel, line, ctx['approvals'], ctx['authors']):
            continue
        why = _line_violation(line, ctx['terms'], ctx['author_terms'])
        if why:
            errors.append(f'{rel}:{idx}: {why}')
            break
    return errors


def validate_text_safety(repo: Path) -> list[str]:
    errors: list[str] = []
    files = git_files(repo)
    authors = skill_author_names(files)
    ctx = {
        'approvals': approved_lines(repo),
        'terms': deny_terms(repo),
        'authors': authors,
        'author_terms': author_identity_terms(authors),
    }
    for path in files:
        if not path.exists():
            continue
        rel = path.relative_to(repo).as_posix()
        why = path_is_forbidden(rel)
        if why:
            errors.append(f'{rel}: {why}')
            continue
        if not text_file(path):
            # Only the license-free text repo is expected; binary files are not useful here.
            errors.append(f'{rel}: binary or non-UTF-8 file not allowed in public toolbox')
            continue
        errors.extend(_scan_text(rel, path.read_text(encoding='utf-8', errors='ignore'), ctx))
    return errors
