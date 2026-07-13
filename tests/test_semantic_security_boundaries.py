"""Adversarial semantic boundaries at real export transactions."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.shell_cases import shell_variants
from tests.support import add_scripts_path, make_repo
from tests.test_export_transaction import TransactionCase
from tests.test_profile_export import ProfileTransactionCase

add_scripts_path()
from export_transaction import staged_text_errors  # noqa: E402
from safety_checks import validate_text_safety  # noqa: E402

class SemanticCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='semantic-boundary-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.stage = self.base / 'stage'
        self.stage.mkdir()

    def errors(self, text: str) -> list[str]:
        (self.stage / 'notes.md').write_text(text, encoding='utf-8')
        return staged_text_errors(self.stage)

class CanonicalSemanticParityTests(unittest.TestCase):
    def test_placeholder_executable_path_is_rejected(self):
        base = Path(tempfile.mkdtemp(prefix='canonical-semantic-'))
        self.addCleanup(shutil.rmtree, base, True)
        repo = make_repo(base)
        notes = repo / 'notes.md'
        notes.write_text('Run $HOME/venv/bin/python task.py\n')
        subprocess.run(['git', 'add', 'notes.md'], cwd=repo, check=True)
        errors = validate_text_safety(repo)
        self.assertTrue(any('executable path' in error for error in errors))


class PlaceholderBoundaryTests(SemanticCase):
    def test_cpp_empty_template_specialization_is_valid(self):
        self.assertEqual(self.errors('template<> struct Codec<int> {};\n'), [])

    def test_missing_opening_delimiters_are_rejected(self):
        malformed = ('private-term>', '[private-term>', 'private-term>>',
                     'private-term>> # damaged',
                     'author: "private-term>>"', '<path>>/venv/bin/python',
                     '<<path/>', '<<private-term data-x="1">',
                     '<<repo-author-email@example.com>',
                     'Run private-term> now.', 'private-term>>.',
                     'Run private-term>/venv/bin/python task.py',
                     '[private-term>>] # damaged',
                     '<private-term x="unterminated>',
                     'Run **private-term>** now.', '`private-term>`',
                     '~~private-term>~~', '<code>private-term></code>',
                     '_private-term>_', '{private-term>}')
        for text in malformed:
            with self.subTest(text=text):
                self.assertTrue(any('malformed placeholder' in error
                                    for error in self.errors(text + '\n')))

class ShellExecutableBoundaryTests(SemanticCase):
    def test_shell_quote_and_parameter_variants_are_rejected(self):
        for path in shell_variants():
            with self.subTest(path=path):
                self.assertTrue(any('executable path' in error
                                    for error in self.errors(f'Run {path}\n')))

    def test_shell_brace_expansion_limit_fails_closed(self):
        choices = ['python'] + [f'tool{index}' for index in range(64)]
        path = '$HOME/bin/{' + ','.join(choices) + '}'
        self.assertTrue(any('executable path' in error
                            for error in self.errors(f'Run {path}\n')))

class ShellUrlBoundaryTests(SemanticCase):
    def test_shell_operators_after_urls_are_not_masked(self):
        commands = ('curl https://example.com;$HOME/bin/python task.py',
                    'printf https://example.com|$HOME/bin/python task.py',
                    'true https://example.com&&$HOME/bin/python task.py',
                    'https://example.com&&$HOME/bin/python task.py',
                    'https://example.com;$HOME/bin/python task.py',
                    'curl https://example.com;"$HOME"/bin/python task.py',
                    '$(curl https://example.com)$HOME/bin/python task.py',
                    '`curl https://example.com`$HOME/bin/python task.py',
                    'curl https://example.com>$HOME/bin/python task.py',
                    'curl "https://example.com$($HOME/bin/python task.py)"',
                    'curl https://example.com/$($HOME/bin/python)')
        for command in commands:
            with self.subTest(command=command):
                self.assertTrue(any('executable path' in error
                                    for error in self.errors(command + '\n')))

    def test_prose_url_data_is_not_treated_as_shell(self):
        urls = ('See https://example.com/?x=1&$HOME/bin/python',
                'See https://example.com/path;$HOME/bin/python',
                'See https://example.com/?x=1|next=$HOME/bin/python')
        for text in urls:
            with self.subTest(text=text):
                self.assertEqual(self.errors(text + '\n'), [])


class TransactionBoundaryTests(TransactionCase):
    def test_cpp_empty_specialization_exports(self):
        readme = self.source / 'README.md'
        readme.write_text(readme.read_text() + '\ntemplate<> struct Codec<int> {};\n')
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_opening_placeholder_preserves_package(self):
        (self.source / 'notes.md').write_text('private-term>\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('malformed placeholder', result.stderr)

    def test_skill_body_nested_author_is_not_metadata(self):
        skill = self.home / 'skills/fixtures/complete-skill/SKILL.md'
        field = 'au' + 'thor'
        skill.write_text(skill.read_text() +
                         f'\n```yaml\n- {field}: Jane Fixture\n```\nRun Jane Fixture.\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('author field outside metadata', result.stderr)

    def test_plugin_block_author_line_is_not_metadata(self):
        manifest = self.source / 'plugin.yaml'
        manifest.write_text(manifest.read_text() + '\nnotes: |\n  author: Jane Fixture\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('author field outside metadata', result.stderr)


class SanitizationScopeTests(TransactionCase):
    def test_deny_term_replacement_uses_word_boundaries(self):
        info = self.repo / '.git' / 'info'
        info.mkdir(parents=True, exist_ok=True)
        (info / 'identity-denylist.txt').write_text('Ann\n')
        readme = self.source / 'README.md'
        readme.write_text(readme.read_text() + '\nAnnual report.\n')
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Annual report.', (self.plugin_dest / 'README.md').read_text())


class AuthorMetadataSafetyTests(TransactionCase):
    def skill(self) -> Path:
        return self.home / 'skills/fixtures/complete-skill/SKILL.md'

    def replace_author(self, value: str) -> None:
        path = self.skill()
        text = re.sub(r'(?m)^author: .+$', f'author: {value}', path.read_text(), count=1)
        path.write_text(text)

    def test_author_email_is_rejected_inside_metadata(self):
        email = 'jane@' + 'private.test'
        self.replace_author(f'Jane Person <{email}>')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('email address', result.stderr)

    def test_complex_author_scalar_is_rejected(self):
        self.replace_author('>-\n  Jane Fixture')
        with self.skill().open('a') as handle:
            handle.write('\nRun jane fixture.\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('complex author metadata', result.stderr)

    def test_quoted_empty_author_placeholder_is_rejected(self):
        self.replace_author('"<>"')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('malformed placeholder', result.stderr)


class ProfileAuthorLocationTests(ProfileTransactionCase):
    def test_profile_block_author_line_is_not_metadata(self):
        manifest = self.source / 'distribution.yaml'
        source = manifest.read_text()
        block = 'description: |\n  Fixture profile.\n  author: Jane Fixture'
        source = source.replace(
            'description: Fixture profile distribution proving the native public package shape.',
            block,
        )
        manifest.write_text(source)
        result = self.export_profile()
        self.assert_preserved(result)
        self.assertIn('author field outside metadata', result.stderr)


if __name__ == '__main__':
    unittest.main()
