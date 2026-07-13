"""Symbolic shell-word analysis for placeholder-rooted executable paths."""
from __future__ import annotations

import re
from functools import lru_cache

from printf_policy import decode_shell_escapes, printf_value
from shell_glob_policy import brace_variants, glob_match, overflow_glob_match
from text_context_policy import mask_non_shell_context

INNER_EXPANSION_RE = re.compile(r'\$\{(?P<body>[^{}]*)\}')
SIMPLE_EXPANSION_RE = re.compile(r'\$(?P<name>[A-Za-z_][A-Za-z0-9_]*)')
INNER_COMMAND_RE = re.compile(r'\$\((?P<body>[^()]*)\)')
BACKTICK_RE = re.compile(r'`(?P<body>[^`]*)`')
ANSI_C_RE = re.compile(r"\$'(?P<body>(?:\\.|[^'])*)'")
NAME_RE = re.compile(r'(?P<name>[A-Za-z_][A-Za-z0-9_]*)(?:\[[^]]+\])?')
OPERATOR_RE = re.compile(r'(?::[-=+?]|[-=+?]|%%?|##?)')
EXECUTABLE_EXAMPLES = ('python', 'python2', 'python2.7', 'python3', 'python3.11',
                       'node', 'bash', 'sh', 'hermes')
SHELL_SPECIALS = '$~*?[]{}'


def _literal(char: str) -> str:
    return f'__literal_{ord(char):x}__'


def _protect_chars(value: str, chars: str) -> str:
    return ''.join(_literal(char) if char in chars else char for char in value)


def _protect_shell_literals(word: str) -> str:
    word = re.sub(r'\\([$~*?\[\]{}])', lambda match: _literal(match.group(1)), word)
    word = re.sub(r"'([^']*)'",
                  lambda match: "'" + _protect_chars(
                      match.group(1), SHELL_SPECIALS) + "'", word)
    def quoted(match: re.Match) -> str:
        value = re.sub(r'\{[^{}$]*(?:,|\.\.)[^{}$]*\}',
                       lambda brace: _protect_chars(brace.group(0), '{}'),
                       match.group(1))
        return '"' + _protect_chars(value, '~*?[]') + '"'
    return re.sub(r'"((?:\\.|[^"])*)"', quoted, word)


def _shell_words(line: str) -> list[str]:
    words: list[str] = []
    buffer: list[str] = []
    quote = ''
    command_depth = 0
    index = 0
    while index < len(line):
        char = line[index]
        if char == '\\' and index + 1 < len(line):
            buffer.extend((char, line[index + 1]))
            index += 2
            continue
        if char in {'"', "'", '`'} and not command_depth:
            quote = '' if quote == char else (char if not quote else quote)
        if not quote and line.startswith('$(', index):
            command_depth += 1
        elif not quote and char == ')' and command_depth:
            command_depth -= 1
        if not quote and not command_depth and (char.isspace() or char in ';|&'):
            if buffer:
                words.append(''.join(buffer))
                buffer = []
        else:
            buffer.append(char)
        index += 1
    if buffer:
        words.append(''.join(buffer))
    return words


def _parameter_value(body: str, dynamic: bool) -> str:
    match = NAME_RE.match(body)
    if not match:
        return '*' if dynamic else body
    name = match.group('name')
    rest = body[match.end():]
    operator = OPERATOR_RE.search(rest)
    if name.upper() in {'HOME', 'HERMES_HOME'}:
        if operator and operator.group(0) in {'+', ':+'}:
            return rest[operator.end():]
        return f'${name.upper()}'
    if dynamic:
        if operator and operator.group(0).startswith(('%', '#')):
            return '*'
        return rest[operator.end():] if operator else '*'
    if not operator or operator.group(0) in {'+', ':+'}:
        return ''
    if operator.group(0).startswith(('%', '#')):
        return ''
    return rest[operator.end():]


def _command_value(body: str, dynamic: bool) -> str:
    printed = printf_value(body)
    if printed is not None:
        return printed
    if re.search(r'(?:\$(?:HOME|HERMES_HOME)|<[A-Za-z0-9_-]+>)', body):
        return body
    return '*' if dynamic else ''


def _project(word: str, dynamic: bool) -> str:
    word = ANSI_C_RE.sub(lambda match: decode_shell_escapes(match.group('body')), word)
    word = _protect_shell_literals(word)
    while True:
        match = INNER_EXPANSION_RE.search(word)
        if not match:
            break
        value = _parameter_value(match.group('body'), dynamic)
        word = word[:match.start()] + value + word[match.end():]
    while True:
        match = INNER_COMMAND_RE.search(word)
        if not match:
            break
        value = _command_value(match.group('body'), dynamic)
        word = word[:match.start()] + value + word[match.end():]
    word = BACKTICK_RE.sub(lambda match: _command_value(match.group('body'), dynamic),
                           word)
    def simple(match: re.Match) -> str:
        name = match.group('name')
        if name.upper() in {'HOME', 'HERMES_HOME'}:
            return f'${name.upper()}'
        return '*' if dynamic else ''
    word = SIMPLE_EXPANSION_RE.sub(simple, word)
    word = re.sub(r'\\~', '__literal_tilde__', word)
    word = re.sub(r'(["\'])~', r'\1__literal_tilde__', word)
    word = re.sub(r'\\([*?\[\]{}])',
                  lambda match: f'__literal_{ord(match.group(1)):x}__', word)
    word = word.translate({ord('"'): None, ord("'"): None, ord('\\'): None})
    return re.sub(r'\{(<[^>\n]+>|\$(?:HOME|HERMES_HOME))\}', r'\1', word,
                  flags=re.IGNORECASE)


@lru_cache(maxsize=4)
def _executable_re(placeholders: tuple[str, ...]) -> re.Pattern:
    names = '|'.join(re.escape(name) for name in sorted(placeholders, key=len, reverse=True))
    return re.compile(
        rf'(?:<(?:{names})>|\$(?:HERMES_HOME|HOME)|'
        r'(?<![A-Za-z0-9._-])~(?:[A-Za-z0-9._-]+)?)'
        r'(?:/[^/\n]*)*/'
        r'(?:python(?:[0-9]+(?:\.[0-9]+)*)?|node|bash|sh|hermes)'
        r'(?![A-Za-z0-9._-])', re.IGNORECASE,
    )


@lru_cache(maxsize=4)
def _root_re(placeholders: tuple[str, ...]) -> re.Pattern:
    names = '|'.join(re.escape(name) for name in sorted(placeholders, key=len, reverse=True))
    return re.compile(
        rf'<(?:{names})>|\$(?:HERMES_HOME|HOME)|'
        r'(?<![A-Za-z0-9._-])~(?:[A-Za-z0-9._-]+)?', re.IGNORECASE)


def _dynamic_executable(word: str, placeholders: tuple[str, ...]) -> bool:
    projected = _project(word, True)
    if _executable_re(placeholders).search(projected):
        return True
    root = _root_re(placeholders).search(projected)
    if not root or '/' not in projected[root.end():]:
        return False
    segment = projected.rsplit('/', 1)[-1]
    if not any(char in segment for char in '*?[{'):
        return False
    patterns = brace_variants(segment)
    if patterns is None:
        return overflow_glob_match(EXECUTABLE_EXAMPLES, segment)
    return any(glob_match(name, pattern)
               for pattern in patterns for name in EXECUTABLE_EXAMPLES)


def _unsafe_word(word: str, placeholders: tuple[str, ...]) -> bool:
    if re.fullmatch(r'<https?://[^\s>]+>', word, re.IGNORECASE):
        return False
    exact = _project(word, False)
    return bool(_executable_re(placeholders).search(exact) or
                _dynamic_executable(word, placeholders))


def placeholder_executable_path(text: str, placeholders: tuple[str, ...]) -> bool:
    text = mask_non_shell_context(text).replace('`/`', '` `').replace('\\\n', '')
    return any(_unsafe_word(word, placeholders)
               for line in text.splitlines() for word in _shell_words(line))
