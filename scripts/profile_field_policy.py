"""Field-aware replacement of private public-source profile identifiers."""
from __future__ import annotations

import re
from pathlib import Path

import yaml
from yaml.nodes import MappingNode, ScalarNode, SequenceNode

PROFILE_FIELDS = {'source', 'source_profile', 'source-profile', 'public_plugin_profile'}
PUBLIC_PROFILE = '<public-plugin-source-profile>'
AMBIGUOUS_PROFILE = '<ambiguous-private-profile>'
FIELD_RE = re.compile(
    r'^(?P<prefix>\s*(?:source|source_profile|source-profile|public_plugin_profile)\s*:\s*)'
    r'(?P<quote>["\']?)(?P<value>.*?)(?P=quote)(?P<comment>\s*(?:#.*)?)$',
    re.IGNORECASE,
)


def _value_contains(node: object, profile: str,
                    active: set[int] | None = None) -> bool:
    active = set() if active is None else active
    if id(node) in active:
        return True
    active.add(id(node))
    if isinstance(node, ScalarNode):
        value = str(node.value)
        result = value != PUBLIC_PROFILE and profile.casefold() in value.casefold()
    elif isinstance(node, SequenceNode):
        result = any(_value_contains(child, profile, active) for child in node.value)
    elif isinstance(node, MappingNode):
        result = any(_value_contains(value, profile, active) for _, value in node.value)
    else:
        result = False
    active.remove(id(node))
    return result


def _field_result(key: object, value: object,
                  profile: str) -> tuple[list[tuple[int, int]], bool] | None:
    if (not isinstance(key, ScalarNode)
            or str(key.value).casefold() not in PROFILE_FIELDS):
        return None
    if not isinstance(value, ScalarNode):
        return [], _value_contains(value, profile)
    exact = str(value.value).strip().casefold() == profile.casefold()
    alias = value.start_mark.index < key.end_mark.index
    if exact and not alias:
        return [(value.start_mark.index, value.end_mark.index)], False
    return [], _value_contains(value, profile)


def _profile_spans(node: object, profile: str, seen: set[int]) -> tuple[list[tuple[int, int]], bool]:
    if id(node) in seen:
        return [], False
    seen.add(id(node))
    spans: list[tuple[int, int]] = []
    ambiguous = False
    if isinstance(node, SequenceNode):
        for child in node.value:
            child_spans, child_bad = _profile_spans(child, profile, seen)
            spans.extend(child_spans)
            ambiguous = ambiguous or child_bad
        return spans, ambiguous
    if not isinstance(node, MappingNode):
        return spans, ambiguous
    for key, value in node.value:
        field = _field_result(key, value, profile)
        if field is None:
            field = _profile_spans(value, profile, seen)
        child_spans, child_bad = field
        spans.extend(child_spans)
        ambiguous = ambiguous or child_bad
    return spans, ambiguous


def _scalar_replacement(raw: str) -> str:
    decoration_match = re.match(r'(?:(?:&[A-Za-z0-9_-]+|![^\s]+)\s+)*', raw)
    decoration = decoration_match.group(0) if decoration_match else ''
    value = raw[len(decoration):]
    if value.startswith(('|', '>')):
        lines = value.splitlines()
        indent_match = re.match(r'\s*', lines[1] if len(lines) > 1 else '  ')
        indent = indent_match.group(0) if indent_match else '  '
        ending = '\n' if raw.endswith('\n') else ''
        return decoration + lines[0] + '\n' + indent + PUBLIC_PROFILE + ending
    quote = value[:1] if value[:1] in {'"', "'"} and value[-1:] == value[:1] else ''
    return decoration + quote + PUBLIC_PROFILE + quote


def _replace_spans(text: str, spans: list[tuple[int, int]]) -> str:
    for start, end in sorted(spans, reverse=True):
        text = text[:start] + _scalar_replacement(text[start:end]) + text[end:]
    return text


def _replace_yaml(text: str, profile: str) -> tuple[str, bool]:
    try:
        node = yaml.compose(text)
    except yaml.YAMLError:
        return text, False
    spans, ambiguous = _profile_spans(node, profile, set())
    return _replace_spans(text, spans), ambiguous


def _replace_lines(text: str, profile: str) -> str:
    output = []
    for line in text.splitlines(keepends=True):
        ending = '\n' if line.endswith('\n') else ''
        content = line[:-1] if ending else line
        match = FIELD_RE.match(content)
        if match and match.group('value').strip().casefold() == profile.casefold():
            quote = match.group('quote')
            content = (match.group('prefix') + quote + PUBLIC_PROFILE + quote
                       + match.group('comment'))
        output.append(content + ending)
    return ''.join(output)


def _replace_residual_segment(text: str, pattern: re.Pattern) -> tuple[str, int]:
    parts = text.split(PUBLIC_PROFILE)
    replaced = []
    count = 0
    for part in parts:
        part, found = pattern.subn(AMBIGUOUS_PROFILE, part)
        replaced.append(part)
        count += found
    return PUBLIC_PROFILE.join(replaced), count


def _replace_residuals(text: str, profile: str) -> tuple[str, int]:
    pattern = re.compile(re.escape(profile), re.IGNORECASE)
    output = []
    count = 0
    for line in text.splitlines(keepends=True):
        match = FIELD_RE.match(line.rstrip('\n'))
        prefix = match.group('prefix') if match else ''
        body, found = _replace_residual_segment(line[len(prefix):], pattern)
        output.append(prefix + body)
        count += found
    return ''.join(output), count


def _residual_contains(node: object, profile: str,
                       active: set[int] | None = None) -> bool:
    active = set() if active is None else active
    if id(node) in active:
        return False
    active.add(id(node))
    if isinstance(node, ScalarNode):
        value = str(node.value)
        result = value != PUBLIC_PROFILE and profile.casefold() in value.casefold()
    elif isinstance(node, SequenceNode):
        result = any(_residual_contains(child, profile, active) for child in node.value)
    elif isinstance(node, MappingNode):
        result = any(_residual_contains(value, profile, active) for _, value in node.value)
    else:
        result = False
    active.remove(id(node))
    return result


def _yaml_residual(text: str, profile: str) -> bool:
    try:
        node = yaml.compose(text)
    except yaml.YAMLError:
        return False
    return _residual_contains(node, profile)


def replace_profile_identifiers(text: str, rel: Path, profile: str | None) -> str:
    if not profile:
        return text
    if rel.suffix.lower() in {'.yaml', '.yml'}:
        text, ambiguous = _replace_yaml(text, profile)
        ambiguous = ambiguous or _yaml_residual(text, profile)
    else:
        text, ambiguous = _replace_lines(text, profile), False
    text, residual = _replace_residuals(text, profile)
    return text + (AMBIGUOUS_PROFILE if ambiguous and not residual else '')
