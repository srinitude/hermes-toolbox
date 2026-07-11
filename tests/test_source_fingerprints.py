"""Source fingerprints: tracked files plus manifest-listed package roots only."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.support import FIXTURES, add_scripts_path

add_scripts_path()
from public_manifest import write_inventory  # noqa: E402

SKILL_DEST = 'skills/fixtures/complete-skill'


def fingerprints(repo: Path) -> dict[str, str]:
    write_inventory(repo)
    raw = (repo / 'inventory' / 'source-fingerprints.json').read_text(encoding='utf-8')
    return json.loads(raw)


def seed_repo(base: Path, git: bool) -> Path:
    repo = base / 'repo'
    (repo / 'inventory').mkdir(parents=True)
    shutil.copytree(FIXTURES / 'complete-skill', repo / SKILL_DEST)
    (repo / 'README.md').write_text('# Public toolbox fixture\n', encoding='utf-8')
    (repo / 'scratch.txt').write_text('unrelated untracked note\n', encoding='utf-8')
    (repo / '.serena').mkdir()
    (repo / '.serena' / 'project.yml').write_text('language: python\n', encoding='utf-8')
    if git:
        subprocess.run(['git', 'init', '-q'], cwd=repo, check=True)
        subprocess.run(['git', 'add', '--', 'README.md'], cwd=repo, check=True)
    return repo


class FingerprintCase(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='toolbox-fp-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = seed_repo(self.base, git=True)
        self.prints = fingerprints(self.repo)


class ExclusionTests(FingerprintCase):
    def test_unrelated_untracked_root_file_is_excluded(self):
        self.assertNotIn('scratch.txt', self.prints)

    def test_serena_project_cache_is_excluded(self):
        self.assertEqual([key for key in self.prints if key.startswith('.serena/')], [])

    def test_fingerprints_exclude_themselves_even_when_tracked(self):
        subprocess.run(['git', 'add', '--', 'inventory', 'skills'], cwd=self.repo, check=True)
        current = fingerprints(self.repo)
        self.assertNotIn('inventory/source-fingerprints.json', current)
        self.assertIn('inventory/public-manifest.json', current)


class InclusionTests(FingerprintCase):
    def test_tracked_file_remains_included(self):
        self.assertIn('README.md', self.prints)

    def test_new_untracked_file_inside_listed_package_is_included(self):
        extra = self.repo / SKILL_DEST / 'references' / 'notes.md'
        extra.parent.mkdir()
        extra.write_text('Newly exported reference material.\n', encoding='utf-8')
        current = fingerprints(self.repo)
        self.assertIn(f'{SKILL_DEST}/references/notes.md', current)
        self.assertIn(f'{SKILL_DEST}/SKILL.md', current)

    def test_hashes_are_exact_sha256_of_file_bytes(self):
        digest = hashlib.sha256((self.repo / SKILL_DEST / 'SKILL.md').read_bytes()).hexdigest()
        self.assertEqual(self.prints[f'{SKILL_DEST}/SKILL.md'], digest)


class WalkFallbackTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='toolbox-fp-nogit-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = seed_repo(self.base, git=False)
        self.prints = fingerprints(self.repo)

    def test_non_git_repo_uses_safe_walk_and_skips_private_paths(self):
        self.assertIn(f'{SKILL_DEST}/SKILL.md', self.prints)
        self.assertIn('README.md', self.prints)
        self.assertEqual([key for key in self.prints if key.startswith('.serena/')], [])
        self.assertNotIn('inventory/source-fingerprints.json', self.prints)


if __name__ == '__main__':
    unittest.main()
