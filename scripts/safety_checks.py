#!/usr/bin/env python3
"""Text-level public-safety and identity-neutrality checks."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from author_path_policy import approved_author_metadata_path
from author_policy import (
    author_identity_terms, identity_view, metadata_author_context, unsafe_author_field,
)
from credential_policy import (
    credential_assignment, private_key_block, python_credential_assignment,
    sensitive_credential,
)
from line_safety_policy import line_violation
from sanitize_rules import semantic_text_errors
from structured_text_policy import structured_payloads
from toolbox_common import (
    FORBIDDEN_PARTS, TRAILER_RE, git_files, git_info_dir, parse_frontmatter,
    read_terms, text_file,
)
from yaml_identity_policy import decoded_yaml_scalars

MIN_PUBLIC_SKILL_LINES = 40
SUPPORT_REF_RE = re.compile(r'\b(?:references|templates|scripts|assets)/[A-Za-z0-9][A-Za-z0-9._/-]*')


def deny_terms(repo: Path) -> list[str]:
    terms: list[str] = []
    info = git_info_dir(repo)
    for name in ['private-profile-denylist.txt', 'private-plugin-denylist.txt', 'identity-denylist.txt']:
        terms.extend(read_terms(info / name))
    env = os.environ.get('HERMES_TOOLBOX_DENY_TERMS')
    if env:
        terms.extend(x.strip() for x in env.split(',') if x.strip())
    return sorted(set(terms), key=len, reverse=True)


def line_allowed(rel: str, index: int, locations: set[tuple[str, int]]) -> bool:
    return (rel, index) in locations


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
        value = fm.get(key)
        if not value:
            errors.append(f'{rel}: missing frontmatter key {key}')
        elif not isinstance(value, str):
            errors.append(f'{rel}: frontmatter key {key} must be a scalar string')
    description = fm.get('description')
    if isinstance(description, str) and len(description) > 1024:
        errors.append(f'{rel}: description exceeds 1024 characters')
    if len(text.splitlines()) < MIN_PUBLIC_SKILL_LINES:
        errors.append(f'{rel}: public skill is too short to be a usable exported skill package ({len(text.splitlines())} lines < {MIN_PUBLIC_SKILL_LINES})')
    headings = [line.strip().lower() for line in body.splitlines() if line.startswith('## ')]
    if not any(h.startswith('## when to') for h in headings):
        errors.append(f'{rel}: missing a "When to Use"-style section')
    if not headings:
        errors.append(f'{rel}: missing level-2 body sections')
    return errors


def skill_reference_errors(rel: str, pkg_dir: Path) -> list[str]:
    """Every extension-bearing support path named in SKILL.md must exist in the package."""
    text = (pkg_dir / 'SKILL.md').read_text(encoding='utf-8')
    errors = []
    for token in sorted(set(SUPPORT_REF_RE.findall(text))):
        path = token.rstrip('.')
        if '.' not in path.rsplit('/', 1)[-1]:
            continue  # directory or prose mention, not a file reference
        if not (pkg_dir / path).is_file():
            errors.append(f'{rel}: referenced support file is missing from the package: {path}')
    return errors


def _structured_scalar_error(rel: str, scalar: tuple, ctx: dict,
                             role: str) -> tuple[int, str] | None:
    value, line, author, credential = scalar
    if credential and sensitive_credential(value):
        return line, 'credential-like assignment detected'
    if author and role != 'fence' and approved_author_metadata_path(rel):
        return None
    if author:
        return line, 'author field outside approved metadata'
    result = line_violation(value, ctx['terms'], ctx['author_terms'])
    return (line, result) if result else None


def _decoded_yaml_error(rel: str, text: str, ctx: dict) -> tuple[int, str] | None:
    for payload, offset, kind, role in structured_payloads(rel, text):
        if kind == 'json':
            try:
                json.loads(payload)
            except json.JSONDecodeError:
                return offset + 1, 'invalid JSON cannot be published'
        scalars = decoded_yaml_scalars(payload)
        if scalars is None:
            return offset + 1, 'invalid YAML cannot be published'
        for scalar in scalars:
            error = _structured_scalar_error(rel, scalar, ctx, role)
            if error:
                return offset + error[0], error[1]
    return None


def _credential_errors(rel: str, text: str, decoded) -> list[str]:
    is_python = rel.endswith('.py')
    raw = (decoded is None
           and (private_key_block(text)
                or not is_python and credential_assignment(text)))
    python_credential = is_python and not raw and python_credential_assignment(text)
    return ([f'{rel}: credential-like assignment detected']
            if raw or python_credential else [])


def _scan_text(rel: str, text: str, ctx: dict) -> list[str]:
    errors = ([f'{rel}: {error}' for error in semantic_text_errors(text)]
              if ctx.get('semantic') else [])
    decoded = _decoded_yaml_error(rel, text, ctx)
    if decoded:
        errors.append(f'{rel}:{decoded[0]}: {decoded[1]}')
    if rel.endswith('SKILL.md'):
        errors.extend(validate_public_skill(rel, text))
    errors.extend(_credential_errors(rel, text, decoded))
    if TRAILER_RE.search(text):
        errors.append(f'{rel}: generated/co-author trailer detected')
    for idx, line in enumerate(text.splitlines(), 1):
        allowed = line_allowed(rel, idx, ctx['author_locations'])
        if (rel, idx) in ctx['invalid_author_locations']:
            errors.append(f'{rel}:{idx}: complex author metadata is not allowed')
            break
        if not allowed and unsafe_author_field(line):
            errors.append(f'{rel}:{idx}: author field outside metadata')
            break
        spans = ctx['author_spans'].get((rel, idx), [])
        identity_line = identity_view(line, spans)
        why = line_violation(line, ctx['terms'], ctx['author_terms'], identity_line)
        if why:
            errors.append(f'{rel}:{idx}: {why}')
            break
    return errors


def _file_context(ctx: dict, rel: str) -> dict:
    semantic = not rel.startswith(('.github/', 'scripts/', 'tests/'))
    return {**ctx, 'semantic': semantic}


def validate_text_safety(repo: Path) -> list[str]:
    errors: list[str] = []
    files = git_files(repo)
    authors, author_locations, invalid_locations, author_spans = metadata_author_context(
        repo, files,
    )
    ctx = {
        'terms': deny_terms(repo),
        'author_locations': author_locations,
        'invalid_author_locations': invalid_locations,
        'author_spans': author_spans,
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
        text = path.read_text(encoding='utf-8', errors='ignore')
        errors.extend(_scan_text(rel, text, _file_context(ctx, rel)))
    return errors
