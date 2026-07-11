#!/usr/bin/env python3
"""Transactional export of native, sanitized public profile distributions."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import yaml

from candidate_policy import PolicyConfig, decide_profile, profile_candidate
from export_transaction import run_transaction, stage_tree, staged_text_errors
from profile_checks import load_profile_manifest, profile_package_errors
from real_runtime import install_profile
from sanitize_rules import sanitize_public_text
from toolbox_common import EXCLUDED_CATEGORIES, write

MANIFEST_KEYS = ('name', 'version', 'description', 'hermes_requires', 'author',
                 'license', 'homepage', 'env_requires', 'distribution_owned')
REUSABLE_CONFIG_KEYS = ('model', 'toolsets', 'agent', 'memory', 'skills', 'plugins',
                        'terminal', 'display', 'approvals')
GENERATED_FILES = ('distribution.yaml', 'config.yaml', 'manifest.json')


def _profile_included(rel: Path, owned: tuple[str, ...]) -> bool:
    if rel.name.startswith('.') or '__pycache__' in rel.parts or rel.suffix in {'.pyc', '.pyo'}:
        return False
    if rel.as_posix() in GENERATED_FILES:
        return False
    return any(rel.as_posix() == entry or rel.as_posix().startswith(entry + '/')
               for entry in owned)


def _owned_entries(data: dict) -> tuple[tuple[str, ...], list[str]]:
    owned = data.get('distribution_owned')
    if not isinstance(owned, list) or not owned:
        return (), ['distribution manifest must declare its distribution_owned paths']
    entries, errors = [], []
    for entry in owned:
        path = Path(str(entry))
        if path.is_absolute() or '..' in path.parts:
            errors.append(f'distribution_owned entry escapes the package: {entry}')
        else:
            entries.append(path.as_posix())
    return tuple(entries), errors


def _missing_owned(source: Path, entries: tuple[str, ...]) -> list[str]:
    return [f'distribution_owned path {entry!r} is missing from the source profile'
            for entry in entries if not (source / entry).exists()]


def native_distribution(data: dict) -> str:
    kept = {key: data[key] for key in MANIFEST_KEYS
            if data.get(key) not in (None, '', [])}
    return yaml.safe_dump(kept, sort_keys=False, allow_unicode=True)


def reusable_config(source: Path) -> tuple[str | None, list[str]]:
    try:
        data = yaml.safe_load((source / 'config.yaml').read_text(encoding='utf-8'))
    except (OSError, yaml.YAMLError) as exc:
        return None, [f'config.yaml is not readable reusable YAML: {exc}']
    if not isinstance(data, dict):
        return None, ['config.yaml must be a mapping of reusable settings']
    kept = {key: data[key] for key in REUSABLE_CONFIG_KEYS if key in data}
    return yaml.safe_dump(kept, sort_keys=False, allow_unicode=True), []


def profile_package_manifest(dst: Path, name: str) -> str:
    return json.dumps({
        'package': name,
        'type': 'profile',
        'sanitized': True,
        'included_files': sorted(str(p.relative_to(dst)) for p in dst.rglob('*') if p.is_file()),
        'excluded_categories': EXCLUDED_CATEGORIES,
    }, indent=2, sort_keys=True) + '\n'


def _install_check(staging: Path, name: str) -> list[str]:
    with tempfile.TemporaryDirectory(prefix='hermes-profile-export-') as tmp:
        home = Path(tmp) / 'home'
        home.mkdir()
        result = install_profile(home, staging, 'export-install-check')
    if result.returncode != 0:
        detail = (result.stdout + result.stderr).strip()[:300]
        return [f'{name}: real profile install failed: {detail}']
    return []


def _write_generated(staging: Path, repo: Path, cfg: PolicyConfig, data: dict,
                     config_text: str) -> None:
    generated = [('distribution.yaml', native_distribution(data)), ('config.yaml', config_text)]
    for name, text in generated:
        write(staging / name, sanitize_public_text(text, Path(name), repo, None,
                                                   cfg.private_profile_prefix,
                                                   cfg.public_plugin_profile))


def _stage_profile(candidate, repo: Path, cfg: PolicyConfig, staging: Path) -> list[str]:
    data, error = load_profile_manifest(candidate.source)
    if error:
        return [f'{candidate.name}: {error}']
    entries, errors = _owned_entries(data)
    errors += _missing_owned(candidate.source, entries)
    config_text, config_errors = reusable_config(candidate.source)
    errors += config_errors
    if errors:
        return [f'{candidate.name}: {error}' for error in errors]
    stage_tree(candidate.source, staging, repo, None, cfg.private_profile_prefix,
               cfg.public_plugin_profile, lambda rel: _profile_included(rel, entries))
    _write_generated(staging, repo, cfg, data, config_text)
    return []


def export_one_profile(hermes_home: Path, repo: Path, name: str, cfg: PolicyConfig) -> bool:
    candidate = profile_candidate(hermes_home, repo, name)
    decision = decide_profile(candidate, cfg)
    if not decision.accepted:
        raise SystemExit(f'public profile candidate {name!r} rejected: ' + '; '.join(decision.reasons))

    def build(staging: Path) -> list[str]:
        errors = _stage_profile(candidate, repo, cfg, staging)
        if errors:
            return errors
        write(staging / 'manifest.json', profile_package_manifest(staging, name))
        return (profile_package_errors(staging, f'profiles/{name}')
                + staged_text_errors(staging) + _install_check(staging, name))

    return run_transaction(candidate.destination, build, f'public profile candidate {name!r}')


def export_selected_profiles(hermes_home: Path, repo: Path, cfg: PolicyConfig) -> list[Path]:
    return [repo / 'profiles' / name for name in cfg.public_profiles
            if export_one_profile(hermes_home, repo, name, cfg)]
