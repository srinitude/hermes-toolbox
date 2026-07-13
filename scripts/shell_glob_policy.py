"""Bounded Bash-style brace and filename pattern projection."""
from __future__ import annotations

import fnmatch
import re

RANGE_RE = re.compile(
    r'^(?P<start>-?\d+|[A-Za-z])\.\.(?P<end>-?\d+|[A-Za-z])'
    r'(?:\.\.(?P<step>-?\d+))?$'
)
OVERFLOW_CHOICES = tuple(f'__overflow_{index}' for index in range(65))


def _range_values(body: str) -> tuple[str, ...] | None:
    match = RANGE_RE.fullmatch(body)
    if not match:
        return None
    start_text, end_text = match.group('start'), match.group('end')
    characters = start_text.isalpha() and end_text.isalpha()
    numeric = start_text.lstrip('-').isdigit() and end_text.lstrip('-').isdigit()
    if not characters and not numeric:
        return None
    if numeric and max(len(start_text), len(end_text)) > 100:
        return OVERFLOW_CHOICES
    start = ord(start_text) if characters else int(start_text)
    end = ord(end_text) if characters else int(end_text)
    step_text = match.group('step') or '1'
    if len(step_text) > 100:
        return OVERFLOW_CHOICES
    raw_step = int(step_text)
    if raw_step == 0:
        raw_step = 1
    step = abs(raw_step) if end >= start else -abs(raw_step)
    values = range(start, end + (1 if step > 0 else -1), step)
    rendered = []
    for value in values:
        rendered.append(chr(value) if characters else str(value))
        if len(rendered) > 64:
            break
    return tuple(rendered)


def _brace_choices(body: str) -> tuple[str, ...] | None:
    if ',' in body:
        return tuple(set(body.split(',')))
    return _range_values(body)


def brace_variants(segment: str) -> tuple[str, ...] | None:
    variants = {segment}
    while True:
        expanded: set[str] = set()
        changed = False
        for value in variants:
            match = re.search(r'\{([^{}]+)\}', value)
            choices = _brace_choices(match.group(1)) if match else None
            if not match or choices is None:
                expanded.add(value)
                continue
            expanded.update(value[:match.start()] + choice + value[match.end():]
                            for choice in choices)
            if len(expanded) > 64:
                return None
            changed = True
        if not changed:
            return tuple(expanded)
        variants = expanded


def _bounded_brace_match(name: str, pattern: str,
                         budget: list[int]) -> bool | None:
    if budget[0] <= 0:
        return None
    budget[0] -= 1
    match = re.search(r'\{([^{}]+)\}', pattern)
    if not match:
        return glob_match(name, pattern)
    choices = _brace_choices(match.group(1))
    if choices is None:
        return glob_match(name, pattern)
    if choices == OVERFLOW_CHOICES:
        return None
    unknown = False
    for choice in choices:
        candidate = pattern[:match.start()] + choice + pattern[match.end():]
        result = _bounded_brace_match(name, candidate, budget)
        if result:
            return True
        unknown = unknown or result is None
    return None if unknown else False


def overflow_glob_match(names: tuple[str, ...], pattern: str) -> bool:
    for name in names:
        result = _bounded_brace_match(name, pattern, [512])
        if result is not False:
            return True
    return False


def glob_match(name: str, pattern: str) -> bool:
    posix_class = r'\[\[:(?:alnum|alpha|digit|lower|upper|word|xdigit):\]\]'
    projected = re.sub(posix_class, '?', pattern)
    return fnmatch.fnmatchcase(name.casefold(), projected.casefold())
