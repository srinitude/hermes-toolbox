"""Whole-batch export rollback: any late failure restores the full repo tree."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.support import FIXTURES, make_home, make_repo, run_exporter

SKILL_REL = 'fixtures/complete-skill'


def repo_tree(repo: Path) -> dict[str, bytes]:
    return {path.relative_to(repo).as_posix(): path.read_bytes()
            for path in sorted(repo.rglob('*'))
            if path.is_file() and '.git' not in path.relative_to(repo).parts}


class BatchRollbackCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='toolbox-batch-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = make_repo(self.base)
        self.home = make_home(self.base, plugins={'aaa-plugin': FIXTURES / 'complete-plugin',
                                                  'bbb-plugin': FIXTURES / 'complete-plugin'})
        shutil.copytree(FIXTURES / 'complete-skill', self.home / 'skills' / SKILL_REL)
        self.change_list = self.base / 'changes.lst'

    def export(self, *plugins: str, with_change_list: bool = False):
        args = ['--public-skill', SKILL_REL]
        for name in plugins:
            args += ['--public-plugin', name]
        args += ['--public-plugin-profile', 'pub-src']
        if with_change_list:
            args += ['--change-list', str(self.change_list)]
        return run_exporter(self.repo, self.home, *args)

    def source_plugin(self, name: str) -> Path:
        return self.home / 'profiles' / 'pub-src' / 'plugins' / name

    def append_readme_update(self, name: str) -> None:
        readme = self.source_plugin(name) / 'README.md'
        readme.write_text(readme.read_text(encoding='utf-8') + '\nUpdated usage note.\n',
                          encoding='utf-8')


class LateCandidateFailureTests(BatchRollbackCase):
    def test_second_candidate_failure_restores_entire_tree(self):
        baseline_run = self.export('aaa-plugin', 'bbb-plugin')
        self.assertEqual(baseline_run.returncode, 0, baseline_run.stderr)
        baseline = repo_tree(self.repo)
        self.append_readme_update('aaa-plugin')
        (self.source_plugin('bbb-plugin') / 'README.md').unlink()
        result = self.export('aaa-plugin', 'bbb-plugin', with_change_list=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('bbb-plugin', result.stderr)
        self.assertEqual(repo_tree(self.repo), baseline)
        self.assertFalse(self.change_list.exists())


class NewDestinationRollbackTests(BatchRollbackCase):
    def test_failure_removes_destination_created_earlier_in_batch(self):
        baseline_run = self.export('bbb-plugin')
        self.assertEqual(baseline_run.returncode, 0, baseline_run.stderr)
        baseline = repo_tree(self.repo)
        credential_line = 'api_key = ' + 'abcdef0123456789abcdef'
        (self.source_plugin('bbb-plugin') / 'notes.md').write_text(credential_line + '\n',
                                                                   encoding='utf-8')
        result = self.export('aaa-plugin', 'bbb-plugin')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.repo / 'plugins' / 'aaa-plugin').exists())
        self.assertEqual(repo_tree(self.repo), baseline)


class ValidatorFailureRollbackTests(BatchRollbackCase):
    def test_completeness_failure_restores_destinations_and_inventories(self):
        baseline_run = self.export('aaa-plugin', 'bbb-plugin')
        self.assertEqual(baseline_run.returncode, 0, baseline_run.stderr)
        stale = self.repo / 'plugins' / 'stale-pkg'
        stale.mkdir()
        (stale / 'plugin.yaml').write_text('name: stale-pkg\nkind: standalone\n',
                                           encoding='utf-8')
        baseline = repo_tree(self.repo)
        self.append_readme_update('aaa-plugin')
        result = self.export('aaa-plugin', 'bbb-plugin', with_change_list=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('stale-pkg', result.stderr)
        self.assertEqual(repo_tree(self.repo), baseline)
        self.assertFalse(self.change_list.exists())


if __name__ == '__main__':
    unittest.main()
