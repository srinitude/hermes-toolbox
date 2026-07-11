#!/usr/bin/env python3
"""Scan public toolbox state and publish accepted candidates fail-closed."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
sys.path.insert(0, str(Path(__file__).resolve().parent))

from candidate_policy import read_allowlist  # noqa: E402
from publisher_transaction import PublisherTransaction, stage_paths  # noqa: E402
from toolbox_common import git_info_dir  # noqa: E402

COMMIT_MESSAGE = 'chore: publish public toolbox candidates'
REQUIRED_ALLOWLISTS = ('public-plugin-allowlist.txt', 'public-profile-allowlist.txt')
VALIDATORS = ('validate-public-safety.py', 'validate-identity-neutrality.py',
              'validate-package-completeness.py')
INVENTORY_FILES = ('inventory/public-manifest.json', 'inventory/source-fingerprints.json')


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return run(['git', *args], repo)


def fail(message: str) -> int:
    print(f'publish blocked: {message}', file=sys.stderr)
    return 1


def gated(result: subprocess.CompletedProcess, label: str) -> int:
    """Forward diagnostics to stderr only; stdout stays silent for cron no-ops."""
    sys.stderr.write(result.stderr)
    if result.returncode == 0:
        return 0
    sys.stderr.write(result.stdout)
    return fail(f'{label} failed with exit code {result.returncode}')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['scan', 'validate', 'publish'], required=True)
    parser.add_argument('--hermes-home', default=os.environ.get('HERMES_HOME', str(Path.home() / '.hermes')))
    parser.add_argument('--repo', default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument('--private-profile-prefix', default=os.environ.get('HERMES_PRIVATE_PROFILE_PREFIX', ''))
    parser.add_argument('--public-plugin-profile', default=os.environ.get('HERMES_PUBLIC_PLUGIN_PROFILE', ''))
    return parser.parse_args()


def scan_summary(repo: Path) -> dict:
    def has_package_dirs(root: Path) -> bool:
        return root.exists() and any(p.is_dir() for p in root.glob('*'))
    return {'repo': '<repo>', 'has_skills': (repo / 'skills').exists(),
            'has_profiles': has_package_dirs(repo / 'profiles'),
            'has_plugins': has_package_dirs(repo / 'plugins')}


def worktree_error(repo: Path) -> str | None:
    status = git(repo, 'status', '--porcelain')
    if status.returncode != 0:
        return 'target is not a git worktree'
    if status.stdout.strip():
        return 'starting worktree is dirty; refusing to publish'
    ignored = git(repo, 'clean', '-ndx')
    if ignored.returncode != 0 or ignored.stdout.strip():
        return 'starting worktree has ignored or untracked residue; refusing to publish'
    origin = git(repo, 'rev-parse', '--verify', '--quiet', 'origin/main')
    if origin.returncode != 0:
        return 'origin/main is not resolvable in the target worktree'
    if git(repo, 'rev-parse', 'HEAD').stdout.strip() != origin.stdout.strip():
        return 'checkout is not exactly at origin/main; refusing to publish'
    return None


def identity_configured(repo: Path) -> bool:
    name = git(repo, 'config', '--local', '--get', 'user.name')
    email = git(repo, 'config', '--local', '--get', 'user.email')
    return (name.returncode == 0 and email.returncode == 0
            and bool(name.stdout.strip()) and bool(email.stdout.strip()))


def policy_error(repo: Path, args: argparse.Namespace) -> str | None:
    info = git_info_dir(repo)
    for name in REQUIRED_ALLOWLISTS:
        if not (info / name).is_file():
            return f'missing required local allowlist {name}'
    if not identity_configured(repo):
        return 'repo-local git identity (user.name and user.email) is not configured'
    plugins = read_allowlist(info / 'public-plugin-allowlist.txt', 'public plugin')
    if plugins and not args.public_plugin_profile:
        return 'plugins are allowlisted but no source profile gate (--public-plugin-profile) is configured'
    return None


def export_candidates(repo: Path, args: argparse.Namespace, change_list: Path) -> int:
    cmd = ['python3', str(repo / 'scripts' / 'export-public-toolbox.py'),
           '--hermes-home', args.hermes_home, '--repo', str(repo),
           '--change-list', str(change_list)]
    if args.private_profile_prefix:
        cmd += ['--private-profile-prefix', args.private_profile_prefix]
    if args.public_plugin_profile:
        cmd += ['--public-plugin-profile', args.public_plugin_profile]
    return gated(run(cmd, repo), 'transactional exporter')


def validation_packet(repo: Path) -> list[list[str]]:
    packet = [['python3', str(repo / 'scripts' / name)] for name in VALIDATORS]
    if (repo / 'profiles' / 'hermes-agent-tutorial').is_dir():
        packet.append(['python3', str(repo / 'scripts' / 'validate-tutorial-suite.py')])
    targets = [name for name in ('scripts', 'tests', 'plugins') if (repo / name).is_dir()]
    packet.append(['python3', str(repo / 'scripts' / 'verify-python-structure.py'), *targets])
    if (repo / 'tests').is_dir():
        packet.append(['python3', '-m', 'unittest', 'discover', '-s', 'tests'])
    return packet


def run_validation_packet(repo: Path) -> int:
    for cmd in validation_packet(repo):
        code = gated(run(cmd, repo), ' '.join(cmd[1:]))
        if code != 0:
            return code
    return 0


def accepted_entries(change_list: Path) -> list[str]:
    if not change_list.is_file():
        return []
    return [entry for entry in change_list.read_text(encoding='utf-8').split('\0') if entry]


def stage_accepted(repo: Path, entries: list[str]) -> int:
    try:
        stage_paths(repo, [*entries, *INVENTORY_FILES])
    except RuntimeError as exc:
        return fail(str(exc))
    return 0


def commit_and_push(repo: Path) -> int:
    committed = git(repo, 'commit', '-q', '-m', COMMIT_MESSAGE)
    if committed.returncode != 0:
        return fail(f'commit failed: {(committed.stdout + committed.stderr).strip()}')
    pushed = git(repo, 'push', '--quiet', 'origin', 'HEAD:refs/heads/main')
    if pushed.returncode != 0:
        return fail(f'push failed: {pushed.stderr.strip()}')
    print(f"published accepted public candidates: {git(repo, 'rev-parse', 'HEAD').stdout.strip()}")
    return 0


def publish(repo: Path, args: argparse.Namespace) -> int:
    error = worktree_error(repo) or policy_error(repo, args)
    if error:
        return fail(error)
    with PublisherTransaction(repo) as transaction:
        with tempfile.TemporaryDirectory(prefix='toolbox-publish-') as tmp:
            change_list = Path(tmp) / 'accepted.lst'
            code = export_candidates(repo, args, change_list)
            code = code or run_validation_packet(repo)
            code = code or stage_accepted(repo, accepted_entries(change_list))
        if code != 0:
            return code
        if not git(repo, 'diff', '--cached', '--name-only').stdout.strip():
            transaction.finish()
            return 0
        code = commit_and_push(repo)
        if code == 0:
            transaction.finish()
        return code


def run_validate_mode(repo: Path) -> int:
    for name in VALIDATORS:
        code = gated(run(['python3', str(repo / 'scripts' / name)], repo), name)
        if code != 0:
            return code
    return 0


def main() -> int:
    args = parse_args()
    repo = Path(args.repo).resolve()
    if args.mode == 'scan':
        print(json.dumps(scan_summary(repo), indent=2, sort_keys=True))
        return 0
    if args.mode == 'validate':
        return run_validate_mode(repo)
    return publish(repo, args)


if __name__ == '__main__':
    raise SystemExit(main())
