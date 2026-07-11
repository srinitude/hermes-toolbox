#!/usr/bin/env python3
"""Shared filesystem, hashing, and parsing helpers for toolbox scripts."""
from __future__ import annotations

import hashlib
import re
import subprocess
from pathlib import Path

EXCLUDED_CATEGORIES = [
    'env', 'auth', 'tokens', 'memories', 'sessions', 'logs', 'cache',
    'state', 'pairing', 'runtime'
]
REQUIRED_EXCLUDED = set(EXCLUDED_CATEGORIES)
RUNTIME_PARTS = {
    '.env', 'auth.json', 'mcp-tokens', 'memories', 'sessions', 'logs',
    'cache', 'pairing',
}
FORBIDDEN_PARTS = RUNTIME_PARTS | {
    'state.db', 'checkpoints', 'backups', 'state-snapshots',
    '.hermes_history', '.skills_prompt_snapshot.json',
}
EMAIL_RE = re.compile(r'\b[A-Za-z0-9._%+-]+@(?!(?:example\.com)\b)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
HERMES_HOME_RE = re.compile(r'(?<![A-Za-z0-9_<])/(home|Users)/([A-Za-z0-9._-]+)/\.hermes(?=/|\b)')
USER_HOME_RE = re.compile(r'(?<![A-Za-z0-9_<])/(home|Users)/([A-Za-z0-9._-]+)(?=/|\b)')
API_KEY_CONFIG_RE = re.compile(r'hermes config set ([A-Z][A-Z0-9_]*_API_KEY)\s+<[^\n>]+>')
SECRET_RE = re.compile(r'(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|password|secret)\s*[:=]\s*[A-Za-z0-9_./+=-]{16,}')
TRAILER_RE = re.compile(r'(?im)^(co-authored-by|generated-by|ai-authored-by|ai-co-authored-by):')
FRONTMATTER_RE = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.S)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(root: Path) -> str:
    """Deterministic digest of every file (relative path + bytes) under root."""
    digest = hashlib.sha256()
    if not root.exists():
        return ''
    for path in sorted(p for p in root.rglob('*') if p.is_file()):
        digest.update(path.relative_to(root).as_posix().encode('utf-8'))
        digest.update(b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def read_text_or_skip(path: Path) -> str | None:
    data = path.read_bytes()
    if b'\0' in data:
        return None
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return None


def text_file(path: Path) -> bool:
    try:
        return read_text_or_skip(path) is not None
    except OSError:
        return False


def read_terms(path: Path) -> list[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding='utf-8', errors='ignore').splitlines()
    return [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]


def git_info_dir(repo: Path) -> Path:
    """Resolve the repo's local (untracked) .git/info directory, worktree-safe."""
    try:
        out = subprocess.check_output(
            ['git', 'rev-parse', '--git-path', 'info'], cwd=repo, text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return repo / '.git' / 'info'
    path = Path(out)
    return path if path.is_absolute() else (repo / path)


def git_files(repo: Path) -> list[Path]:
    try:
        out = subprocess.check_output(
            ['git', 'ls-files', '--cached', '--others', '--exclude-standard'],
            cwd=repo, text=True,
        )
        files = [repo / line for line in out.splitlines() if line]
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    return _walk_files(repo)


def _walk_files(repo: Path) -> list[Path]:
    files = []
    for path in repo.rglob('*'):
        if not path.is_file() or '.git' in path.parts or '__pycache__' in path.parts:
            continue
        if path.suffix in {'.pyc', '.pyo'}:
            continue
        files.append(path)
    return files


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str | None]:
    match = FRONTMATTER_RE.search(text)
    if not match:
        return None, None
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line or line.startswith(' ') or ':' not in line:
            continue
        key, value = line.split(':', 1)
        data[key.strip()] = value.strip().strip('"\'')
    return data, text[match.end():]


def frontmatter_author(skill_text: str) -> str | None:
    data, _ = parse_frontmatter(skill_text)
    if data is None:
        return None
    return data.get('author') or None


def check_child_file(root: Path, rel: object, label: str) -> tuple[Path | None, str | None]:
    """Validate that rel names an existing file strictly inside root."""
    if not isinstance(rel, str) or not rel.strip():
        return None, f'{label} must be a non-empty relative path'
    rel_path = Path(rel)
    if rel_path.is_absolute() or '..' in rel_path.parts:
        return None, f'{label} must stay inside its package: {rel}'
    candidate = (root / rel_path).resolve()
    if root.resolve() not in candidate.parents:
        return None, f'{label} resolves outside its package: {rel}'
    if not candidate.is_file():
        return None, f'{label} references missing file: {rel}'
    return candidate, None


def require_child_file(root: Path, rel: object, label: str) -> Path:
    path, error = check_child_file(root, rel, label)
    if error:
        raise SystemExit(error)
    assert path is not None
    return path
