"""Skill body structured data is validated before package replacement."""
from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from tests.support import FIXTURES, add_scripts_path, make_repo, tree_bytes

add_scripts_path()
from export_transaction import export_one_skill  # noqa: E402


class SkillForbiddenPathTests(unittest.TestCase):
    def test_nested_cache_is_not_published(self):
        base = Path(tempfile.mkdtemp(prefix='skill-path-safety-'))
        self.addCleanup(shutil.rmtree, base, True)
        repo = make_repo(base)
        source_skills = base / 'skills'
        rel = Path('hermes-agent/hermes-config-audits')
        source = source_skills / rel
        shutil.copytree(FIXTURES / 'complete-skill', source)
        self.assertTrue(export_one_skill(source_skills, repo, rel, None, None))
        cache = source / 'scripts/.pytest_cache/v/nodeids'
        cache.parent.mkdir(parents=True)
        cache.write_text('private-cache-entry\n')
        self.assertFalse(export_one_skill(source_skills, repo, rel, None, None))
        self.assertFalse((repo / 'skills' / rel / 'scripts/.pytest_cache').exists())


class SkillBodySafetyTests(unittest.TestCase):
    def setUp(self):
        self.base = Path(tempfile.mkdtemp(prefix='skill-body-safety-'))
        self.addCleanup(shutil.rmtree, self.base, True)
        self.repo = make_repo(self.base)
        self.source_skills = self.base / 'skills'
        self.rel = Path('hermes-agent/hermes-config-audits')
        shutil.copytree(FIXTURES / 'complete-skill', self.source_skills / self.rel)
        self.assertTrue(export_one_skill(self.source_skills, self.repo, self.rel, None, None))
        self.destination = self.repo / 'skills' / self.rel
        self.baseline = tree_bytes(self.destination)

    def test_escaped_fenced_author_and_credential_are_rejected(self):
        field = 'au' + '\\u0074hor'
        key = 'api' + '\\u005fkey'
        payloads = (
            f'```yaml\n"{field}": Jane Private\n```\nRun Jane Private.\n',
            f'```json\n{{"{key}":"abcdef0123456789abcdef"}}\n```\n',
        )
        skill = self.source_skills / self.rel / 'SKILL.md'
        original = skill.read_text()
        for payload in payloads:
            with self.subTest(payload=payload[:7]):
                skill.write_text(original + '\n' + payload)
                with self.assertRaises(SystemExit):
                    export_one_skill(self.source_skills, self.repo, self.rel, None, None)
                self.assertEqual(tree_bytes(self.destination), self.baseline)
