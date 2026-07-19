from __future__ import annotations

from pathlib import Path, PurePosixPath

import yaml

OWNED_PATHS = {
    ".github/",
    ".gitignore",
    "AGENTS.md",
    "LICENSE",
    "README.md",
    "SOUL.md",
    "config.yaml",
    "distribution.yaml",
    "mise.toml",
    "pyproject.toml",
    "scripts/",
    "skills/",
    "templates/",
    "tests/",
    "uv.lock",
}
EXCLUDED_DIRECTORIES = {".git", ".hermes", ".ruff_cache", ".venv", "__pycache__"}


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ValueError(f"invalid YAML in {path.name}") from error
    if not isinstance(data, dict):
        raise ValueError(f"{path.name} must contain a mapping")
    return data


def owned_path_errors(value) -> list[str]:
    if not isinstance(value, list):
        return ["distribution_owned must be a list"]
    if not all(isinstance(item, str) for item in value):
        return ["distribution_owned entries must be strings"]
    errors = []
    if len(value) != len(set(value)):
        errors.append("distribution_owned contains a duplicate path")
    for item in value:
        path = PurePosixPath(item)
        if not item or "\\" in item or path.is_absolute() or ".." in path.parts:
            errors.append(f"distribution_owned contains unsafe path: {item}")
    actual = set(value)
    for item in sorted(OWNED_PATHS - actual):
        errors.append(f"distribution_owned is missing {item}")
    for item in sorted(actual - OWNED_PATHS):
        errors.append(f"distribution_owned contains unexpected path: {item}")
    return errors


def root_entry_errors(root: Path, owned: list[str]) -> list[str]:
    present = {path.name + ("/" if path.is_dir() else "") for path in root.iterdir()}
    declared = set(owned)
    errors = [f"undeclared root entry: {item}" for item in sorted(present - declared)]
    errors.extend(f"declared root entry is missing: {item}" for item in sorted(declared - present))
    return errors


def filesystem_errors(root: Path) -> list[str]:
    errors = []
    for path in root.rglob("*"):
        parts = path.relative_to(root).parts
        relative = "/".join(parts)
        if len(parts) > 1 and path.name in EXCLUDED_DIRECTORIES:
            errors.append(f"excluded path is not allowed: {relative}")
        elif path.is_symlink():
            errors.append(f"symlink is not allowed: {relative}")
        elif path.is_file() and path.stat().st_mode & 0o111:
            errors.append(f"executable mode is not allowed: {relative}")
        elif not path.is_file() and not path.is_dir():
            errors.append(f"unsupported filesystem entry: {relative}")
    return errors


def manifest_errors(root: Path) -> list[str]:
    try:
        manifest = load_yaml(root / "distribution.yaml")
    except ValueError as error:
        return [str(error)]
    errors = []
    if manifest.get("name") != "hermes-toolbox":
        errors.append("distribution name must be hermes-toolbox")
    owned = manifest.get("distribution_owned")
    errors.extend(owned_path_errors(owned))
    if isinstance(owned, list) and all(isinstance(item, str) for item in owned):
        errors.extend(root_entry_errors(root, owned))
    errors.extend(filesystem_errors(root))
    return errors
