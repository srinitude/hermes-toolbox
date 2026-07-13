#!/usr/bin/env python3
"""Completeness gate for public toolbox packages: plugin packages, native
profile distributions, personality primitives, and skill packages with
resolvable references, no placeholders or test doubles, and structural
limits on every public Python file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from package_checks import check_repo_personalities  # noqa: E402
from plugin_checks import plugin_package_errors  # noqa: E402
from profile_checks import profile_package_errors  # noqa: E402
from safety_checks import skill_reference_errors, validate_public_skill  # noqa: E402


def check_skill_package(pkg: Path, rel: str) -> list[str]:
    text = (pkg / 'SKILL.md').read_text(encoding='utf-8')
    return (validate_public_skill(f'{rel}/SKILL.md', text)
            + skill_reference_errors(rel, pkg))


def package_dirs(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return [child for child in sorted(root.iterdir())
            if child.is_dir() and child.name != '__pycache__']


def skill_packages(repo: Path) -> list[Path]:
    root = repo / 'skills'
    if not root.is_dir():
        return []
    return sorted(md.parent for md in root.rglob('SKILL.md'))


def validate(repo: Path) -> list[str]:
    errors: list[str] = []
    for pkg in package_dirs(repo / 'plugins'):
        errors += plugin_package_errors(pkg, f'plugins/{pkg.name}', repo)
    for pkg in package_dirs(repo / 'profiles'):
        errors += profile_package_errors(pkg, f'profiles/{pkg.name}')
    for pkg in skill_packages(repo):
        errors += check_skill_package(pkg, pkg.relative_to(repo).as_posix())
    errors += check_repo_personalities(repo)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate public package completeness.')
    parser.add_argument('--repo', type=Path, default=SCRIPTS.parent)
    args = parser.parse_args()
    errors = validate(args.repo)
    if errors:
        print('Package completeness validation failed:', file=sys.stderr)
        for error in errors:
            print(f'- {error}', file=sys.stderr)
        return 1
    print('Package completeness validation passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
