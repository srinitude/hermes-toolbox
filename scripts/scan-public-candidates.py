#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

def run(cmd, cwd, capture=False):
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=capture, check=False)

def status(repo: Path) -> str:
    return subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo, text=True)

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['scan', 'validate', 'publish'], required=True)
    parser.add_argument('--hermes-home', default=os.environ.get('HERMES_HOME', str(Path.home() / '.hermes')))
    parser.add_argument('--repo', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--private-profile-prefix', default=os.environ.get('HERMES_PRIVATE_PROFILE_PREFIX', ''))
    parser.add_argument('--public-plugin-profile', default=os.environ.get('HERMES_PUBLIC_PLUGIN_PROFILE', ''))
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    if args.mode == 'scan':
        summary = {
            'repo': '<repo>',
            'has_skills': (repo / 'skills').exists(),
            'has_profiles': any(p.is_dir() for p in (repo / 'profiles').glob('*')) if (repo / 'profiles').exists() else False,
            'has_plugins': any(p.is_dir() for p in (repo / 'plugins').glob('*')) if (repo / 'plugins').exists() else False,
        }
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    if args.mode == 'validate':
        for script in ['validate-public-safety.py', 'validate-identity-neutrality.py']:
            res = run(['python3', str(repo / 'scripts' / script)], cwd=repo)
            if res.returncode != 0:
                return res.returncode
        return 0
    # publish mode
    before = status(repo)
    export_cmd = [
        'python3', str(repo / 'scripts' / 'export-public-toolbox.py'),
        '--hermes-home', args.hermes_home,
        '--repo', str(repo),
    ]
    if args.private_profile_prefix:
        export_cmd += ['--private-profile-prefix', args.private_profile_prefix]
    if args.public_plugin_profile:
        export_cmd += ['--public-plugin-profile', args.public_plugin_profile]
    approved = os.environ.get('HERMES_TOOLBOX_APPROVED_AUTHOR_LINE')
    if approved:
        export_cmd += ['--approved-author-line', approved]
    res = run(export_cmd, cwd=repo, capture=True)
    if res.returncode != 0:
        sys.stderr.write(res.stdout)
        sys.stderr.write(res.stderr)
        return res.returncode
    after = status(repo)
    if not after:
        return 0
    subprocess.check_call(['git', 'add', '.'], cwd=repo)
    staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=repo, text=True)
    if not staged.strip():
        return 0
    subprocess.check_call(['git', 'commit', '-m', 'chore: publish public toolbox candidates'], cwd=repo)
    subprocess.check_call(['git', 'push'], cwd=repo)
    print('Published public toolbox candidates.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
