"""YAML-aware author metadata boundaries across public package types."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from tests.test_export_transaction import TransactionCase


class SkillYamlCase(TransactionCase):
    def skill(self) -> Path:
        return self.home / 'skills/fixtures/complete-skill/SKILL.md'

    def source_with_author(self, author_line: str, body: str = '') -> str:
        source = self.skill().read_text()
        source = re.sub(r'(?m)^author\s*:.*$', author_line, source, count=1)
        return source + body


class SkillYamlAuthorTests(SkillYamlCase):
    def test_yaml_scalar_variants_protect_author_identity(self):
        baseline = self.skill().read_text()
        variants = ('author : Jane Fixture', 'author: &who Jane Fixture',
                    'author: !!str Jane Fixture')
        for author_line in variants:
            with self.subTest(author_line=author_line):
                source = re.sub(r'(?m)^author\s*:.*$', author_line, baseline, count=1)
                self.skill().write_text(source + '\nRun Jane Fixture.\n')
                result = self.export()
                self.assert_last_known_good_preserved(result)
                self.assertIn('approved author identity', result.stderr)

    def test_non_scalar_author_is_rejected(self):
        self.skill().write_text(self.source_with_author('author: [Jane, Fixture]'))
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('complex author metadata', result.stderr)


class MalformedAuthorYamlTests(SkillYamlCase):
    def test_decorated_malformed_author_placeholders_are_rejected(self):
        variants = ('author: "private-term>>" # damaged',
                    'author: &who private-term>',
                    'author: !!str private-term>',
                    'author: "<>" # damaged')
        for author_line in variants:
            with self.subTest(author_line=author_line):
                self.skill().write_text(self.source_with_author(author_line))
                result = self.export()
                self.assert_last_known_good_preserved(result)
                self.assertIn('malformed placeholder', result.stderr)


class FrontmatterCompatibilityTests(SkillYamlCase):
    def test_frontmatter_closing_delimiter_whitespace_is_valid(self):
        source = self.source_with_author('author: Hermes Agent', '\nRun Hermes Agent.\n')
        source = source.replace('\n---\n', '\n---   \n', 1)
        self.skill().write_text(source)
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)


class PluginContinuationAuthorTests(TransactionCase):
    def test_continuation_scalar_locations_protect_identity(self):
        manifest = self.source / 'plugin.yaml'
        readme = self.source / 'README.md'
        manifest_base, readme_base = manifest.read_text(), readme.read_text()
        variants = ('author:\n  Jane Fixture', 'author: &who\n  Jane Fixture',
                    'author: !!str\n  Jane Fixture')
        for author_field in variants:
            with self.subTest(author_field=author_field):
                manifest.write_text(manifest_base + '\n' + author_field + '\n')
                readme.write_text(readme_base + '\nRun Jane Fixture.\n')
                result = self.export()
                self.assert_last_known_good_preserved(result)
                self.assertIn('approved author identity', result.stderr)


class YamlAliasTests(TransactionCase):
    def test_author_alias_to_non_author_field_is_rejected(self):
        manifest = self.source / 'plugin.yaml'
        manifest.write_text(manifest.read_text() +
                            '\nidentity: &who Jane Fixture\nauthor: *who\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('complex author metadata', result.stderr)

    def test_non_author_merge_is_valid(self):
        manifest = self.source / 'plugin.yaml'
        manifest.write_text(manifest.read_text() +
                            '\ndefaults: &d {license: MIT}\n<<: *d\n')
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)


    def test_duplicate_non_author_alias_merge_is_valid(self):
        manifest = self.source / 'plugin.yaml'
        manifest.write_text(manifest.read_text() +
                            '\ndefaults: &d {license: MIT}\n<<: [*d, *d]\n')
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)


class NestedAuthorTests(TransactionCase):
    def test_nested_flow_author_is_rejected(self):
        manifest = self.source / 'plugin.yaml'
        field = 'au' + 'thor'
        manifest.write_text(manifest.read_text() +
                            f'\nnotes: {{"{field}": Jane Fixture}}\n')
        (self.source / 'README.md').write_text('Run Jane Fixture.\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('complex author metadata', result.stderr)

    def test_noncanonical_author_key_casing_is_rejected(self):
        manifest = self.source / 'plugin.yaml'
        manifest.write_text(manifest.read_text() + '\nAuthor: Jane Fixture\n')
        (self.source / 'README.md').write_text('Run Jane Fixture.\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('complex author metadata', result.stderr)

    def test_whitespace_normalized_identity_is_rejected(self):
        manifest = self.source / 'plugin.yaml'
        manifest.write_text(manifest.read_text() + '\nauthor: Li Wei\n')
        (self.source / 'README.md').write_text('Run LI   WEI.\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('approved author identity', result.stderr)


class YamlMergeSequenceTests(TransactionCase):
    def test_author_bearing_merge_sequence_is_rejected(self):
        manifest = self.source / 'plugin.yaml'
        field = 'au' + 'thor'
        manifest.write_text(manifest.read_text() +
                            '\ndefaults: &d {license: MIT}\n'
                            f'private: &p {{{field}: Jane Fixture}}\n<<: [*d, *p]\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('complex author metadata', result.stderr)

    def test_cyclic_merge_is_rejected_without_recursion_error(self):
        manifest = self.source / 'plugin.yaml'
        manifest.write_text(manifest.read_text() + '\ndefaults: &d {<<: *d}\n<<: *d\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('complex author metadata', result.stderr)
        self.assertNotIn('RecursionError', result.stderr)


class PluginYamlAuthorTests(TransactionCase):
    def test_spaced_top_level_author_key_protects_identity(self):
        manifest = self.source / 'plugin.yaml'
        manifest.write_text(manifest.read_text() + '\nauthor : Jane Fixture\n')
        readme = self.source / 'README.md'
        readme.write_text(readme.read_text() + '\nRun Jane Fixture.\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('approved author identity', result.stderr)

    def test_top_level_yaml_merge_is_rejected(self):
        manifest = self.source / 'plugin.yaml'
        field = 'au' + 'thor'
        manifest.write_text(manifest.read_text() +
                            f'\ndefaults: &d {{{field}: Jane Fixture}}\n<<: *d\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('complex author metadata', result.stderr)

    def test_author_comment_private_term_is_sanitized(self):
        info = self.repo / '.git' / 'info'
        info.mkdir(parents=True, exist_ok=True)
        (info / 'identity-denylist.txt').write_text('Ann\n')
        manifest = self.source / 'plugin.yaml'
        manifest.write_text(manifest.read_text() + '\nauthor: Hermes Agent # ann\n')
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        output = (self.plugin_dest / 'plugin.yaml').read_text()
        self.assertIn('author: Hermes Agent # <private-term>', output)


if __name__ == '__main__':
    unittest.main()
