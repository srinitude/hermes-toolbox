from __future__ import annotations

import ast
import re
from pathlib import Path

from scripts.manifest_checks import EXCLUDED_DIRECTORIES

CONSTRUCT_NODES = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
NESTING_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try, ast.Match)
BLOCKED_TERMS = (
    "delve", "dive into", "tapestry", "testament", "realm", "journey",
    "landscape", "navigate", "underscore", "robust", "seamless", "leverage",
    "elevate", "embark", "unlock", "unleash", "harness", "foster", "crucial",
    "vital", "pivotal", "nuanced", "intricate", "meticulous", "profound",
    "vibrant", "showcase", "streamline", "empower", "holistic", "resonate",
    "boasts", "comprehensive", "cutting-edge", "game-changer", "unwavering",
    "bustling", "when it comes to", "in today's world", "look no further",
    "shed light on", "pave the way", "a testament to", "plays a crucial role",
    "in conclusion", "in summary", "dive deeper", "take it to the next level",
)


def repository_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] not in EXCLUDED_DIRECTORIES:
            yield path


def privacy_errors(root: Path) -> list[str]:
    patterns = {
        "absolute user path": re.compile(r"(?:/(?:Users|home)/|[A-Z]:\\Users\\)[^/$`<\s]+", re.I),
        "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
        "secret assignment": re.compile(r"(?i)(?:api[_-]?key|password|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_-]{12,}"),
        "recognizable API token": re.compile(r"(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})"),
        "private key block": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
        "personal peer identifier": re.compile(r"peerName\s*[\"']?\s*[:=]\s*[\"']?(?!<)[A-Za-z0-9_-]{3,}", re.I),
    }
    errors = []
    for path in repository_files(root):
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in patterns.items():
            if pattern.search(text):
                errors.append(f"{label} found in {path.relative_to(root)}")
    return errors


def voice_errors(root: Path) -> list[str]:
    pattern = re.compile(r"(?i)\b(?:" + "|".join(re.escape(term) for term in BLOCKED_TERMS) + r")\b")
    errors = []
    for relative in ("AGENTS.md", "README.md", "SOUL.md", "templates/AGENTS.md"):
        path = root / relative
        if not path.is_file():
            continue
        fenced = False
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.startswith("```"):
                fenced = not fenced
                continue
            if fenced:
                continue
            if "—" in line or "–" in line:
                errors.append(f"disallowed dash in {relative}:{line_number}")
            if match := pattern.search(line):
                errors.append(f"blocked wording {match.group(0)!r} in {relative}:{line_number}")
    return errors


def governed_files(root: Path):
    for path in repository_files(root):
        if path.suffix in {".md", ".py", ".sh"}:
            yield path


def size_errors(root: Path) -> list[str]:
    errors = []
    for path in governed_files(root):
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if path.suffix == ".md" and len(lines) > 200:
            errors.append(f"Markdown line limit exceeded: {path.relative_to(root)}")
        if path.suffix == ".md" and path.stat().st_size > 20_000:
            errors.append(f"Markdown byte limit exceeded: {path.relative_to(root)}")
        if path.suffix in {".py", ".sh"} and len(lines) > 200:
            errors.append(f"code line limit exceeded: {path.relative_to(root)}")
        if path.suffix == ".py":
            errors.extend(construct_errors(root, path))
    return errors


def construct_errors(root: Path, path: Path) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return [f"invalid Python syntax: {path.relative_to(root)}"]
    errors = [
        f"construct line limit exceeded: {path.relative_to(root)}:{node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, CONSTRUCT_NODES) and construct_lines(node) > 30
    ]
    errors.extend(
        f"nesting depth limit exceeded: {path.relative_to(root)}:{node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, CONSTRUCT_NODES) and nesting_depth(node) > 3
    )
    return errors


def construct_lines(node: ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    starts = [node.lineno, *(decorator.lineno for decorator in node.decorator_list)]
    return (node.end_lineno or node.lineno) - min(starts) + 1


def nesting_depth(node: ast.AST) -> int:
    maximum = 0

    def visit(current: ast.AST, depth: int) -> None:
        nonlocal maximum
        for child in ast.iter_child_nodes(current):
            if child is not node and isinstance(child, CONSTRUCT_NODES):
                continue
            is_elif = (
                isinstance(current, ast.If)
                and isinstance(child, ast.If)
                and len(current.orelse) == 1
                and current.orelse[0] is child
                and child.col_offset == current.col_offset
            )
            child_depth = depth + int(isinstance(child, NESTING_NODES) and not is_elif)
            maximum = max(maximum, child_depth)
            visit(child, child_depth)

    visit(node, 0)
    return maximum
