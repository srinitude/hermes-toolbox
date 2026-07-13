#!/usr/bin/env python3
"""Deterministic text sanitization rules for exported public packages."""
from __future__ import annotations

import os
import re
from pathlib import Path

from markup_policy import cxx_missing_open_context, markup_candidate
from profile_field_policy import (
    AMBIGUOUS_PROFILE, replace_profile_identifiers,
)
from shell_path_policy import placeholder_executable_path
from text_sanitizer import sanitize_line
from toolbox_common import git_info_dir, read_terms


def local_private_terms(repo: Path) -> list[str]:
    terms = list(read_terms(git_info_dir(repo) / 'identity-denylist.txt'))
    env = os.environ.get('HERMES_TOOLBOX_DENY_TERMS', '')
    if env:
        terms.extend(part.strip() for part in env.split(',') if part.strip())
    return sorted(set(terms), key=len, reverse=True)


def _author_terms(author_name: str) -> list[tuple[str, str]]:
    first = author_name.split()[0]
    return [
        (f"{first}'s VPS", 'the local Hermes environment'),
        (f"{first}'s public repos", "the repository owner's public repos"),
        (f"{first}'s repos", "the repository owner's repos"),
        (f"{first}'s", "the repository owner's"),
        (f'{first}-authored', 'repository-author-authored'),
        (f'{first}-specific/private/user-specific', 'user-specific/private'),
        (f'{first}-specific/private', 'user-specific/private'),
        (f'{first}-specific', 'user-specific'),
        (f'non-{first}-specific', 'reusable/public'),
        (f'Non-{first}-specific', 'Reusable/public'),
        (f'non-{first}', 'public'),
        (f'Non-{first}', 'Public'),
        (f'{first} as a person', 'the repository owner as a person'),
    ]


def replacement_terms(repo: Path, author_name: str | None,
                      private_prefix: str | None) -> list[tuple[str, str]]:
    terms: list[tuple[str, str]] = []
    if author_name:
        terms.extend(_author_terms(author_name))
    if private_prefix:
        terms.append((f'`{private_prefix}`', '`<first-name>-`'))
        terms.append((private_prefix, '<first-name>-'))
    terms.extend([
        ('on ' + 'this ' + 'VPS', 'for this Hermes environment'),
        ('For ' + 'this ' + 'VPS', 'For this Hermes environment'),
        ('this ' + 'VPS', 'this Hermes environment'),
    ])
    terms.extend((term, '<private-term>') for term in local_private_terms(repo))
    return terms


SANITIZER_PLACEHOLDERS = (
    'first-name', 'private-term', 'public-plugin-source-profile',
    'repo-author-email', 'repo-author-name',
)
EXECUTABLE_PLACEHOLDERS = SANITIZER_PLACEHOLDERS + (
    'command', 'home', 'name', 'path', 'plugin', 'profile', 'repo', 'skill', 'user',
)
EXECUTABLE_NAMES = '|'.join(
    re.escape(name) for name in sorted(EXECUTABLE_PLACEHOLDERS, key=len, reverse=True)
)
PLACEHOLDER_CANDIDATE_RE = re.compile(
    rf'<+(?P<name>{EXECUTABLE_NAMES})(?![A-Za-z0-9_-])', re.IGNORECASE,
)
MISSING_OPEN_RE = re.compile(
    rf'(?m)^\s*(?:author\s*:\s*)?(?P<quote>["\']?)\[?'
    rf'(?:{EXECUTABLE_NAMES})>{{1,2}}(?P=quote)\s*(?:#.*)?$',
    re.IGNORECASE,
)
INLINE_MISSING_OPEN_RE = re.compile(
    rf'(?<![A-Za-z0-9</-])(?:{EXECUTABLE_NAMES})>{{1,2}}'
    r'(?=[\s/.!?,;:\]\)#*`~<_}]|$)', re.IGNORECASE,
)
EMPTY_AUTHOR_PLACEHOLDER_RE = re.compile(
    r'(?m)^\s*author:\s*(?P<quote>["\']?)<>(?P=quote)\s*$'
)
AUTHOR_MALFORMED_RE = re.compile(
    rf'(?im)^\s*author\s*:.*(?:<>|(?<!<)(?:{EXECUTABLE_NAMES})>{{1,2}}).*$',
)
SAFE_AUTHOR_LINE_RE = re.compile(
    r'(?im)^\s*author\s*:\s*(?:<name>|<repo-author-name>)\s*(?:#.*)?$'
)
def _inline_missing_open(text: str) -> bool:
    for match in INLINE_MISSING_OPEN_RE.finditer(text):
        prefix = text[text.rfind('\n', 0, match.start()) + 1:match.start()]
        if not cxx_missing_open_context(prefix):
            return True
    return False


def _malformed_placeholder(text: str) -> bool:
    author_view = SAFE_AUTHOR_LINE_RE.sub('', text)
    if (EMPTY_AUTHOR_PLACEHOLDER_RE.search(text) or MISSING_OPEN_RE.search(text)
            or _inline_missing_open(text) or AUTHOR_MALFORMED_RE.search(author_view)):
        return True
    canonical = {name.casefold(): name for name in EXECUTABLE_PLACEHOLDERS}
    for match in PLACEHOLDER_CANDIDATE_RE.finditer(text):
        if markup_candidate(text, match):
            continue
        expected = f'<{canonical[match.group("name").casefold()]}>'
        actual = text[match.start():match.start() + len(expected)]
        if actual != expected:
            return True
        if text[match.start() + len(expected):].startswith('>'):
            return True
    return False


def semantic_text_errors(text: str) -> list[str]:
    errors = []
    if _malformed_placeholder(text):
        errors.append('malformed placeholder survived sanitization')
    if AMBIGUOUS_PROFILE in text:
        errors.append('ambiguous private profile identifier survived sanitization')
    if placeholder_executable_path(text, EXECUTABLE_PLACEHOLDERS):
        errors.append('placeholder-bearing executable path survived sanitization')
    return errors


def sanitize_public_text(text: str, rel: Path, repo: Path, author_name: str | None,
                         private_prefix: str | None, public_plugin_profile: str | None) -> str:
    terms = replacement_terms(repo, author_name, private_prefix)
    text = replace_profile_identifiers(text, rel, public_plugin_profile)
    out_lines: list[str] = []
    for line in text.splitlines():
        # Approved authorship metadata remains only in the SKILL.md frontmatter author line.
        if rel.name == 'SKILL.md' and author_name and line.strip() == f'author: {author_name}':
            out_lines.append(line)
            continue
        out_lines.append(sanitize_line(line, terms))
    return '\n'.join(out_lines) + ('\n' if text.endswith('\n') else '')
