"""Token-safe line projection for public text sanitization."""
from __future__ import annotations

import re

from toolbox_common import API_KEY_CONFIG_RE, EMAIL_RE, HERMES_HOME_RE, USER_HOME_RE

CANONICAL_PLACEHOLDER_RE = re.compile(
    r'<(?:first-name|private-term|public-plugin-source-profile|repo-author-email|repo-author-name)>'
)
PROFILE_FIELD_KEY_RE = re.compile(
    r'^\s*(?:source|source_profile|source-profile|public_plugin_profile)\s*:',
    re.IGNORECASE,
)


def _replace_term(text: str, old: str, replacement: str) -> str:
    left = r'(?<![A-Za-z0-9_-])' if old[:1].isalnum() else ''
    right = r'(?![A-Za-z0-9_-])' if old[-1:].isalnum() else ''
    return re.sub(f'{left}{re.escape(old)}{right}', replacement, text,
                  flags=re.IGNORECASE)


def _sanitize_fragment(text: str, terms: list[tuple[str, str]]) -> str:
    for old, replacement in terms:
        text = _replace_term(text, old, replacement)
    text = HERMES_HOME_RE.sub('$HERMES_HOME', text)
    text = USER_HOME_RE.sub('$HOME', text)
    text = EMAIL_RE.sub('<repo-author-email>', text)
    text = API_KEY_CONFIG_RE.sub(
        lambda match: f'# Configure {match.group(1)} through the official setup/auth/env flow, not as a non-secret config key',
        text,
    )
    return text.replace('$HOME/.hermes/plugins', '$HERMES_HOME/plugins')


def sanitize_line(line: str, terms: list[tuple[str, str]]) -> str:
    field = PROFILE_FIELD_KEY_RE.match(line)
    prefix = field.group(0) if field else ''
    line = line[len(prefix):]
    parts: list[str] = [prefix]
    cursor = 0
    for match in CANONICAL_PLACEHOLDER_RE.finditer(line):
        parts.append(_sanitize_fragment(line[cursor:match.start()], terms))
        parts.append(match.group(0))
        cursor = match.end()
    parts.append(_sanitize_fragment(line[cursor:], terms))
    return ''.join(parts)
