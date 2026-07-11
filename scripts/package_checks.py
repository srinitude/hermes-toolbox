#!/usr/bin/env python3
"""Package-level manifest and completeness checks for public artifacts."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

import yaml

from toolbox_common import REQUIRED_EXCLUDED, check_child_file, read_text_or_skip

TODO_RE = re.compile(r'\bTODO\b|\bFIXME\b')
DOUBLE_RE = re.compile(r'(?i)\b\w*(?:fake|mock|stub|spy)\w*\b|monkeypatch')
SKIP_RE = re.compile(r'skipTest|skipIf|skipUnless|unittest\.skip|pytest\.mark\.skip|xfail')
ABSOLUTE_PATH_RE = re.compile(r'/(?:home|Users|tmp|private/tmp|var/folders)/[A-Za-z0-9._-]+')
FORBIDDEN_PROFILE_KEYS = ('source', 'installed_at')


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


def _body_is_placeholder(body: list[ast.stmt]) -> bool:
    def is_docstring(stmt: ast.stmt) -> bool:
        return (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
                and isinstance(stmt.value.value, str))

    def is_noop(stmt: ast.stmt) -> bool:
        return isinstance(stmt, ast.Pass) or (
            isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
            and stmt.value.value is Ellipsis)

    stmts = [stmt for stmt in body if not is_docstring(stmt)]
    return all(is_noop(stmt) for stmt in stmts)


def _python_placeholders(rel: str, text: str) -> list[str]:
    errors = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if DOUBLE_RE.search(line):
            errors.append(f'{rel}:{lineno}: test double reference: {line.strip()}')
        if SKIP_RE.search(line):
            errors.append(f'{rel}:{lineno}: skip/xfail placeholder: {line.strip()}')
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return errors + [f'{rel}:{exc.lineno}: syntax error: {exc.msg}']
    constructs = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    for node in ast.walk(tree):
        if isinstance(node, constructs) and _body_is_placeholder(node.body):
            errors.append(f'{rel}:{node.lineno}: {node.name} has a placeholder body')
    return errors


def find_placeholders(pkg_dir: Path) -> list[str]:
    """Report TODO markers, test doubles, skips, and placeholder bodies."""
    errors: list[str] = []
    for path in sorted(p for p in pkg_dir.rglob('*') if p.is_file()):
        if '__pycache__' in path.parts:
            continue
        text = read_text_or_skip(path)
        if text is None:
            continue
        rel = path.relative_to(pkg_dir).as_posix()
        for lineno, line in enumerate(text.splitlines(), 1):
            if TODO_RE.search(line):
                errors.append(f'{rel}:{lineno}: TODO/FIXME marker: {line.strip()}')
        if path.suffix == '.py':
            errors.extend(_python_placeholders(rel, text))
    return errors


def check_profile_hygiene(profile_dir: Path, rel: str) -> list[str]:
    """Reject runtime provenance fields and absolute paths in profile manifests."""
    manifest = profile_dir / 'distribution.yaml'
    if not manifest.is_file():
        return [f'{rel}: missing distribution.yaml']
    try:
        data = yaml.safe_load(manifest.read_text(encoding='utf-8'))
    except yaml.YAMLError as exc:
        return [f'{rel}/distribution.yaml: invalid YAML: {exc}']
    if not isinstance(data, dict):
        return [f'{rel}/distribution.yaml: manifest must be a mapping']
    errors = [f'{rel}/distribution.yaml: forbidden runtime field {key!r}'
              for key in FORBIDDEN_PROFILE_KEYS if key in data]
    for path in sorted({manifest, *profile_dir.glob('config*.yaml')}):
        for lineno, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
            if ABSOLUTE_PATH_RE.search(line):
                errors.append(f'{rel}/{path.name}:{lineno}: absolute path: {line.strip()}')
    return errors


def _diff_errors(rel: str, label: str, declared, actual) -> list[str]:
    errors = []
    for name in sorted(set(declared) - set(actual)):
        errors.append(f'{rel}: declared {label} {name!r} was not registered by the real manager')
    for name in sorted(set(actual) - set(declared)):
        errors.append(f'{rel}: registered {label} {name!r} is not declared in plugin.yaml')
    return errors


def check_registration_parity(declared: dict, probe: dict, rel: str) -> list[str]:
    """Compare plugin.yaml declarations against real PluginManager output."""
    errors = _diff_errors(rel, 'tool', declared.get('provides_tools') or [],
                          probe['new_tools'])
    errors += _diff_errors(rel, 'command', declared.get('provides_commands') or [],
                           probe['new_commands'])
    name = str(declared.get('name') or '')
    declared_skills = declared.get('provides_skills') or []
    skills = probe.get('skills') or {}
    for skill in sorted(declared_skills):
        entry = skills.get(f'{name}:{skill}')
        if not entry or not entry.get('is_skill_file'):
            errors.append(f'{rel}: declared skill {skill!r} is not a real SKILL.md registration')
    for qualified in sorted(skills):
        if qualified.split(':', 1)[1] not in declared_skills:
            errors.append(f'{rel}: registered skill {qualified!r} is not declared in plugin.yaml')
    return errors
