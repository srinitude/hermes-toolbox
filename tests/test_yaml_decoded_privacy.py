"""Decoded YAML privacy boundaries at real export transactions."""
from __future__ import annotations

import re

import yaml

from tests.test_export_transaction import TransactionCase


class YamlDecodedPrivacyTests(TransactionCase):
    def test_encoded_deny_term_is_rejected(self):
        term = 'Private' + 'Name'
        info = self.repo / '.git' / 'info'
        info.mkdir(parents=True, exist_ok=True)
        (info / 'identity-denylist.txt').write_text(term + '\n')
        encoded = '\\u0050' + 'rivateName'
        (self.source / 'identity.yaml').write_text(f'description: "{encoded}"\n')
        self.assert_last_known_good_preserved(self.export())

    def test_encoded_author_identity_in_yaml_prose_is_rejected(self):
        skill = self.home / 'skills/fixtures/complete-skill/SKILL.md'
        source = re.sub(r'(?m)^author: .+$', r'author: "Jane \\u0046ixture"',
                        skill.read_text(), count=1)
        skill.write_text(source)
        encoded = 'Jane \\u0046ixture'
        (self.source / 'identity.yaml').write_text(f'description: "{encoded}"\n')
        self.assert_last_known_good_preserved(self.export())

    def test_binary_encoded_deny_term_is_rejected(self):
        term = 'Private' + 'Name'
        info = self.repo / '.git' / 'info'
        info.mkdir(parents=True, exist_ok=True)
        (info / 'identity-denylist.txt').write_text(term + '\n')
        for encoded in ('UHJpdmF0ZU5hbWU=', 'UHJp!dmF0ZU5hbWU='):
            with self.subTest(encoded=encoded):
                text = f'description: !!binary "{encoded}"\n'
                (self.source / 'identity.yaml').write_text(text)
                self.assert_last_known_good_preserved(self.export())


class YamlSyntaxTests(TransactionCase):
    def test_invalid_auxiliary_yaml_preserves_last_known_good(self):
        (self.source / 'config.yaml').write_text('service: [broken\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('invalid YAML', result.stderr)

    def test_non_decodable_typed_yaml_is_rejected(self):
        (self.source / 'typed.yaml').write_text('count: !!int nope\n')
        result = self.export()
        self.assert_last_known_good_preserved(result)
        self.assertIn('invalid YAML', result.stderr)


class SkillFrontmatterSyntaxTests(TransactionCase):
    def test_invalid_skill_frontmatter_yaml_is_rejected(self):
        skill = self.home / 'skills/fixtures/complete-skill/SKILL.md'
        source = skill.read_text()
        source = source.replace('\n---\n', '\ntags: [broken\n---\n', 1)
        skill.write_text(source)
        self.assert_last_known_good_preserved(self.export())

    def test_non_scalar_required_frontmatter_is_rejected(self):
        skill = self.home / 'skills/fixtures/complete-skill/SKILL.md'
        source = skill.read_text().replace('name: complete-skill',
                                           'name: [complete-skill]', 1)
        skill.write_text(source)
        self.assert_last_known_good_preserved(self.export())


class YamlFlowPrivacyTests(TransactionCase):
    def test_flow_author_line_does_not_exempt_encoded_description(self):
        manifest = self.source / 'plugin.yaml'
        data = yaml.safe_load(manifest.read_text())
        term = 'Private' + 'Name'
        data.update(author='Jane Fixture', description=term)
        encoded = '\\u0050' + 'rivateName'
        text = yaml.safe_dump(data, default_flow_style=True)
        text = text.replace(f'description: {term}', f'description: "{encoded}"')
        manifest.write_text(text)
        info = self.repo / '.git' / 'info'
        info.mkdir(parents=True, exist_ok=True)
        (info / 'identity-denylist.txt').write_text(term + '\n')
        self.assert_last_known_good_preserved(self.export())


class YamlAliasPrivacyTests(TransactionCase):
    def test_author_alias_reuse_outside_metadata_is_rejected(self):
        manifest = self.source / 'plugin.yaml'
        text = re.sub(r'(?m)^name:', 'author: &who Jane Fixture\nidentity: *who\nname:',
                      manifest.read_text(), count=1)
        manifest.write_text(text)
        self.assert_last_known_good_preserved(self.export())
