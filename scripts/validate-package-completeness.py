#!/usr/bin/env python3
"""Completeness gate for public toolbox packages: plugin packages, native
profile distributions, personality primitives, and skill packages with
resolvable references, no placeholders or test doubles, and structural
limits on every public Python file."""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))

from package_checks import (  # noqa: E402
    check_package_manifest, check_repo_personalities, find_placeholders,
)
from profile_checks import profile_package_errors  # noqa: E402
from safety_checks import skill_reference_errors, validate_public_skill  # noqa: E402
from toolbox_common import check_child_file  # noqa: E402

REQUIRED_PLUGIN_FILES = ('README.md', 'plugin.yaml', '__init__.py', 'manifest.json')


def load_structure_checker():
    spec = importlib.util.spec_from_file_location(
        'verify_python_structure', SCRIPTS / 'verify-python-structure.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plugin_yaml_errors(pkg: Path, rel: str) -> list[str]:
    try:
        data = yaml.safe_load((pkg / 'plugin.yaml').read_text(encoding='utf-8'))
    except (OSError, yaml.YAMLError) as exc:
        return [f'{rel}/plugin.yaml: invalid YAML: {exc}']
    if not isinstance(data, dict):
        return [f'{rel}/plugin.yaml: must be a mapping']
    errors = []
    if data.get('name') != pkg.name:
        errors.append(f'{rel}/plugin.yaml: name must match directory')
    if data.get('kind') != 'standalone':
        errors.append(f'{rel}/plugin.yaml: kind must be standalone')
    for skill in data.get('provides_skills') or []:
        _, error = check_child_file(pkg, f'skills/{skill}/SKILL.md', 'bundled skill')
        if error:
            errors.append(f'{rel}: bundled skill {skill!r} missing skills/{skill}/SKILL.md')
    return errors


def structure_errors(pkg: Path, repo: Path, structure) -> list[str]:
    errors: list[str] = []
    for py in sorted(pkg.rglob('*.py')):
        if '__pycache__' not in py.parts:
            errors.extend(structure.check_file(py.resolve(), repo.resolve()))
    return errors


def check_plugin_package(pkg: Path, rel: str, repo: Path, structure) -> list[str]:
    errors = [f'{rel}: missing {name}' for name in REQUIRED_PLUGIN_FILES
              if not (pkg / name).is_file()]
    if errors:
        return errors
    errors += plugin_yaml_errors(pkg, rel)
    errors += check_package_manifest(pkg, rel, 'plugin')
    errors += [f'{rel}/{error}' for error in find_placeholders(pkg)]
    errors += structure_errors(pkg, repo, structure)
    return errors


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
    structure = load_structure_checker()
    errors: list[str] = []
    for pkg in package_dirs(repo / 'plugins'):
        errors += check_plugin_package(pkg, f'plugins/{pkg.name}', repo, structure)
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
