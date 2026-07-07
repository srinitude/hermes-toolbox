#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FORBIDDEN_PARTS = {
    '.env', 'auth.json', 'mcp-tokens', 'memories', 'sessions', 'logs',
    'cache', 'state.db', 'pairing', 'checkpoints', 'backups',
    'state-snapshots', '.hermes_history', '.skills_prompt_snapshot.json',
}
SECRET_RE = re.compile(r'(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret)\s*[:=]\s*[A-Za-z0-9_./+=-]{16,}')
TRAILER_RE = re.compile(r'(?im)^(co-authored-by|generated-by|ai-authored-by|ai-co-authored-by):')
EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@(?!(?:example\.com)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
ABS_USER_HOME_RE = re.compile(r'(?<![A-Za-z0-9_<])/(home|Users)/([A-Za-z0-9._-]+)(?=/|\b)')
FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.S)
MIN_PUBLIC_SKILL_LINES = 40


def git_files() -> list[Path]:
    try:
        out = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=REPO, text=True)
        files = [REPO / line for line in out.splitlines() if line]
        if files:
            return files
    except Exception:
        pass
    files = []
    for p in REPO.rglob('*'):
        if not p.is_file() or '.git' in p.parts:
            continue
        r = p.relative_to(REPO).as_posix()
        if '__pycache__' in p.parts or r.endswith(('.pyc', '.pyo')):
            continue
        files.append(p)
    return files


def read_terms(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding='utf-8', errors='ignore').splitlines() if line.strip() and not line.strip().startswith('#')]


def text_file(path: Path) -> bool:
    try:
        data = path.read_bytes()
    except Exception:
        return False
    if b'\0' in data:
        return False
    try:
        data.decode('utf-8')
    except UnicodeDecodeError:
        return False
    return True


def approved_lines() -> set[str]:
    lines = set(read_terms(REPO / '.git/info/approved-authorship.txt'))
    env = os.environ.get('HERMES_TOOLBOX_APPROVED_AUTHOR_LINE')
    if env:
        lines.add(env.strip())
    return lines


def deny_terms() -> list[str]:
    terms: list[str] = []
    for rel in ['private-profile-denylist.txt', 'private-plugin-denylist.txt', 'identity-denylist.txt']:
        terms.extend(read_terms(REPO / '.git/info' / rel))
    env = os.environ.get('HERMES_TOOLBOX_DENY_TERMS')
    if env:
        terms.extend([x.strip() for x in env.split(',') if x.strip()])
    # Sort longest first for clearer diagnostics.
    return sorted(set(terms), key=len, reverse=True)


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def parse_frontmatter(text: str) -> tuple[dict[str, str], str] | tuple[None, None]:
    match = FRONTMATTER_RE.search(text)
    if not match:
        return None, None
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line.startswith(' ') or line.startswith('  '):
            continue
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        data[key.strip()] = value.strip().strip('"\'')
    return data, text[match.end():]


def skill_author_names(files: list[Path]) -> set[str]:
    names: set[str] = set()
    for path in files:
        if rel(path).endswith('SKILL.md') and path.exists() and text_file(path):
            fm, _ = parse_frontmatter(path.read_text(encoding='utf-8', errors='ignore'))
            if fm and fm.get('author'):
                names.add(fm['author'])
    return names


def line_allowed(path: Path, line: str, approvals: set[str], author_names: set[str]) -> bool:
    stripped = line.strip()
    if rel(path).endswith('SKILL.md') and stripped in approvals:
        return True
    if rel(path).endswith('SKILL.md') and stripped.startswith('author:'):
        value = stripped.split(':', 1)[1].strip().strip('"\'')
        if value in author_names:
            return True
    return False


def author_identity_terms(author_names: set[str]) -> list[str]:
    terms: set[str] = set()
    for name in author_names:
        parts = [p for p in re.split(r'\s+', name.strip()) if p]
        if len(parts) >= 2:
            terms.add(name)
            first = parts[0]
            if len(first) > 2:
                terms.add(first)
    return sorted(terms, key=len, reverse=True)


def safe_child_file(root: Path, rel_path: object) -> tuple[Path | None, str | None]:
    if not isinstance(rel_path, str) or not rel_path.strip():
        return None, 'config_file must be a non-empty relative path'
    path = Path(rel_path)
    if path.is_absolute() or '..' in path.parts:
        return None, 'config_file must stay inside the personality package'
    root_resolved = root.resolve()
    candidate = (root / path).resolve()
    if root_resolved not in candidate.parents:
        return None, 'config_file resolves outside the personality package'
    if not candidate.is_file():
        return None, 'missing config_file target'
    return candidate, None


def path_is_forbidden(path: Path) -> str | None:
    r = rel(path)
    if '__pycache__' in Path(r).parts or r.endswith(('.pyc', '.pyo')):
        return 'generated Python cache file is not tracked public content'
    parts = set(Path(r).parts)
    for part in FORBIDDEN_PARTS:
        if part in parts:
            return f'forbidden runtime/private path component: {part}'
    if any(path_part.startswith('state.db') for path_part in Path(r).parts):
        return 'forbidden runtime/private path component: state.db*'
    if '/private-' in r or r.startswith('private-'):
        return 'private package path is not public-safe'
    return None


def validate_public_skill(path: Path, text: str) -> list[str]:
    errors: list[str] = []
    fm, body = parse_frontmatter(text)
    r = rel(path)
    if fm is None or body is None:
        return [f'{r}: missing valid YAML-style frontmatter block']
    for key in ['name', 'description', 'version', 'author', 'license']:
        if not fm.get(key):
            errors.append(f'{r}: missing frontmatter key {key}')
    if fm.get('description') and len(fm['description']) > 1024:
        errors.append(f'{r}: description exceeds 1024 characters')
    if len(text.splitlines()) < MIN_PUBLIC_SKILL_LINES:
        errors.append(f'{r}: public skill is too short to be a usable exported skill package ({len(text.splitlines())} lines < {MIN_PUBLIC_SKILL_LINES})')
    headings = [line.strip().lower() for line in body.splitlines() if line.startswith('## ')]
    if not any(h.startswith('## when to use') or h.startswith('## when to use') or h.startswith('## when to') for h in headings):
        errors.append(f'{r}: missing a "When to Use"-style section')
    if not headings:
        errors.append(f'{r}: missing level-2 body sections')
    return errors


def validate() -> list[str]:
    errors: list[str] = []
    files = git_files()
    approvals = approved_lines()
    terms = deny_terms()
    authors = skill_author_names(files)
    author_terms = author_identity_terms(authors)
    for path in files:
        if not path.exists():
            continue
        r = rel(path)
        why = path_is_forbidden(path)
        if why:
            errors.append(f'{r}: {why}')
            continue
        if not text_file(path):
            # Only the license-free text repo is expected; binary files are not useful here.
            errors.append(f'{r}: binary or non-UTF-8 file not allowed in public toolbox')
            continue
        text = path.read_text(encoding='utf-8', errors='ignore')
        if r.endswith('SKILL.md'):
            errors.extend(validate_public_skill(path, text))
        if SECRET_RE.search(text):
            errors.append(f'{r}: credential-like assignment detected')
        if TRAILER_RE.search(text):
            errors.append(f'{r}: generated/co-author trailer detected')
        for idx, line in enumerate(text.splitlines(), 1):
            if line_allowed(path, line, approvals, authors):
                continue
            if EMAIL_RE.search(line):
                errors.append(f'{r}:{idx}: non-example email address detected')
                break
            if ABS_USER_HOME_RE.search(line):
                errors.append(f'{r}:{idx}: user-specific absolute home path detected; use $HOME, $HERMES_HOME, or placeholders')
                break
            for term in terms:
                if term and term in line:
                    errors.append(f'{r}:{idx}: denied private/identity term detected')
                    break
            else:
                for term in author_terms:
                    if term and term in line:
                        errors.append(f'{r}:{idx}: approved author identity appears outside allowed frontmatter')
                        break
                else:
                    continue
            break
    # Package manifest checks.
    for pkg_root_name in ['profiles', 'plugins']:
        root = REPO / pkg_root_name
        if not root.exists():
            continue
        for child in root.iterdir():
            if child.name == 'README.md' or not child.is_dir():
                continue
            manifest = child / 'manifest.json'
            if not manifest.exists():
                errors.append(f'{pkg_root_name}/{child.name}: missing manifest.json')
                continue
            try:
                data = json.loads(manifest.read_text(encoding='utf-8'))
            except Exception as exc:
                errors.append(f'{pkg_root_name}/{child.name}/manifest.json: invalid JSON: {exc}')
                continue
            if data.get('sanitized') is not True:
                errors.append(f'{pkg_root_name}/{child.name}/manifest.json: sanitized must be true')
            excluded = set(data.get('excluded_categories', []))
            required = {'env', 'auth', 'tokens', 'memories', 'sessions', 'logs', 'cache', 'state', 'pairing', 'runtime'}
            if not required.issubset(excluded):
                errors.append(f'{pkg_root_name}/{child.name}/manifest.json: missing required excluded categories')
            if pkg_root_name == 'plugins' and not data.get('source_gate'):
                errors.append(f'{pkg_root_name}/{child.name}/manifest.json: missing source gate')

    personality_root = REPO / 'primitives' / 'personalities'
    if personality_root.exists():
        for child in personality_root.iterdir():
            if not child.is_dir():
                continue
            manifest = child / 'manifest.json'
            if not manifest.exists():
                errors.append(f'primitives/personalities/{child.name}: missing manifest.json')
                continue
            try:
                data = json.loads(manifest.read_text(encoding='utf-8'))
            except Exception as exc:
                errors.append(f'primitives/personalities/{child.name}/manifest.json: invalid JSON: {exc}')
                continue
            if data.get('type') != 'personality':
                errors.append(f'primitives/personalities/{child.name}/manifest.json: type must be personality')
            if data.get('sanitized') is not True:
                errors.append(f'primitives/personalities/{child.name}/manifest.json: sanitized must be true')
            _, config_error = safe_child_file(child, data.get('config_file'))
            if config_error:
                errors.append(f'primitives/personalities/{child.name}/manifest.json: {config_error}')
            excluded = set(data.get('excluded_categories', []))
            required = {'env', 'auth', 'tokens', 'memories', 'sessions', 'logs', 'cache', 'state', 'pairing', 'runtime'}
            if not required.issubset(excluded):
                errors.append(f'primitives/personalities/{child.name}/manifest.json: missing required excluded categories')
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args()
    errors = validate()
    if args.json:
        print(json.dumps({'ok': not errors, 'errors': errors}, indent=2))
    elif errors:
        print('Public-safety validation failed:', file=sys.stderr)
        for err in errors:
            print(f'- {err}', file=sys.stderr)
    else:
        print('Public-safety validation passed.')
    return 0 if not errors else 1


if __name__ == '__main__':
    raise SystemExit(main())
