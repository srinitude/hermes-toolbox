"""Public documentation must match inventory/public-manifest.json exactly."""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from tests.support import REPO

NAME_RE = re.compile(r'[a-z0-9][a-z0-9/_-]*')
SELECT_RE = re.compile(r'--(skill|plugin|profile)\s+(\S+)')
ENABLE_RE = re.compile(r'hermes plugins enable\s+(\S+)')
PROFILE_INSTALL_RE = re.compile(r'hermes profile install\s+profiles/(\S+)')
TOP_DOCS = ('README.md', 'CONTRIBUTING.md', 'plugins/README.md',
            'profiles/README.md', 'primitives/README.md')


def entry_names(data: dict, kind: str) -> set[str]:
    names = set()
    for entry in data.get(kind, []):
        parts = Path(entry['path']).parts
        names.add('/'.join(parts[1:3]) if kind == 'skills' else parts[1])
    return names


def doc_files() -> list[Path]:
    files = [REPO / name for name in TOP_DOCS]
    files += sorted((REPO / 'docs').glob('*.md'))
    files += sorted((REPO / 'examples').glob('*.md'))
    return files


def concrete_name(token: str) -> str | None:
    match = NAME_RE.fullmatch(token.strip('`"\'.,:)('))
    return match.group(0) if match else None


class DocsContractCase(unittest.TestCase):
    def setUp(self):
        manifest = REPO / 'inventory' / 'public-manifest.json'
        self.data = json.loads(manifest.read_text(encoding='utf-8'))
        self.docs = {path.relative_to(REPO).as_posix(): path.read_text(encoding='utf-8')
                     for path in doc_files()}


class ManifestNameTests(DocsContractCase):
    def test_readme_lists_every_manifest_skill(self):
        readme = self.docs['README.md']
        for name in sorted(entry_names(self.data, 'skills')):
            self.assertIn(name, readme, f'README.md does not list manifest skill {name}')

    def test_documented_selections_exist_in_manifest(self):
        listed = {'skill': entry_names(self.data, 'skills'),
                  'plugin': entry_names(self.data, 'plugins'),
                  'profile': entry_names(self.data, 'profiles')}
        for rel, text in self.docs.items():
            for kind, token in SELECT_RE.findall(text):
                name = concrete_name(token)
                if name is not None:
                    self.assertIn(name, listed[kind],
                                  f'{rel}: --{kind} {name} is not in the public manifest')

    def test_enable_and_install_targets_exist_in_manifest(self):
        plugins = entry_names(self.data, 'plugins')
        profiles = entry_names(self.data, 'profiles')
        for rel, text in self.docs.items():
            for token in ENABLE_RE.findall(text):
                name = concrete_name(token)
                if name is not None:
                    self.assertIn(name, plugins, f'{rel}: enables unlisted plugin {name}')
            for token in PROFILE_INSTALL_RE.findall(text):
                name = concrete_name(token)
                if name is not None:
                    self.assertIn(name, profiles, f'{rel}: installs unlisted profile {name}')


class ManifestCountTests(DocsContractCase):
    def expected_lines(self) -> list[str]:
        return [f'- Skills: {len(self.data["skills"])}',
                f'- Plugin packages: {len(self.data["plugins"])}',
                f'- Profile packages: {len(self.data["profiles"])}',
                f'- Personality presets: {len(self.data["personalities"])}']

    def test_readme_states_manifest_counts(self):
        for line in self.expected_lines():
            self.assertIn(line, self.docs['README.md'], f'README.md missing count line {line!r}')

    def test_customization_inventory_states_manifest_counts(self):
        text = self.docs['docs/customization-inventory.md']
        for line in self.expected_lines():
            self.assertIn(line, text, f'customization-inventory.md missing {line!r}')

    def test_docs_never_instruct_enabling_plugins_with_empty_inventory(self):
        for rel, text in self.docs.items():
            if not entry_names(self.data, 'plugins'):
                self.assertNotIn('hermes plugins enable', text,
                                 f'{rel}: plugin enablement documented with an empty inventory')


class InstallerFlagTests(DocsContractCase):
    def test_no_broad_plugins_flag_anywhere(self):
        for rel, text in self.docs.items():
            self.assertIsNone(re.search(r'--plugins\b', text),
                              f'{rel}: broad --plugins flag is not an installer flag')

    def test_no_enable_all_plugin_loop(self):
        for rel, text in self.docs.items():
            self.assertNotIn('for plugin_path in', text, f'{rel}: enable-all loop documented')

    def test_install_docs_document_explicit_skill_selection(self):
        for rel in ('README.md', 'docs/install.md'):
            self.assertIn('--skill', self.docs[rel], f'{rel}: missing --skill documentation')
            self.assertIn('--all-skills', self.docs[rel], f'{rel}: missing --all-skills')

    def test_install_docs_separate_personality_install_from_activation(self):
        for rel in ('README.md', 'docs/install.md'):
            self.assertIn('--personalities', self.docs[rel], f'{rel}: missing --personalities')
            self.assertIn('--activate-validator', self.docs[rel],
                          f'{rel}: missing --activate-validator')


if __name__ == '__main__':
    unittest.main()
