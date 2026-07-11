"""Skill package export contracts: support files, containment, authorship."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tests.support import FIXTURES, make_home, make_repo, run_exporter

SKILL_REL = 'fixtures/complete-skill'
SUPPORT_SECTION = (
    '\n## Support Material\n\n'
    'Load `references/usage-pattern.md` for the recorded usage pattern and\n'
    '`templates/report-template.md` when drafting the final report. Ship only\n'
    'SKILL.md plus references/templates/scripts/assets support directories,\n'
    'and keep new notes under `references/` until they are reviewed.\n'
)


class SkillExportCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='skill-export-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = make_repo(self.base)
        self.home = make_home(self.base)
        self.source = self.home / 'skills' / SKILL_REL
        shutil.copytree(FIXTURES / 'complete-skill', self.source)
        self.dest = self.repo / 'skills' / SKILL_REL
        self.add_source_file('SKILL.md', self.read_source('SKILL.md') + SUPPORT_SECTION)
        self.add_source_file('references/usage-pattern.md', '# Usage pattern\n')
        self.add_source_file('templates/report-template.md', '# Report template\n')
        self.add_source_file('notes/private-notes.md', 'unreviewed local notes\n')
        self.add_source_file('.hidden.md', 'hidden working file\n')

    def read_source(self, rel: str) -> str:
        return (self.source / rel).read_text(encoding='utf-8')

    def add_source_file(self, rel: str, text: str) -> None:
        path = self.source / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def export(self):
        return run_exporter(self.repo, self.home, '--public-skill', SKILL_REL)


class SkillSupportFileTests(SkillExportCase):
    def test_allowed_support_directories_are_copied(self):
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.dest / 'references' / 'usage-pattern.md').is_file())
        self.assertTrue((self.dest / 'templates' / 'report-template.md').is_file())

    def test_unlisted_source_files_are_excluded(self):
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.dest / 'notes').exists())
        self.assertFalse((self.dest / '.hidden.md').exists())

    def test_author_frontmatter_is_preserved(self):
        author_line = next(line for line in self.read_source('SKILL.md').splitlines()
                           if line.startswith('author: '))
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(author_line,
                      (self.dest / 'SKILL.md').read_text(encoding='utf-8'))

    def test_manifest_hash_tracks_exported_skill(self):
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads((self.repo / 'inventory' / 'public-manifest.json')
                              .read_text(encoding='utf-8'))
        entries = {e['path']: e['sha256'] for e in manifest['skills']}
        import hashlib
        expected = hashlib.sha256((self.dest / 'SKILL.md').read_bytes()).hexdigest()
        self.assertEqual(entries.get(f'skills/{SKILL_REL}/SKILL.md'), expected)


class SkillRejectionTests(SkillExportCase):
    def assert_rejected(self, result) -> None:
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.dest.exists())

    def test_missing_license_frontmatter_is_rejected(self):
        text = self.read_source('SKILL.md').replace('license: MIT\n', '')
        self.add_source_file('SKILL.md', text)
        self.assert_rejected(self.export())

    def test_dangling_reference_is_rejected(self):
        self.add_source_file('SKILL.md', self.read_source('SKILL.md')
                             + '\nAlso load `references/missing-notes.md` first.\n')
        self.assert_rejected(self.export())

    def test_directory_prose_mentions_are_not_treated_as_references(self):
        # SUPPORT_SECTION already names bare `references/` and the slash-joined
        # references/templates/scripts/assets enumeration; both must be ignored.
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
