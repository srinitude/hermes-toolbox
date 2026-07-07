"""Compatibility helpers for the hermes-prompting-lab tutorial plugin.

Runtime registration is implemented in __init__.py so Hermes can load the
plugin from a directory path. These helper modules keep the public package
layout close to the documented Hermes plugin shape.
"""
from __future__ import annotations

from pathlib import Path
import json

PLUGIN_DIR = Path(__file__).resolve().parent
DATA_FILE = PLUGIN_DIR / 'data' / 'plugin.json'


def _data() -> dict:
    if not DATA_FILE.exists():
        return {'commands': [], 'description': 'Hermes tutorial plugin', 'lessons': []}
    return json.loads(DATA_FILE.read_text(encoding='utf-8'))


def _render(raw_args: str = '') -> str:
    data = _data()
    focus = raw_args.strip()
    lines = [data.get('description', 'Hermes tutorial plugin')]
    if focus:
        lines.append(f'Focus: {focus}')
    for lesson in data.get('lessons', [])[:5]:
        lines.append(f"- {lesson.get('id')}: {lesson.get('title')}")
    return '\n'.join(lines)


COMMANDS = [(name, _render, _data().get('description', 'Hermes tutorial plugin'), '[topic]') for name in _data().get('commands', [])]
