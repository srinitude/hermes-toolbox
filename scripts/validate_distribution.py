from __future__ import annotations

import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import yaml

from scripts.manifest_checks import load_yaml, manifest_errors
from scripts.payload_checks import privacy_errors, size_errors, voice_errors

EXPECTED_SKILLS = {
    "crit",
    "crit-cli",
    "global-coding-policy",
    "goal-prompt",
    "hermes-agent-skill-authoring",
    "hermes-skill-lifecycle",
    "hermes-state-db-wal",
    "honcho-profile-tuning",
    "meaning-preserving-rewrite",
    "plan",
}
REQUIRED_FILES = {
    "AGENTS.md",
    "README.md",
    "SOUL.md",
    "config.yaml",
    "distribution.yaml",
    "templates/AGENTS.md",
}
FORBIDDEN_CONFIG_KEYS = {
    "api_key",
    "base_url",
    "fallback",
    "fallback_chain",
    "fallback_providers",
    "model",
    "models",
    "plugins",
    "provider",
    "reference_models",
}
EXCLUDED_PATH_PARTS = {
    "claude-code",
    "claude-code-config-inventory",
    "claude-subscription-oauth",
    "deterministic-interview-workflows",
    "hermes-raft-integration",
    "hermes-surface-composition",
    "plan-package-validation",
    "profile-builder",
}
LINK_PATTERN = re.compile(r"`((?:references|templates|scripts|assets)/[^`\s]+)`")


def required_file_errors(root: Path) -> list[str]:
    return [f"missing required file: {name}" for name in sorted(REQUIRED_FILES) if not (root / name).is_file()]


def walk_keys(value, prefix=""):
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            yield path, str(key).casefold().replace("-", "_").replace(" ", "_")
            yield from walk_keys(child, path)
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            yield from walk_keys(child, f"{prefix}[{index}]")


def config_errors(root: Path) -> list[str]:
    try:
        config = load_yaml(root / "config.yaml")
    except ValueError as error:
        return [str(error)]
    errors = []
    for path, key in walk_keys(config):
        if key in FORBIDDEN_CONFIG_KEYS:
            errors.append(f"config contains excluded choice or secret key: {path}")
    return errors


def parse_skill(path: Path) -> tuple[dict, str]:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n") or "\n---\n" not in content[4:]:
        return {}, content
    frontmatter, body = content[4:].split("\n---\n", 1)
    data = yaml.safe_load(frontmatter)
    return (data if isinstance(data, dict) else {}), body


def skill_errors(root: Path) -> list[str]:
    paths = sorted((root / "skills").rglob("SKILL.md")) if (root / "skills").exists() else []
    parsed = [(path, *parse_skill(path)) for path in paths]
    names = {str(data.get("name", "")) for _, data, _ in parsed}
    errors = [f"skill set mismatch: {sorted(names ^ EXPECTED_SKILLS)}"] if names != EXPECTED_SKILLS else []
    for path, data, body in parsed:
        description = str(data.get("description", ""))
        if data.get("author") != "Kiren Srinivasan":
            errors.append(f"invalid author: {path}")
        if len(description) >= 60 or not description.startswith("Use when "):
            errors.append(f"invalid description: {path}")
        if not body.strip() or len(body.splitlines()) >= 200:
            errors.append(f"invalid body line count: {path}")
        if path.stat().st_size > 100_000:
            errors.append(f"skill is over 100000 bytes: {path}")
        for reference in LINK_PATTERN.findall(body):
            if "<" not in reference and "*" not in reference and not (path.parent / reference).is_file():
                errors.append(f"missing linked file: {path.parent / reference}")
    return errors


def exclusion_errors(root: Path) -> list[str]:
    errors = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root)
        if relative_path.parts[0] in {".git", ".hermes", ".venv"}:
            continue
        relative = relative_path.as_posix().lower()
        if relative_path.parts[0].lower() == "plugins":
            errors.append(f"plugins are not allowed: {relative}")
            continue
        if any(part in relative for part in EXCLUDED_PATH_PARTS):
            errors.append(f"unfinished or Claude-specific material is present: {relative}")
    return errors


def validate(root: Path) -> list[str]:
    checks = (
        required_file_errors,
        manifest_errors,
        config_errors,
        skill_errors,
        exclusion_errors,
        privacy_errors,
        voice_errors,
        size_errors,
    )
    return [error for check in checks for error in check(root)]


def staged_mode_errors(root: Path) -> list[str]:
    output = subprocess.check_output(["git", "ls-files", "--stage", "-z"], cwd=root)
    errors = []
    for entry in output.decode().split("\0"):
        if not entry:
            continue
        metadata, path = entry.split("\t", 1)
        mode = metadata.split()[0]
        if mode != "100644":
            errors.append(f"unexpected staged mode {mode}: {path}")
    return errors


def validate_staged(root: Path) -> list[str]:
    tree = subprocess.check_output(["git", "write-tree"], cwd=root, text=True).strip()
    with tempfile.TemporaryDirectory(prefix="toolbox-staged-") as raw:
        temp = Path(raw)
        with (temp / "tree.tar").open("wb") as stream:
            subprocess.run(["git", "archive", tree], cwd=root, check=True, stdout=stream)
        extracted = temp / "tree"
        extracted.mkdir()
        with tarfile.open(temp / "tree.tar") as archive:
            archive.extractall(extracted, filter="data")
        return staged_mode_errors(root) + validate(extracted)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate_staged(root)
    if errors:
        print("\n".join(f"ERROR: {item}" for item in errors))
        return 1
    print("Distribution validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
