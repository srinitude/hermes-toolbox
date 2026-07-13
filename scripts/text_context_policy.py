"""Mask documentation and markup regions before shell-path analysis."""
from __future__ import annotations

import re

FULL_URL_RE = re.compile(r'https?://\S+', re.IGNORECASE)
SHELL_URL_BREAK_RE = re.compile(r'\$\(|[|)`<>]|&&|[;&](?=[\s$<{"\'])')
MARKDOWN_URL_RE = re.compile(r'\]\(https?://[^)\s]+\)', re.IGNORECASE)
PROSE_URL_PREFIX_RE = re.compile(r'^\s*(?:see|visit|open|read|url:)\s', re.IGNORECASE)


def _tag_end(text: str, start: int) -> int:
    match = re.match(r'</?[A-Za-z][A-Za-z0-9:_-]*', text[start:])
    if not match:
        return -1
    cursor = start + match.end()
    if cursor >= len(text) or text[cursor] == '>':
        return cursor if text.startswith('</', start) else -1
    if not text[cursor].isspace() and text[cursor] != '/':
        return -1
    quote = ''
    for cursor in range(cursor, len(text)):
        char = text[cursor]
        if char in {'"', "'"}:
            quote = '' if quote == char else (char if not quote else quote)
        elif char == '>' and not quote:
            return cursor
    return -1


def _mask_markup(text: str) -> str:
    masked = list(text)
    cursor = 0
    while cursor < len(text):
        start = text.find('<', cursor)
        if start < 0:
            break
        end = _tag_end(text, start)
        if end >= start:
            masked[start:end + 1] = ' ' * (end - start + 1)
            cursor = end + 1
        else:
            cursor = start + 1
    return ''.join(masked)


def _quoted_shell_boundary(line: str, start: int, close: int) -> int:
    boundaries = (line.find('$(', start, close), line.find('`', start, close))
    live = [index for index in boundaries if index >= 0]
    return min(live) if live else -1


def _url_end(line: str, match: re.Match) -> int:
    start = match.start()
    quote = line[start - 1] if start and line[start - 1] in {'"', "'"} else ''
    if quote:
        close = line.find(quote, start)
        if close >= 0:
            boundary = _quoted_shell_boundary(line, start, close) if quote == '"' else -1
            return boundary if boundary >= 0 else close
    if PROSE_URL_PREFIX_RE.match(line[:start]):
        return start + len(match.group(0))
    shell_break = SHELL_URL_BREAK_RE.search(match.group(0))
    return start + (shell_break.start() if shell_break else len(match.group(0)))


def _mask_url_line(line: str) -> str:
    pieces = []
    cursor = 0
    for match in FULL_URL_RE.finditer(line):
        end = _url_end(line, match)
        pieces.extend((line[cursor:match.start()], '<url>'))
        cursor = end
    pieces.append(line[cursor:])
    return ''.join(pieces)


def _mask_urls(text: str) -> str:
    return ''.join(_mask_url_line(line) for line in text.splitlines(keepends=True))


def mask_non_shell_context(text: str) -> str:
    text = _mask_markup(text)
    text = MARKDOWN_URL_RE.sub('](<url>)', text)
    return _mask_urls(text)
