#!/usr/bin/env python3
"""Deterministic text sanitization rules for exported public packages."""
from __future__ import annotations

import os
from pathlib import Path

from toolbox_common import (
    API_KEY_CONFIG_RE, EMAIL_RE, HERMES_HOME_RE, USER_HOME_RE,
    git_info_dir, read_terms,
)


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
        (author_name, '<repo-author-name>'),
    ]


def replacement_terms(repo: Path, author_name: str | None, private_prefix: str | None,
                      public_plugin_profile: str | None) -> list[tuple[str, str]]:
    terms: list[tuple[str, str]] = []
    if author_name:
        terms.extend(_author_terms(author_name))
    if private_prefix:
        terms.append((f'`{private_prefix}`', '`<first-name>-`'))
        terms.append((private_prefix, '<first-name>-'))
    if public_plugin_profile:
        terms.append((f'`{public_plugin_profile}`', '`<public-plugin-source-profile>`'))
        terms.append((public_plugin_profile, '<public-plugin-source-profile>'))
    terms.extend([
        ('on ' + 'this ' + 'VPS', 'for this Hermes environment'),
        ('For ' + 'this ' + 'VPS', 'For this Hermes environment'),
        ('this ' + 'VPS', 'this Hermes environment'),
    ])
    terms.extend((term, '<private-term>') for term in local_private_terms(repo))
    return terms


def _sanitize_line(line: str, terms: list[tuple[str, str]]) -> str:
    new = line
    for old, repl in terms:
        new = new.replace(old, repl)
    new = HERMES_HOME_RE.sub('$HERMES_HOME', new)
    new = USER_HOME_RE.sub('$HOME', new)
    new = EMAIL_RE.sub('<repo-author-email>', new)
    new = API_KEY_CONFIG_RE.sub(
        lambda m: f'# Configure {m.group(1)} through the official setup/auth/env flow, not as a non-secret config key',
        new,
    )
    new = new.replace('$HERMES_HOME/hermes-agent/venv/bin/python', '${HERMES_AGENT_PYTHON:-python3}')
    return new.replace('$HOME/.hermes/plugins', '$HERMES_HOME/plugins')


def sanitize_public_text(text: str, rel: Path, repo: Path, author_name: str | None,
                         private_prefix: str | None, public_plugin_profile: str | None) -> str:
    terms = replacement_terms(repo, author_name, private_prefix, public_plugin_profile)
    out_lines: list[str] = []
    for line in text.splitlines():
        # Approved authorship metadata remains only in the SKILL.md frontmatter author line.
        if rel.name == 'SKILL.md' and author_name and line.strip() == f'author: {author_name}':
            out_lines.append(line)
            continue
        out_lines.append(_sanitize_line(line, terms))
    return '\n'.join(out_lines) + ('\n' if text.endswith('\n') else '')
