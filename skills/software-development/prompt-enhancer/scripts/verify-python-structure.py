#!/usr/bin/env python3
"""Verify Python file, construct, and semantic nesting limits with AST."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

NAMED = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
CONTROL = (
    ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try,
    ast.With, ast.AsyncWith, ast.Match,
)


def start_line(node: ast.AST) -> int:
    decorators = getattr(node, "decorator_list", ())
    return min([node.lineno, *(item.lineno for item in decorators)])


def max_nesting(node: ast.AST, depth: int = 0) -> int:
    maximum = depth
    for child in ast.iter_child_nodes(node):
        if isinstance(child, NAMED) and child is not node:
            continue
        child_depth = depth + 1 if isinstance(child, CONTROL) else depth
        maximum = max(maximum, max_nesting(child, child_depth))
    return maximum


def inspect_file(
    path: Path, file_limit: int, construct_limit: int, nesting_limit: int,
) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    line_count = len(text.splitlines())
    if line_count > file_limit:
        errors.append(f"{path}: file has {line_count} lines (max {file_limit})")
    tree = ast.parse(text, filename=str(path))
    for node in ast.walk(tree):
        if not isinstance(node, NAMED):
            continue
        start = start_line(node)
        span = node.end_lineno - start + 1
        if span > construct_limit:
            errors.append(f"{path}:{start} {node.name} spans {span} lines")
        nesting = max_nesting(node)
        if nesting > nesting_limit:
            errors.append(f"{path}:{start} {node.name} nests {nesting} levels")
    return errors


def python_files(roots: list[Path]) -> list[Path]:
    files: set[Path] = set()
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            files.add(root)
        elif root.is_dir():
            files.update(root.rglob("*.py"))
    return sorted(path for path in files if "__pycache__" not in path.parts)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("roots", nargs="+", type=Path)
    parser.add_argument("--file-limit", type=int, default=200)
    parser.add_argument("--construct-limit", type=int, default=30)
    parser.add_argument("--nesting-limit", type=int, default=3)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = python_files(args.roots)
    errors = [
        error
        for path in files
        for error in inspect_file(
            path, args.file_limit, args.construct_limit, args.nesting_limit,
        )
    ]
    if errors:
        print("\n".join(errors))
        return 1
    print(f"structure ok: {len(files)} Python files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
