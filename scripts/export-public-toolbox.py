#!/usr/bin/env python3
"""Export sanitized public toolbox packages. Thin CLI over the export modules."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from candidate_policy import public_skill_rels
from export_transaction import export_plugins_swept, export_public_skills
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
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    hermes_home = Path(args.hermes_home).resolve()
    ensure_local_info(repo, args.private_profile_prefix, args.public_plugin_profile,
                      args.approved_author_line)
    export_public_skills(hermes_home, repo, public_skill_rels(args.public_skill),
                         args.private_profile_prefix, args.public_plugin_profile)
    if args.public_plugin_profile:
        export_plugins_swept(hermes_home, repo, args.public_plugin_profile,
                             args.private_profile_prefix)
    write_inventory(repo)
    subprocess.check_call(['python3', str(repo / 'scripts' / 'validate-public-safety.py')], cwd=repo)
    subprocess.check_call(['python3', str(repo / 'scripts' / 'validate-identity-neutrality.py')], cwd=repo)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
