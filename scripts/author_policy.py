"""YAML-aware author metadata locations and identity matching."""
from __future__ import annotations

import re
from pathlib import Path

from author_path_policy import approved_author_metadata_path

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

from toolbox_common import FRONTMATTER_RE, text_file

AUTHOR_METADATA_FILES = {'SKILL.md', 'distribution.yaml', 'plugin.yaml'}
AUTHOR_FIELD_RE = re.compile(
    r'^\s*(?:-\s*)?(?:(?P<quote>["\'])author(?P=quote)|author)\s*:\s*'
    r'(?P<value>.+?)\s*$',
    re.IGNORECASE,
)
INLINE_AUTHOR_RE = re.compile(r'\{[^}\n]*["\']?author["\']?\s*:', re.IGNORECASE)
NON_PERSON_AUTHORS = {
    'acme software', 'hermes agent', 'hermes toolbox contributors',
    'nous research', 'openai', 'openai codex',
}
SAFE_AUTHOR_PLACEHOLDERS = {'<name>', '<repo-author-name>'}
SAFE_AUTHOR_PLACEHOLDER_KEYS = {value.casefold() for value in SAFE_AUTHOR_PLACEHOLDERS}
STRING_TAG = 'tag:yaml.org,2002:str'
MERGE_TAG = 'tag:yaml.org,2002:merge'


def _yaml_source(path: Path, text: str) -> tuple[str, int] | None:
    if path.name != 'SKILL.md':
        return text, 1
    match = FRONTMATTER_RE.search(text)
    return (match.group(1), 2) if match else None


def _scalar_spans(value: ScalarNode, first_line: int) -> list[tuple[int, int, int | None]]:
    start, end = value.start_mark, value.end_mark
    spans = []
    for source_line in range(start.line, end.line + 1):
        first = start.column if source_line == start.line else 0
        last = end.column if source_line == end.line else None
        spans.append((first_line + source_line, first, last))
    return spans


def _merge_targets(node: object) -> list[object]:
    if isinstance(node, SequenceNode):
        return list(node.value)
    if not isinstance(node, MappingNode):
        return []
    return [value for key, value in node.value
            if isinstance(key, ScalarNode) and key.tag == MERGE_TAG]


def _mapping_has_author(node: object, active: set[int] | None = None) -> bool:
    active = set() if active is None else active
    if id(node) in active:
        return True
    active.add(id(node))
    direct = isinstance(node, MappingNode) and any(
        isinstance(key, ScalarNode) and str(key.value).casefold() == 'author'
        for key, _ in node.value
    )
    result = direct or any(_mapping_has_author(child, active)
                           for child in _merge_targets(node))
    active.remove(id(node))
    return result


def _children(node: object) -> list[object]:
    if isinstance(node, SequenceNode):
        return list(node.value)
    if isinstance(node, MappingNode):
        return [value for _, value in node.value]
    return []


def _nested_author_lines(node: object, first_line: int, root: bool = True,
                         active: set[int] | None = None) -> list[int]:
    active = set() if active is None else active
    if id(node) in active:
        return []
    active.add(id(node))
    lines = []
    if isinstance(node, MappingNode) and not root:
        lines.extend(first_line + key.start_mark.line for key, _ in node.value
                     if (isinstance(key, ScalarNode)
                         and str(key.value).casefold() == 'author'))
    for child in _children(node):
        lines.extend(_nested_author_lines(child, first_line, False, active))
    active.remove(id(node))
    return lines


def _author_entries(source: str, first_line: int) -> list[tuple]:
    try:
        node = yaml.compose(source)
    except yaml.YAMLError:
        return []
    if not isinstance(node, MappingNode):
        return []
    entries = []
    author_count = 0
    for key, value in node.value:
        if isinstance(key, ScalarNode) and key.tag == MERGE_TAG:
            if _mapping_has_author(value):
                entries.append((None, first_line + key.start_mark.line, True, []))
            continue
        if (not isinstance(key, ScalarNode)
                or str(key.value).casefold() != 'author'):
            continue
        author_count += 1
        line = first_line + key.start_mark.line
        plain = isinstance(value, ScalarNode) and value.tag == STRING_TAG
        aliased = plain and value.start_mark.index < key.end_mark.index
        invalid = (str(key.value) != 'author' or not plain
                   or value.style in {'|', '>'} or aliased)
        spans = _scalar_spans(value, first_line) if plain else []
        entries.append((str(value.value) if plain else None, line, invalid, spans))
    entries.extend((None, line, True, [])
                   for line in _nested_author_lines(node, first_line))
    if author_count > 1:
        return [(value, line, True, spans) for value, line, _, spans in entries]
    return entries


def metadata_author_context(repo: Path, files: list[Path]) -> tuple:
    names: set[str] = set()
    locations: set[tuple[str, int]] = set()
    invalid: set[tuple[str, int]] = set()
    spans: dict[tuple[str, int], list[tuple[int, int | None]]] = {}
    for path in files:
        if not path.exists() or not text_file(path):
            continue
        rel = path.relative_to(repo).as_posix()
        if not approved_author_metadata_path(rel):
            continue
        source = _yaml_source(path, path.read_text(encoding='utf-8', errors='ignore'))
        if source is None:
            continue
        for value, line, bad, value_spans in _author_entries(*source):
            locations.add((rel, line))
            if bad or not value:
                invalid.add((rel, line))
                continue
            names.add(value)
            for span_line, start, end in value_spans:
                locations.add((rel, span_line))
                spans.setdefault((rel, span_line), []).append((start, end))
    return names, locations, invalid, spans


def _personal_author(name: str) -> bool:
    normalized = ' '.join(name.casefold().split())
    return (bool(normalized) and normalized not in NON_PERSON_AUTHORS
            and normalized not in SAFE_AUTHOR_PLACEHOLDER_KEYS)


def author_identity_terms(author_names: set[str]) -> list[str]:
    terms: set[str] = set()
    for name in author_names:
        if not _personal_author(name):
            continue
        terms.add(name)
    return sorted(terms, key=len, reverse=True)


def contains_term(line: str, term: str) -> bool:
    left = r'(?<!\w)' if term[:1].isalnum() else ''
    right = r'(?!\w)' if term[-1:].isalnum() else ''
    body = r'\s+'.join(re.escape(part) for part in term.split())
    return re.search(f'{left}{body}{right}', line, re.IGNORECASE) is not None


def identity_view(line: str, spans: list[tuple[int, int | None]]) -> str:
    chars = list(line)
    for start, end in spans:
        stop = len(chars) if end is None else min(end, len(chars))
        chars[start:stop] = ' ' * max(0, stop - start)
    return ''.join(chars)


def unsafe_author_field(line: str) -> bool:
    if INLINE_AUTHOR_RE.search(line):
        return True
    match = AUTHOR_FIELD_RE.match(line)
    if not match:
        return False
    value = match.group('value').strip().strip('"\'')
    return value not in SAFE_AUTHOR_PLACEHOLDERS
