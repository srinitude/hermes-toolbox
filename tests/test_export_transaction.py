"""Transactional export contracts: failures preserve last-known-good bytes."""
from __future__ import annotations

import re
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


class SanitizationFailureTests(TransactionCase):
    def test_sanitizer_validation_failure_preserves_existing_package(self):
        credential_line = 'api_key = ' + 'abcdef0123456789abcdef'
        (self.source / 'notes.md').write_text(credential_line + '\n', encoding='utf-8')
        self.assert_last_known_good_preserved(self.export())

    def test_semantic_corruption_preserves_existing_package(self):
        executable = (Path('/') / 'home' / 'example-user' / '.hermes' /
                      'hermes-agent' / 'venv' / 'bin' / 'python')
        corrupt = f'Run {executable} task.py\n'
        (self.source / 'notes.md').write_text(corrupt, encoding='utf-8')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('placeholder-bearing executable path', result.stderr)

    def test_case_variant_executable_placeholder_preserves_package(self):
        corrupt = 'Run <PRIVATE-TERM>/venv/bin/python task.py\n'
        (self.source / 'notes.md').write_text(corrupt, encoding='utf-8')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('placeholder-bearing executable path', result.stderr)


class ProductAuthorExportTests(TransactionCase):
    def export_author(self, author: str, prose: str | None = None):
        skill = self.home / 'skills' / SKILL_REL / 'SKILL.md'
        source = skill.read_text(encoding='utf-8')
        source = re.sub(r'(?m)^author: .+$', f'author: {author}', source, count=1)
        skill.write_text(source + f'\nRun {prose or author}.\n', encoding='utf-8')
        return self.export()

    def test_explicit_product_authors_pass_full_export_validation(self):
        authors = ('Hermes Agent', 'Nous Research', 'OpenAI Codex', 'OpenAI',
                   'Acme Software')
        for author in authors:
            with self.subTest(author=author):
                result = self.export_author(author)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_unknown_single_word_author_remains_identity_protected(self):
        result = self.export_author('Zaphod')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('approved author identity', result.stderr)

    def test_unknown_two_word_author_remains_identity_protected(self):
        result = self.export_author('Jane Team', 'jane team')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('approved author identity', result.stderr)

    def test_author_identity_match_requires_word_boundaries(self):
        result = self.export_author('Jane Team', 'janet teamwork')
        self.assertEqual(result.returncode, 0, result.stderr)


class MarkupExportTests(TransactionCase):
    def test_valid_html_passes_full_export_validation(self):
        readme = self.source / 'README.md'
        html = '\n<a href="https://example.com">docs</a>\n<details open>text</details>\n'
        readme.write_text(readme.read_text(encoding='utf-8') + html, encoding='utf-8')
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_malformed_known_placeholders_fail_closed(self):
        for malformed in ('<<private-term>', '<private-term?', '<private-term!'):
            with self.subTest(malformed=malformed):
                readme = self.source / 'README.md'
                baseline = readme.read_text(encoding='utf-8')
                readme.write_text(baseline + f'\n{malformed}\n', encoding='utf-8')
                result = self.export()
                self.assert_last_known_good_preserved(result)
                self.assertIn('malformed placeholder', result.stderr)
                readme.write_text(baseline, encoding='utf-8')


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
