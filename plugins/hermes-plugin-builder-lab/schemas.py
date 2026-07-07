"""Compatibility helpers for the hermes-plugin-builder-lab tutorial plugin.

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
        return {'tools': [], 'description': 'Hermes tutorial plugin'}
    return json.loads(DATA_FILE.read_text(encoding='utf-8'))


def schema_for(tool_name: str) -> dict:
    data = _data()
    return {
        'name': tool_name,
        'description': (data.get('tool_descriptions') or {}).get(tool_name, data.get('description', 'Hermes tutorial helper')),
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': 'Question, answer, action, or topic to inspect.'},
                'term': {'type': 'string', 'description': 'Hermes concept or glossary term.'},
                'lesson_id': {'type': 'string', 'description': 'Tutorial lesson identifier.'},
                'status': {'type': 'string', 'description': 'Learning progress status.'},
            },
            'additionalProperties': True,
        },
    }


TOOLS = [(schema_for(name), None) for name in _data().get('tools', [])]
