"""Bounded symbolic model for shell ``printf`` command output."""
from __future__ import annotations

import re
import shlex

FORMAT_RE = re.compile(r'%(?:%|[-+ #0]*\d*(?:\.\d+)?[sbdiouxXfFeEgGc])')
ESCAPE_RE = re.compile(
    r'\\(?:0[0-7]{1,3}|[1-7][0-7]{0,2}|x[0-9A-Fa-f]{1,2}|u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8}|[abfnrtv\\])'
)
ESCAPES = {'a': '\a', 'b': '\b', 'f': '\f', 'n': '\n',
           'r': '\r', 't': '\t', 'v': '\v', '\\': '\\'}


def _escape_value(match: re.Match) -> str:
    code = match.group(0)[1:]
    if code[:1].isdigit():
        digits = code[1:] if code.startswith('0') and len(code) > 1 else code
        return chr(int(digits, 8))
    if code[:1] in {'x', 'u', 'U'}:
        try:
            return chr(int(code[1:], 16))
        except (OverflowError, ValueError):
            return match.group(0)
    return ESCAPES[code]


def decode_shell_escapes(value: str) -> str:
    return ESCAPE_RE.sub(_escape_value, value)


def _stop_index(value: str) -> int:
    for index, char in enumerate(value):
        if char != 'c':
            continue
        cursor = index - 1
        while cursor >= 0 and value[cursor] == '\\':
            cursor -= 1
        if (index - cursor - 1) % 2:
            return index - 1
    return -1


def _decode_percent_b(value: str) -> tuple[str, bool]:
    stop = _stop_index(value)
    prefix = value[:stop] if stop >= 0 else value
    return decode_shell_escapes(prefix), stop >= 0


def _format_argument(conversion: str, value: str) -> tuple[str, bool]:
    kind = conversion[-1]
    if kind == 'b':
        return _decode_percent_b(value)
    precision = re.search(r'\.(\d+)', conversion)
    if kind == 's' and precision:
        value = value[:int(precision.group(1))]
    if kind == 'c':
        return value[:1], False
    return (value if kind == 's' else '*'), False


def _format_once(fmt: str, arguments: list[str],
                 start: int) -> tuple[str, int, int, bool]:
    output: list[str] = []
    cursor = 0
    consumed = 0
    for match in FORMAT_RE.finditer(fmt):
        output.append(decode_shell_escapes(fmt[cursor:match.start()]))
        conversion = match.group(0)
        if conversion == '%%':
            output.append('%')
        else:
            value = arguments[start + consumed] if start + consumed < len(arguments) else ''
            value, stopped = _format_argument(conversion, value)
            output.append(value)
            consumed += 1
            if stopped:
                return ''.join(output), start + consumed, consumed, True
        cursor = match.end()
    output.append(decode_shell_escapes(fmt[cursor:]))
    return ''.join(output), start + consumed, consumed, False


def printf_value(body: str) -> str | None:
    try:
        parts = shlex.split(body)
    except ValueError:
        return None
    if len(parts) > 1 and parts[1] == '--':
        parts.pop(1)
    if parts[:2] in (['command', 'printf'], ['builtin', 'printf']):
        parts.pop(0)
    if len(parts) < 2 or parts[0] != 'printf':
        return None
    fmt, arguments = parts[1], parts[2:]
    if '%' in FORMAT_RE.sub('', fmt):
        return ''.join(arguments) or '*'
    value, index, consumed, stopped = _format_once(fmt, arguments, 0)
    while not stopped and consumed and index < len(arguments):
        extra, index, consumed, stopped = _format_once(fmt, arguments, index)
        value += extra
    return value
