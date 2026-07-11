"""Byte-exact rollback and path staging contracts for the publisher."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.publisher_support import (
    PROFILE_ARGS, append_source_update, git_in, head, make_publisher_repo,
    origin_main, publisher_env, push_baseline, run_scan_publish, seed_commit,
)
from tests.support import add_scripts_path

add_scripts_path()
from publisher_transaction import stage_paths  # noqa: E402

FAILING_TEST = '''import unittest


class LateFailureTests(unittest.TestCase):
    def test_late_failure(self):
        self.fail("late validation failure")
'''


class PublisherRollbackCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='publisher-rollback-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo, self.home = make_publisher_repo(self.base)
        self.bare = push_baseline(self.repo, self.base, self.home)
        self.env = publisher_env(self.base)
        self.baseline = head(self.repo)

    def publish(self):
        return run_scan_publish(self.repo, self.home, self.env, *PROFILE_ARGS)

    def assert_restored(self):
        self.assertEqual(head(self.repo), self.baseline)
        self.assertEqual(origin_main(self.bare), self.baseline)
        self.assertEqual(git_in(self.repo, 'status', '--porcelain').stdout, '')
        self.assertEqual(git_in(self.repo, 'diff', '--cached', '--binary').stdout, '')
        self.assertEqual(git_in(self.repo, 'diff', '--binary').stdout, '')


class LateFailureTests(PublisherRollbackCase):
    def test_repo_test_failure_restores_worktree_and_index(self):
        tests = self.repo / 'tests'
        tests.mkdir()
        (tests / 'test_late.py').write_text(FAILING_TEST, encoding='utf-8')
        self.baseline = seed_commit(self.repo, 'seed late failing test')
        append_source_update(self.home)
        result = self.publish()
        self.assertNotEqual(result.returncode, 0)
        self.assert_restored()

    def test_commit_hook_failure_restores_worktree_and_index(self):
        hook = self.repo / '.git' / 'hooks' / 'pre-commit'
        hook.write_text('#!/bin/sh\nexit 1\n', encoding='utf-8')
        hook.chmod(0o755)
        append_source_update(self.home)
        result = self.publish()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('commit failed', result.stderr)
        self.assert_restored()

    def test_push_failure_removes_local_commit(self):
        hook = self.bare / 'hooks' / 'pre-receive'
        hook.write_text('#!/bin/sh\nexit 1\n', encoding='utf-8')
        hook.chmod(0o755)
        append_source_update(self.home)
        result = self.publish()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('push failed', result.stderr)
        self.assert_restored()


class ExactPathStagingTests(unittest.TestCase):
    def test_deleted_accepted_path_is_staged(self):
        base = Path(tempfile.mkdtemp(prefix='publisher-stage-'))
        self.addCleanup(shutil.rmtree, base, True)
        repo = base / 'repo'
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        git_in(repo, 'config', 'user.name', 'Publisher Test')
        git_in(repo, 'config', 'user.email', 'publisher@example.com')
        path = repo / 'plugins' / 'withdrawn' / 'manifest.json'
        path.parent.mkdir(parents=True)
        path.write_text('{}\n', encoding='utf-8')
        git_in(repo, 'add', '--', 'plugins/withdrawn')
        git_in(repo, 'commit', '-q', '-m', 'seed package')
        path.unlink()
        stage_paths(repo, ['plugins/withdrawn'])
        staged = git_in(repo, 'diff', '--cached', '--name-status').stdout
        self.assertIn('D\tplugins/withdrawn/manifest.json', staged)


if __name__ == '__main__':
    unittest.main()
