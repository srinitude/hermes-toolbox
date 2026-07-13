"""Shared line-level identity and private-path safety policy."""
from __future__ import annotations

from author_policy import contains_term
from toolbox_common import EMAIL_RE, USER_HOME_RE


def line_violation(line: str, terms: list[str], author_terms: list[str],
                   identity_line: str | None = None) -> str | None:
    if EMAIL_RE.search(line):
        return 'non-example email address detected'
    if USER_HOME_RE.search(line):
        return 'user-specific absolute home path detected; use $HOME, $HERMES_HOME, or placeholders'
    searchable = line if identity_line is None else identity_line
    for term in terms:
        if term and contains_term(searchable, term):
            return 'denied private/identity term detected'
    for term in author_terms:
        if term and contains_term(searchable, term):
            return 'approved author identity appears outside allowed frontmatter'
    return None
