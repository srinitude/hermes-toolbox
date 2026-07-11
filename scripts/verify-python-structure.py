#!/usr/bin/env python3
"""Enforce structural gates on Python files: 200-line files, 30-line named
constructs, and control-flow nesting no deeper than three levels."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

MAX_FILE_LINES = 200
MAX_CONSTRUCT_LINES = 30
MAX_NESTING = 3
NAMED_CONSTRUCTS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
CONTROL_BLOCKS = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With,
                  ast.AsyncWith, ast.Try, ast.TryStar, ast.Match)


def construct_errors(rel: str, tree: ast.AST) -> list[str]:
    errors = []
    for node in ast.walk(tree):
        if not isinstance(node, NAMED_CONSTRUCTS):
            continue
        length = node.end_lineno - node.lineno + 1
        if length > MAX_CONSTRUCT_LINES:
            errors.append(
                f'{rel}:{node.lineno}: {node.name} spans {length} lines (max {MAX_CONSTRUCT_LINES})')
    return errors


def nesting_errors(rel: str, node: ast.AST, depth: int = 0) -> list[str]:
    errors = []
    for child in ast.iter_child_nodes(node):
        child_depth = depth + 1 if isinstance(child, CONTROL_BLOCKS) else depth
        if child_depth == MAX_NESTING + 1:
            errors.append(
                f'{rel}:{child.lineno}: control-flow nesting exceeds {MAX_NESTING} levels')
            continue
        errors.extend(nesting_errors(rel, child, child_depth))
    return errors


def check_file(path: Path, root: Path) -> list[str]:
    rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else str(path)
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeDecodeError) as exc:
        return [f'{rel}: unreadable: {exc}']
    line_count = len(text.splitlines())
    errors = []
    if line_count > MAX_FILE_LINES:
        errors.append(f'{rel}: file spans {line_count} lines (max {MAX_FILE_LINES})')
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return errors + [f'{rel}:{exc.lineno}: syntax error: {exc.msg}']
    errors.extend(construct_errors(rel, tree))
    errors.extend(nesting_errors(rel, tree))
    return errors


def collect_python_files(targets: list[str]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        path = Path(target)
        if path.is_dir():
            files.extend(sorted(p for p in path.rglob('*.py') if '__pycache__' not in p.parts))
        elif path.suffix == '.py':
            files.append(path)
        else:
            raise SystemExit(f'not a Python file or directory: {target}')
    return files


def main(argv: list[str]) -> int:
    if not argv:
        print('usage: verify-python-structure.py <file-or-dir> [...]', file=sys.stderr)
        return 2
    root = Path.cwd()
    errors: list[str] = []
    files = collect_python_files(argv)
    for path in files:
        errors.extend(check_file(path.resolve(), root))
    if errors:
        print('Python structure validation failed:', file=sys.stderr)
        for err in errors:
            print(f'- {err}', file=sys.stderr)
        return 1
    print(f'Python structure validation passed ({len(files)} files).')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
