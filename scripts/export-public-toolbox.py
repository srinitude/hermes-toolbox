#!/usr/bin/env python3
"""Export sanitized public toolbox packages. Thin CLI over the export modules."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from batch_transaction import BatchTransaction
from candidate_policy import (
    PolicyConfig, merged_allowlist, public_skill_rels, stale_destinations,
)
from export_transaction import (
    export_public_skills, export_selected_plugins, write_change_list,
)
from profile_export import export_selected_profiles
from public_manifest import write_inventory
from toolbox_common import git_info_dir, write


def ensure_local_info(repo: Path, private_prefix: str, public_plugin_profile: str,
                      approved_author_line: str) -> None:
    info = git_info_dir(repo)
    info.mkdir(parents=True, exist_ok=True)
    write(info / 'private-profile-denylist.txt', (private_prefix or '') + '\n')
    write(info / 'private-plugin-denylist.txt', (public_plugin_profile or '') + '\n')
    if approved_author_line:
        write(info / 'approved-authorship.txt', approved_author_line + '\n')
    existing = info / 'identity-denylist.txt'
    if not existing.exists():
        existing.write_text('', encoding='utf-8')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--hermes-home', default=os.environ.get('HERMES_HOME', str(Path.home() / '.hermes')))
    parser.add_argument('--repo', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--private-profile-prefix', default=os.environ.get('HERMES_PRIVATE_PROFILE_PREFIX', ''))
    parser.add_argument('--public-plugin-profile', default=os.environ.get('HERMES_PUBLIC_PLUGIN_PROFILE', ''))
    parser.add_argument('--approved-author-line', default=os.environ.get('HERMES_TOOLBOX_APPROVED_AUTHOR_LINE', ''))
    parser.add_argument('--public-skill', action='append', default=[], help='Relative skill path under $HERMES_HOME/skills to publish. Repeatable. Defaults to the repo allowlist.')
    parser.add_argument('--public-plugin', action='append', default=[], help='Plugin name from the public plugin source profile to publish. Repeatable. Merged with the local plugin allowlist.')
    parser.add_argument('--public-profile', action='append', default=[], help='Profile distribution name under $HERMES_HOME/profiles to publish. Repeatable. Merged with the local profile allowlist.')
    parser.add_argument('--change-list', default='', help='Write accepted repo-relative destinations to this file, NUL-delimited.')
    return parser.parse_args()


def selected_plugin_names(repo: Path, args: argparse.Namespace) -> tuple[str, ...]:
    names = merged_allowlist(repo, args.public_plugin, 'public-plugin-allowlist.txt', 'public plugin')
    if names and not args.public_plugin_profile:
        raise SystemExit('--public-plugin-profile is required when public plugins are selected')
    return names


def report_retained(repo: Path, cfg: PolicyConfig) -> None:
    selections = [('plugins', 'plugin', cfg.public_plugins),
                  ('profiles', 'profile', cfg.public_profiles)]
    for root_name, label, allowed in selections:
        stale = stale_destinations(repo, root_name, allowed)
        if stale:
            print(f'retaining existing unallowlisted {label} packages: ' + ', '.join(stale),
                  file=sys.stderr)


def run_exports(repo: Path, hermes_home: Path, skill_rels: list[Path],
                args: argparse.Namespace, cfg: PolicyConfig) -> list[Path]:
    accepted = export_public_skills(hermes_home, repo, skill_rels,
                                    args.private_profile_prefix, args.public_plugin_profile)
    accepted += export_selected_plugins(hermes_home, repo, cfg)
    accepted += export_selected_profiles(hermes_home, repo, cfg)
    return accepted


def planned_destinations(repo: Path, skill_rels: list[Path], cfg: PolicyConfig) -> list[Path]:
    return ([repo / 'skills' / rel for rel in skill_rels]
            + [repo / 'plugins' / name for name in cfg.public_plugins]
            + [repo / 'profiles' / name for name in cfg.public_profiles])


def run_validators(repo: Path) -> None:
    names = ['validate-public-safety.py', 'validate-identity-neutrality.py',
             'validate-package-completeness.py']
    if (repo / 'profiles' / 'hermes-agent-tutorial').is_dir():
        names.append('validate-tutorial-suite.py')
    for name in names:
        subprocess.check_call(['python3', str(repo / 'scripts' / name)], cwd=repo)


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    hermes_home = Path(args.hermes_home).resolve()
    cfg = PolicyConfig(
        public_plugins=selected_plugin_names(repo, args),
        public_plugin_profile=args.public_plugin_profile or None,
        private_profile_prefix=args.private_profile_prefix or None,
        public_profiles=merged_allowlist(repo, args.public_profile,
                                         'public-profile-allowlist.txt', 'public profile'))
    skill_rels = public_skill_rels(repo, args.public_skill)
    ensure_local_info(repo, args.private_profile_prefix, args.public_plugin_profile,
                      args.approved_author_line)
    with BatchTransaction(repo, planned_destinations(repo, skill_rels, cfg)):
        accepted = run_exports(repo, hermes_home, skill_rels, args, cfg)
        write_inventory(repo)
        run_validators(repo)
    report_retained(repo, cfg)
    if args.change_list:
        write_change_list(Path(args.change_list), repo, accepted)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
