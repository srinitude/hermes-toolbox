"""Canonical public author-placeholder compatibility."""
from __future__ import annotations

import re

from tests.test_export_transaction import SKILL_REL, TransactionCase


class AuthorPlaceholderExportTests(TransactionCase):
    def test_safe_author_placeholder_is_reusable_in_instructions(self):
        placeholder = '<repo-author-name>'
        skill = self.home / 'skills' / SKILL_REL / 'SKILL.md'
        source = skill.read_text(encoding='utf-8')
        source = re.sub(r'(?m)^author: .+$', f'author: {placeholder}', source, count=1)
        instruction = f'\ngit config user.name "{placeholder}"\n'
        skill.write_text(source + instruction, encoding='utf-8')
        result = self.export()
        self.assertEqual(result.returncode, 0, result.stderr)
