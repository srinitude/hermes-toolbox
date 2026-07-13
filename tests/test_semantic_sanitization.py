"""Semantic sanitization rejects corrupted operational public text."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from tests.support import add_scripts_path

add_scripts_path()
from export_transaction import staged_text_errors  # noqa: E402
from sanitize_rules import sanitize_public_text  # noqa: E402


class SanitizationCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='semantic-sanitize-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = self.base / 'repo'
        (self.repo / '.git/info').mkdir(parents=True)
        self.private_prefix = 'owner-'
        self.public_profile = 'non-owner-plugins'

    def sanitize(self, text: str, rel: str = 'SKILL.md') -> str:
        return sanitize_public_text(
            text, Path(rel), self.repo, 'Hermes Agent', self.private_prefix,
            self.public_profile,
        )

    def staged_errors(self, text: str) -> list[str]:
        package = self.base / 'package'
        package.mkdir(exist_ok=True)
        (package / 'notes.md').write_text(text, encoding='utf-8')
        return staged_text_errors(package)


class ScopeAwareAuthorTests(SanitizationCase):
    def test_author_does_not_rewrite_product_prose(self):
        source = '---\nauthor: Hermes Agent\n---\n\nRun Hermes Agent.\n'
        projected = self.sanitize(source)
        self.assertIn('author: Hermes Agent', projected)
        self.assertIn('Run Hermes Agent.', projected)
        self.assertNotIn('Run <repo-author-name>.', projected)


class ProfileNameTests(SanitizationCase):
    def test_public_source_profile_is_replaced_before_private_prefix(self):
        projected = self.sanitize(f'source: {self.public_profile}\n', 'README.md')
        self.assertEqual(projected, 'source: <public-plugin-source-profile>\n')
        self.assertNotIn('<first-name>', projected)

    def test_replacement_placeholder_survives_overlapping_private_terms(self):
        denylist = self.repo / '.git/info/identity-denylist.txt'
        for profile in ('profile', 'source', 'plugin', 'public'):
            with self.subTest(profile=profile):
                denylist.write_text(profile + '\n')
                projected = sanitize_public_text(
                    f'source: {profile}\n', Path('README.md'), self.repo,
                    'Hermes Agent', self.private_prefix, profile)
                self.assertEqual(projected, 'source: <public-plugin-source-profile>\n')

    def test_ambiguous_profile_mentions_are_rejected(self):
        sources = (f'source: x{self.public_profile}y\n',
                   f'Use {self.public_profile} for plugins.\n')
        for source in sources:
            with self.subTest(source=source):
                projected = self.sanitize(source, 'README.md')
                self.assertIn('<ambiguous-private-profile>', projected)
                errors = self.staged_errors(projected)
                self.assertTrue(any('ambiguous private profile' in error
                                    for error in errors), errors)


class ProfileFieldYamlTests(SanitizationCase):
    def test_yaml_scalar_encodings_are_replaced(self):
        escaped = self.public_profile.replace('plugins', '\\u0070lugins')
        sources = (f'source_profile: "{escaped}"\n',
                   f'source_profile:\n  {self.public_profile}\n',
                   f'Source: {self.public_profile}\n')
        for source in sources:
            with self.subTest(source=source):
                projected = self.sanitize(source, 'plugin.yaml')
                self.assertIn('<public-plugin-source-profile>', projected)
                self.assertNotIn(self.public_profile, projected)

    def test_escaped_profile_in_prose_is_rejected(self):
        escaped = self.public_profile.replace('plugins', '\\u0070lugins')
        projected = self.sanitize(f'description: "Use {escaped}."\n', 'plugin.yaml')
        self.assertIn('<ambiguous-private-profile>', projected)
        self.assertTrue(any('ambiguous private profile' in error
                            for error in self.staged_errors(projected)))

    def test_profile_occurrence_in_field_comment_is_rejected(self):
        source = f'source: {self.public_profile} # repeated {self.public_profile}\n'
        projected = self.sanitize(source, 'plugin.yaml')
        self.assertIn('<ambiguous-private-profile>', projected)
        errors = self.staged_errors(projected)
        self.assertTrue(any('ambiguous private profile' in error for error in errors))


class ProfileYamlGraphTests(SanitizationCase):
    def test_anchor_and_block_profile_scalars_remain_valid_yaml(self):
        sources = (f'source_profile: &src {self.public_profile}\ncopy: *src\n',
                   f'source_profile: |\n  {self.public_profile}\n')
        for source in sources:
            with self.subTest(source=source):
                projected = self.sanitize(source, 'plugin.yaml')
                data = yaml.safe_load(projected)
                self.assertIn('<public-plugin-source-profile>', data['source_profile'])

    def test_cyclic_profile_value_fails_closed_without_recursion(self):
        source = 'node: &n {source: *n}\n'
        projected = self.sanitize(source, 'plugin.yaml')
        self.assertIn('<ambiguous-private-profile>', projected)
        self.assertTrue(any('ambiguous private profile' in error
                            for error in self.staged_errors(projected)))


class WorkflowNameTests(SanitizationCase):
    def test_public_workflow_and_lifecycle_names_survive_exactly(self):
        source = ('Use kanban-workflow-guide with task_lifecycle and '
                  'kanban-workflow-orchestrator.\n')
        self.assertEqual(self.sanitize(source, 'README.md'), source)


class ExecutablePathTests(SanitizationCase):
    def test_private_interpreter_path_is_rejected_after_projection(self):
        executable = (Path('/') / 'home' / 'example-user' / '.hermes' /
                      'hermes-agent' / 'venv' / 'bin' / 'python')
        projected = self.sanitize(f'Run {executable} task.py\n', 'README.md')
        errors = self.staged_errors(projected)
        self.assertTrue(any('executable path' in error for error in errors), errors)

    def test_braced_home_executable_path_is_rejected(self):
        errors = self.staged_errors('Run ${HERMES_HOME}/venv/bin/python task.py\n')
        self.assertTrue(any('executable path' in error for error in errors), errors)

    def test_case_variant_placeholder_executable_path_is_rejected(self):
        errors = self.staged_errors('Run <PRIVATE-TERM>/venv/bin/python task.py\n')
        self.assertTrue(any('executable path' in error for error in errors), errors)

    def test_quoted_executable_path_is_rejected(self):
        errors = self.staged_errors('Run <private-term>/"venv folder"/bin/python\n')
        self.assertTrue(any('executable path' in error for error in errors), errors)


class MarkupGrammarTests(SanitizationCase):
    def test_html_remains_usable(self):
        markup = ('<a href="https://example.com">docs</a>\n'
                  '<img src="asset.png">\n<details open>text</details>\n')
        self.assertEqual(self.staged_errors(markup), [])


class PlaceholderGrammarTests(SanitizationCase):
    def test_nested_placeholder_is_rejected(self):
        errors = self.staged_errors('author: <<private-term>>\n')
        self.assertTrue(any('malformed placeholder' in error for error in errors), errors)

    def test_asymmetric_and_case_variant_placeholders_are_rejected(self):
        malformed = ('<<private-term>', '<private-term>>',
                     '<<PRIVATE-TERM>>', '<private-term:')
        for text in malformed:
            with self.subTest(text=text):
                errors = self.staged_errors(f'author: {text}\n')
                self.assertTrue(any('malformed placeholder' in error for error in errors))

    def test_punctuated_unclosed_placeholders_are_rejected(self):
        for text in ('<private-term?', '<private-term!', '<private-term)'):
            with self.subTest(text=text):
                errors = self.staged_errors(f'author: {text}\n')
                self.assertTrue(any('malformed placeholder' in error for error in errors))

    def test_unclosed_and_empty_placeholders_are_rejected(self):
        for text in ('author: <private-term\n', 'author: <>\n'):
            with self.subTest(text=text):
                errors = self.staged_errors(text)
                self.assertTrue(any('malformed placeholder' in error for error in errors))


class PlaceholderAcceptanceTests(SanitizationCase):
    def test_comparisons_and_cpp_templates_remain_usable(self):
        text = 'Require a < b < c and std::vector<std::vector<int>>.\n'
        self.assertEqual(self.staged_errors(text), [])

    def test_author_placeholders_remain_usable(self):
        text = ('git config user.name "<repo-author-name>"\n'
                'git config user.email "<repo-author-email>"\n')
        self.assertEqual(self.staged_errors(text), [])


if __name__ == '__main__':
    unittest.main()
