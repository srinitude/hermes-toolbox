"""Fail-closed contracts for the automated public toolbox publisher."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

from tests.publisher_support import (
    PROFILE_ARGS, append_source_update, committed_files, git_in, head,
    make_publisher_repo, origin_main, publisher_env, push_baseline,
    run_publisher_script, run_scan_publish, seed_commit, TEST_IDENTITY,
)
from tests.support import SCRIPTS

SWEEP_RE = re.compile(r'git\s+add\s+(?:-A\b|--all\b|-u\b|\.(?:\s|$))'
                      r'|[\'"]add[\'"],\s*[\'"](?:-A|--all|-u|\.)[\'"]')
TRAILER_RE = re.compile(r'(?im)^(co-authored-by|generated-by|ai-authored-by):')
FAILING_TEST = '''import unittest
from pathlib import Path


class GuardTests(unittest.TestCase):
    def test_release_notes_exist(self):
        repo = Path(__file__).resolve().parents[1]
        self.assertTrue((repo / 'RELEASE_NOTES.md').is_file())
'''


class PublisherCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='toolbox-publisher-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo, self.home = make_publisher_repo(self.base)
        self.bare = push_baseline(self.repo, self.base, self.home)
        self.env = publisher_env(self.base)
        self.baseline = head(self.repo)

    def publish(self, *extra: str) -> subprocess.CompletedProcess:
        return run_scan_publish(self.repo, self.home, self.env, *(extra or PROFILE_ARGS))

    def assert_blocked(self, result, needle: str, head_at: str, origin_at: str) -> None:
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(needle, result.stderr)
        self.assertEqual(head(self.repo), head_at)
        self.assertEqual(origin_main(self.bare), origin_at)


class StaticSourceTests(unittest.TestCase):
    def test_publisher_sources_ban_sweeps_autostash_and_pulls(self):
        for name in ('publish-public-candidates.sh', 'scan-public-candidates.py'):
            text = (SCRIPTS / name).read_text(encoding='utf-8')
            self.assertNotIn('--autostash', text, name)
            self.assertNotIn('git pull', text, name)
            self.assertIsNone(SWEEP_RE.search(text), name)


class PreconditionTests(PublisherCase):
    def test_dirty_starting_worktree_fails_closed(self):
        (self.repo / 'scratch.txt').write_text('leftover residue\n', encoding='utf-8')
        self.assert_blocked(self.publish(), 'dirty', self.baseline, self.baseline)

    def test_checkout_must_sit_exactly_at_origin_main(self):
        git_in(self.repo, 'commit', '-q', '--allow-empty', '-m', 'local drift')
        drift = head(self.repo)
        self.assert_blocked(self.publish(), 'origin/main', drift, self.baseline)

    def test_missing_plugin_allowlist_fails_closed(self):
        (self.repo / '.git' / 'info' / 'public-plugin-allowlist.txt').unlink()
        self.assert_blocked(self.publish(), 'public-plugin-allowlist.txt',
                            self.baseline, self.baseline)

    def test_missing_profile_allowlist_fails_closed(self):
        (self.repo / '.git' / 'info' / 'public-profile-allowlist.txt').unlink()
        self.assert_blocked(self.publish(), 'public-profile-allowlist.txt',
                            self.baseline, self.baseline)


class IdentityAndGateTests(PublisherCase):
    def test_missing_repo_local_identity_fails_closed(self):
        git_in(self.repo, 'config', '--unset', 'user.name')
        git_in(self.repo, 'config', '--unset', 'user.email')
        append_source_update(self.home)
        self.assert_blocked(self.publish(), 'repo-local git identity',
                            self.baseline, self.baseline)

    def test_plugin_selection_requires_source_profile_gate(self):
        result = run_scan_publish(self.repo, self.home, self.env)
        self.assert_blocked(result, 'source profile gate', self.baseline, self.baseline)


class ValidationGateTests(PublisherCase):
    def test_validator_failure_blocks_commit_and_push(self):
        stale = self.repo / 'plugins' / 'stale-pkg'
        stale.mkdir()
        (stale / 'plugin.yaml').write_text('name: stale-pkg\nkind: standalone\n',
                                           encoding='utf-8')
        pushed = seed_commit(self.repo, 'seed an incomplete tracked package')
        append_source_update(self.home)
        self.assert_blocked(self.publish(), 'stale-pkg', pushed, pushed)

    def test_failing_repo_test_blocks_commit_and_push(self):
        tests_dir = self.repo / 'tests'
        tests_dir.mkdir()
        (tests_dir / '__init__.py').write_text('"""Seeded repo tests."""\n', encoding='utf-8')
        (tests_dir / 'test_guard.py').write_text(FAILING_TEST, encoding='utf-8')
        pushed = seed_commit(self.repo, 'seed a repository test suite')
        append_source_update(self.home)
        self.assert_blocked(self.publish(), 'FAILED', pushed, pushed)


class PublishFlowTests(PublisherCase):
    def test_publish_commits_exact_accepted_paths_with_repo_identity(self):
        append_source_update(self.home)
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        files = committed_files(self.repo)
        self.assertIn('plugins/demo-plugin/README.md', files)
        self.assertIn('inventory/source-fingerprints.json', files)
        for path in files:
            self.assertTrue(path.startswith(('plugins/demo-plugin/', 'inventory/')), path)
        self.assertEqual(origin_main(self.bare), head(self.repo))
        self.assertNotEqual(head(self.repo), self.baseline)
        name, email = TEST_IDENTITY
        meta = git_in(self.repo, 'log', '-1', '--format=%an%n%ae%n%cn%n%ce%n%B').stdout
        self.assertEqual(meta.splitlines()[:4], [name, email, name, email])
        self.assertIsNone(TRAILER_RE.search('\n'.join(meta.splitlines()[4:])))


class NoOpTests(PublisherCase):
    def test_no_candidate_change_is_a_silent_noop(self):
        result = self.publish()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual(head(self.repo), self.baseline)
        self.assertEqual(origin_main(self.bare), self.baseline)


class LockTests(PublisherCase):
    def test_lock_contention_skips_quietly(self):
        lock = Path(self.env['HERMES_TOOLBOX_LOCK'])
        lock.touch()
        holder = subprocess.Popen(['flock', '-x', str(lock), 'sleep', '30'])
        self.addCleanup(holder.wait)
        self.addCleanup(holder.terminate)
        append_source_update(self.home)
        for _ in range(100):
            probe = subprocess.run(['flock', '-n', '-x', str(lock), 'true'],
                                   capture_output=True)
            if probe.returncode != 0:
                break
            time.sleep(0.05)
        result = run_publisher_script(self.repo, self.home, self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual(head(self.repo), self.baseline)


class BashPublisherTests(PublisherCase):
    def test_bash_publisher_delegates_to_failclosed_scan(self):
        append_source_update(self.home)
        result = run_publisher_script(self.repo, self.home, self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(origin_main(self.bare), head(self.repo))
        self.assertIn('plugins/demo-plugin/README.md', committed_files(self.repo))

    def test_github_origin_requires_public_visibility_proof(self):
        url = 'https://github.com/srinitude/hermes-toolbox.git'
        git_in(self.repo, 'remote', 'set-url', 'origin', url)
        append_source_update(self.home)
        result = run_publisher_script(self.repo, self.home, self.env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('visibility', result.stderr)
        self.assertEqual(head(self.repo), self.baseline)


if __name__ == '__main__':
    unittest.main()
