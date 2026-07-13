"""Select structured metadata payloads embedded in public text files."""
from __future__ import annotations

import re
from pathlib import Path

from toolbox_common import FRONTMATTER_RE

def _fence_re(mark: str) -> re.Pattern:
    escaped = re.escape(mark)
    return re.compile(
        rf'(?msi)^[ ]{{0,3}}(?P<fence>{escaped}{{3,}})(?P<kind>ya?ml|json)'
        rf'(?:[ \t]+[^\n]*)?\n'
        rf'(?P<body>.*?)\n[ ]{{0,3}}(?P=fence){escaped}*[ \t]*$'
    )


FENCE_RES = tuple(_fence_re(mark) for mark in ('`', '~'))
StructuredPayload = tuple[str, int, str, str]


def _fenced_payloads(text: str) -> list[StructuredPayload]:
    matches = [match for pattern in FENCE_RES for match in pattern.finditer(text)]
    payloads = []
    for match in sorted(matches, key=lambda item: item.start()):
        offset = text.count('\n', 0, match.start('body'))
        payloads.append((match.group('body'), offset, match.group('kind'), 'fence'))
    return payloads


def structured_payloads(rel: str, text: str) -> list[StructuredPayload]:
    path = Path(rel)
    suffix = path.suffix.lower()
    if suffix in {'.yaml', '.yml', '.json'}:
        return [(text, 0, suffix.lstrip('.'), 'document')]
    payloads: list[StructuredPayload] = []
    if path.name == 'SKILL.md':
        match = FRONTMATTER_RE.match(text)
        if match:
            payloads.append((match.group(1), 1, 'yaml', 'frontmatter'))
    return payloads + _fenced_payloads(text)
