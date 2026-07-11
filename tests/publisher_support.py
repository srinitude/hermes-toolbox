"""Real git-repo fixtures for exercising the fail-closed publisher scripts."""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from tests.support import FIXTURES, clean_env, make_home, make_repo, run_exporter

SKILL_REL = 'fixtures/complete-skill'
PROFILE_ARGS = ('--public-plugin-profile', 'pub-src')
TEST_IDENTITY = ('Toolbox Publisher', 'publisher@example.com')


def git_in(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(['git', '-C', str(repo), *args], text=True,
                          capture_output=True, check=True)


def head(repo: Path) -> str:
    return git_in(repo, 'rev-parse', 'HEAD').stdout.strip()


def origin_main(bare: Path) -> str:
    return git_in(bare, 'rev-parse', 'main').stdout.strip()


def committed_files(repo: Path) -> list[str]:
    return git_in(repo, 'show', '--name-only', '--format=', 'HEAD').stdout.split()


def publisher_env(base: Path) -> dict[str, str]:
    """Isolated environment: no ambient git/gh identity or tokens leak in."""
    env = clean_env()
    for key in ('GH_TOKEN', 'GITHUB_TOKEN', 'GH_CONFIG_DIR', 'XDG_CONFIG_HOME'):
        env.pop(key, None)
    env.update({'HOME': str(base), 'GIT_CONFIG_GLOBAL': '/dev/null',
                'GIT_CONFIG_SYSTEM': '/dev/null', 'GIT_TERMINAL_PROMPT': '0',
                'HERMES_TOOLBOX_LOCK': str(base / 'publisher.lock')})
    return env


def _write_allowlists(repo: Path) -> None:
    info = repo / '.git' / 'info'
    (info / 'public-skill-allowlist.txt').write_text(SKILL_REL + '\n', encoding='utf-8')
    (info / 'public-plugin-allowlist.txt').write_text('demo-plugin\n', encoding='utf-8')
    (info / 'public-profile-allowlist.txt').write_text('', encoding='utf-8')


def make_publisher_repo(base: Path) -> tuple[Path, Path]:
    """Build a real repo with local allowlists plus a Hermes-home source tree."""
    repo = make_repo(base)
    git_in(repo, 'symbolic-ref', 'HEAD', 'refs/heads/main')
    git_in(repo, 'config', 'user.name', TEST_IDENTITY[0])
    git_in(repo, 'config', 'user.email', TEST_IDENTITY[1])
    _write_allowlists(repo)
    home = make_home(base, plugins={'demo-plugin': FIXTURES / 'complete-plugin'})
    shutil.copytree(FIXTURES / 'complete-skill', home / 'skills' / SKILL_REL)
    return repo, home


def push_baseline(repo: Path, base: Path, home: Path) -> Path:
    """Export once, commit the result as main, and push it to a local bare origin."""
    bare = base / 'origin.git'
    subprocess.run(['git', 'init', '-q', '--bare', str(bare)], check=True)
    git_in(repo, 'remote', 'add', 'origin', str(bare))
    result = run_exporter(repo, home, *PROFILE_ARGS)
    assert result.returncode == 0, result.stderr
    git_in(repo, 'add', '-A')
    git_in(repo, 'commit', '-q', '-m', 'baseline public artifacts')
    git_in(repo, 'push', '-q', '-u', 'origin', 'main')
    return bare


def append_source_update(home: Path) -> None:
    readme = home / 'profiles' / 'pub-src' / 'plugins' / 'demo-plugin' / 'README.md'
    readme.write_text(readme.read_text(encoding='utf-8') + '\nUpdated usage note.\n',
                      encoding='utf-8')


def seed_commit(repo: Path, message: str) -> str:
    git_in(repo, 'add', '-A')
    git_in(repo, 'commit', '-q', '-m', message)
    git_in(repo, 'push', '-q', 'origin', 'main')
    return head(repo)


def run_scan_publish(repo: Path, home: Path, env: dict[str, str],
                     *extra: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(repo / 'scripts' / 'scan-public-candidates.py'),
           '--mode', 'publish', '--repo', str(repo), '--hermes-home', str(home), *extra]
    return subprocess.run(cmd, capture_output=True, text=True, env=env)


def run_publisher_script(repo: Path, home: Path,
                         env: dict[str, str]) -> subprocess.CompletedProcess:
    env = dict(env, HERMES_TOOLBOX_REPO=str(repo), HERMES_HOME=str(home),
               HERMES_PUBLIC_PLUGIN_PROFILE='pub-src')
    return subprocess.run(['bash', str(repo / 'scripts' / 'publish-public-candidates.sh')],
                          capture_output=True, text=True, env=env)
