"""Markup and C++ contexts that resemble sanitizer placeholders."""
from __future__ import annotations

import re

CXX_TYPE_PREFIX_RE = re.compile(r'(?:[A-Za-z_]\w*::)*[A-Za-z_]\w*$')
CXX_QUALIFIED_PREFIX_RE = re.compile(r'(?:[A-Za-z_]\w*::)+[A-Za-z_]\w*$')
CXX_GLOBAL_SPACED_PREFIX_RE = re.compile(r'(?:^|[;}])\s*[A-Za-z_]\w*\s+$')
CXX_OPEN_TEMPLATE_RE = re.compile(
    r'(?:[A-Za-z_]\w*::)*[A-Za-z_]\w*<[^>\n]*$'
)
CXX_TEMPLATE_PARAM_PREFIX_RE = re.compile(
    r'\btemplate\s*<[^>\n]*(?:typename|class)\s*(?:\.\.\.)?\s+$'
)
CXX_RETURN_COMPARISON_RE = re.compile(r'\breturn\s+[A-Za-z_]\w*$')
HTML_ATTRIBUTE = (
    r'[A-Za-z_:][A-Za-z0-9_:.-]*'
    r'(?:\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s"\'=<>`]+))?'
)
HTML_ATTRIBUTES_RE = re.compile(r'(?:' + HTML_ATTRIBUTE + r'\s*)+/?', re.DOTALL)
HTML_ATTRIBUTE_TOKEN_RE = re.compile(HTML_ATTRIBUTE, re.DOTALL)
JSX_NAMED_PREFIX_RE = re.compile(r'[A-Za-z_:][A-Za-z0-9_:.-]*\s*=\s*')
XML_NAME_RE = re.compile(r':[A-Za-z_][A-Za-z0-9_.-]*')
CXX_RVALUE_TAIL_RE = re.compile(
    r'&&\s*,\s*(?:[A-Za-z_]\w*::)*[A-Za-z_]\w*\s*&&'
)
CXX_TYPE = r'(?:[A-Za-z_]\w*::)*[A-Za-z_]\w*'
CXX_SIMPLE_SUFFIX = r'(?:(?:const|volatile)\s*)*[*&]{0,2}\s*'
CXX_ARRAY_REF_SUFFIX = (
    r'(?:(?:const|volatile)\s*)*\(\s*&&?\s*\)\s*(?:\[[^]\n]*\]\s*)+'
)
CXX_SUFFIX = rf'(?:{CXX_SIMPLE_SUFFIX}|{CXX_ARRAY_REF_SUFFIX})'
CXX_TEMPLATE_TAIL_RE = re.compile(
    rf'{CXX_SUFFIX}(?:,\s*{CXX_TYPE}\s*{CXX_SUFFIX})+'
)
JSX_COMPONENT_RE = re.compile(r'(?:\.[A-Za-z_$][A-Za-z0-9_$]*)*')


def _quote_state(current: str, char: str) -> str:
    if current == char:
        return ''
    return char if not current else current


def _tag_state(quote: str, braces: int, char: str,
               escaped: bool) -> tuple[str, int, bool, bool]:
    if escaped:
        return quote, braces, False, False
    if quote and char == '\\':
        return quote, braces, False, True
    if char in {'"', "'", '`'}:
        return _quote_state(quote, char), braces, False, False
    if quote:
        return quote, braces, False, False
    if char == '{':
        return quote, braces + 1, False, False
    if char == '}':
        return quote, max(0, braces - 1), False, False
    return quote, braces, char == '>' and not braces, False


def _tag_close(tail: str) -> int:
    quote, braces, escaped = '', 0, False
    for index, char in enumerate(tail):
        quote, braces, closed, escaped = _tag_state(quote, braces, char, escaped)
        if closed:
            return index
    return -1


def _brace_end(text: str) -> int:
    quote, braces, escaped = '', 0, False
    for index, char in enumerate(text):
        quote, braces, _, escaped = _tag_state(quote, braces, char, escaped)
        if char == '}' and not quote and braces == 0:
            return index + 1
    return -1


def _jsx_attributes(attributes: str) -> bool:
    remaining = attributes.strip().removesuffix('/').rstrip()
    while remaining:
        prefix = JSX_NAMED_PREFIX_RE.match(remaining)
        brace_at = prefix.end() if prefix else 0
        if brace_at < len(remaining) and remaining[brace_at] == '{':
            end = _brace_end(remaining[brace_at:])
            if end < 0:
                return False
            remaining = remaining[brace_at + end:].lstrip()
            continue
        token = HTML_ATTRIBUTE_TOKEN_RE.match(remaining)
        if not token:
            return False
        remaining = remaining[token.end():].lstrip()
    return True


def _jsx_component_tail(tail: str) -> bool:
    close = _tag_close(tail)
    if close < 0:
        return False
    body = tail[:close].strip()
    component = JSX_COMPONENT_RE.match(body)
    if not component:
        return False
    attributes = body[component.end():].strip()
    return not attributes or _jsx_attributes(attributes)


def _xml_tail(tail: str) -> bool:
    close = _tag_close(tail)
    if close <= 0:
        return False
    body = tail[:close].strip()
    name = XML_NAME_RE.match(body)
    if not name:
        return False
    attributes = body[name.end():].strip()
    return not attributes or bool(HTML_ATTRIBUTES_RE.fullmatch(attributes))


def _spaced_tail(tail: str, cxx_type: bool) -> bool:
    close = _tag_close(tail)
    if close <= 0:
        return False
    attributes = tail[:close].strip()
    cxx = re.fullmatch(r'(?:(?:const|volatile)\s*)*[*&]{1,2}\s*', attributes)
    return (not attributes or attributes == '/' or bool(cxx)
            or bool(cxx_type and CXX_RVALUE_TAIL_RE.fullmatch(attributes))
            or bool(cxx_type and CXX_TEMPLATE_TAIL_RE.fullmatch(attributes))
            or bool(HTML_ATTRIBUTES_RE.fullmatch(attributes))
            or _jsx_attributes(attributes))


def _cxx_tail(tail: str, line_prefix: str, stripped: str,
              cxx_type: re.Match | None) -> bool:
    if not cxx_type:
        return False
    if tail.startswith('>'):
        return bool(stripped == line_prefix
                    or CXX_QUALIFIED_PREFIX_RE.search(stripped)
                    or CXX_GLOBAL_SPACED_PREFIX_RE.search(line_prefix))
    if re.match(r'<[^<>\n]+>>|\.\.\.', tail):
        return True
    if re.match(r'(?:\[[^]\n]*\])+\s*>', tail):
        return True
    close = _tag_close(tail)
    if close > 0 and CXX_TEMPLATE_TAIL_RE.fullmatch(tail[:close].strip()):
        return True
    if re.match(r'\s*\?', tail) and CXX_RETURN_COMPARISON_RE.search(line_prefix):
        return True
    if stripped != line_prefix:
        return False
    return (tail.startswith((')', ';', ','))
            or bool(re.match(r'\([^<>\n]*\)>', tail)))


def markup_candidate(text: str, match: re.Match) -> bool:
    if text.startswith('<<', match.start()):
        return False
    tail = text[match.end():]
    if ((match.group('name')[:1].isupper() or tail.startswith('.'))
            and _jsx_component_tail(tail)):
        return True
    line_prefix = text[text.rfind('\n', 0, match.start()) + 1:match.start()]
    stripped = line_prefix.rstrip()
    cxx_type = CXX_TYPE_PREFIX_RE.search(stripped)
    if _cxx_tail(tail, line_prefix, stripped, cxx_type):
        return True
    if tail.startswith(':'):
        return _xml_tail(tail)
    if tail.startswith('@'):
        close = tail.find('>')
        return close > 1 and not any(char.isspace() for char in tail[:close])
    if tail.startswith('/>'):
        return True
    if tail[:1] in {'*', '&', ','}:
        close = tail.find('>')
        return close > 0 and '\n' not in tail[:close]
    if not tail[:1].isspace():
        return False
    return _spaced_tail(tail, bool(cxx_type))


def cxx_missing_open_context(prefix: str) -> bool:
    return bool(CXX_OPEN_TEMPLATE_RE.search(prefix)
                or CXX_TEMPLATE_PARAM_PREFIX_RE.search(prefix))
