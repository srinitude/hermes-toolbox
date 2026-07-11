"""Transactional export contracts: failures preserve last-known-good bytes."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.support import FIXTURES, make_home, make_repo, run_exporter, tree_bytes

SKILL_REL = 'fixtures/complete-skill'


def change_entries(change_list: Path) -> list[str]:
    return [e for e in change_list.read_text(encoding='utf-8').split('\0') if e]


def staging_residue(repo: Path) -> list[Path]:
    return sorted(p for p in repo.rglob('*') if p.name.startswith(('.staging.', '.lkg.')))


class TransactionCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='toolbox-txn-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = make_repo(self.base)
        self.home = make_home(self.base, plugins={'demo-plugin': FIXTURES / 'complete-plugin'})
        shutil.copytree(FIXTURES / 'complete-skill', self.home / 'skills' / SKILL_REL)
        self.source = self.home / 'profiles' / 'pub-src' / 'plugins' / 'demo-plugin'
        self.plugin_dest = self.repo / 'plugins' / 'demo-plugin'
        self.skill_dest = self.repo / 'skills' / SKILL_REL
        baseline = self.export()
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        self.baseline_plugin = tree_bytes(self.plugin_dest)
        self.baseline_skill = tree_bytes(self.skill_dest)

    def export(self, change_list: Path | None = None):
        args = ['--public-skill', SKILL_REL, '--public-plugin', 'demo-plugin',
                '--public-plugin-profile', 'pub-src']
        if change_list is not None:
            args += ['--change-list', str(change_list)]
        return run_exporter(self.repo, self.home, *args)

    def assert_last_known_good_preserved(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tree_bytes(self.plugin_dest), self.baseline_plugin)
        self.assertEqual(tree_bytes(self.skill_dest), self.baseline_skill)
        self.assertEqual(staging_residue(self.repo), [])


class FailureIsolationTests(TransactionCase):
    def test_source_validation_failure_preserves_existing_package(self):
        (self.source / 'README.md').unlink()
        self.assert_last_known_good_preserved(self.export())

    def test_sanitizer_validation_failure_preserves_existing_package(self):
        credential_line = 'api_key = ' + 'abcdef0123456789abcdef'
        (self.source / 'notes.md').write_text(credential_line + '\n', encoding='utf-8')
        self.assert_last_known_good_preserved(self.export())

    def test_interrupted_staging_copy_preserves_existing_package(self):
        blocked = self.source / 'data' / 'payload.txt'
        blocked.parent.mkdir()
        blocked.write_text('payload\n', encoding='utf-8')
        blocked.chmod(0)
        self.addCleanup(blocked.chmod, 0o644)
        self.assert_last_known_good_preserved(self.export())

    def test_manifest_mismatch_preserves_existing_package(self):
        manifest = self.source / 'plugin.yaml'
        text = manifest.read_text(encoding='utf-8')
        manifest.write_text(text.replace('name: demo-plugin', 'name: other-plugin', 1),
                            encoding='utf-8')
        self.assert_last_known_good_preserved(self.export())

    def test_failed_skill_candidate_preserves_existing_skill(self):
        skill_md = self.home / 'skills' / SKILL_REL / 'SKILL.md'
        skill_md.write_text('---\nname: complete-skill\n---\n\ntoo short\n',
                            encoding='utf-8')
        self.assert_last_known_good_preserved(self.export())


class SymlinkFailureTests(TransactionCase):
    def test_unsafe_source_symlink_preserves_existing_packages(self):
        outside = self.base / 'outside-content.txt'
        outside.write_text('benign external content\n', encoding='utf-8')
        (self.source / 'outside-link.txt').symlink_to(outside)
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('symlink', result.stderr.lower())


class ReplacementTests(TransactionCase):
    def test_successful_candidate_replaces_only_its_package(self):
        readme = self.source / 'README.md'
        readme.write_text(readme.read_text(encoding='utf-8') + '\nUpdated usage note.\n',
                          encoding='utf-8')
        change_list = self.base / 'changes.lst'
        result = self.export(change_list)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(change_entries(change_list), ['plugins/demo-plugin'])
        self.assertIn('Updated usage note.',
                      (self.plugin_dest / 'README.md').read_text(encoding='utf-8'))
        self.assertNotEqual(tree_bytes(self.plugin_dest), self.baseline_plugin)
        self.assertEqual(tree_bytes(self.skill_dest), self.baseline_skill)
        self.assertEqual(staging_residue(self.repo), [])

    def test_no_change_produces_empty_change_list(self):
        change_list = self.base / 'changes.lst'
        result = self.export(change_list)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(change_entries(change_list), [])
        self.assertEqual(tree_bytes(self.plugin_dest), self.baseline_plugin)
        self.assertEqual(tree_bytes(self.skill_dest), self.baseline_skill)
        self.assertEqual(staging_residue(self.repo), [])


if __name__ == '__main__':
    unittest.main()
