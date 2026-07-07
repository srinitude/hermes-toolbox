"""Compatibility helpers for the hermes-skills-lab tutorial plugin.

Runtime registration is implemented in __init__.py so Hermes can load the
plugin from a directory path. These helper modules keep the public package
layout close to the documented Hermes plugin shape.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PLUGIN_DIR = Path(__file__).resolve().parent
DATA_FILE = PLUGIN_DIR / 'data' / 'plugin.json'


def load_plugin_data() -> dict[str, Any]:
    if not DATA_FILE.exists():
        return {'name': PLUGIN_DIR.name, 'description': 'Hermes tutorial plugin'}
    return json.loads(DATA_FILE.read_text(encoding='utf-8'))


def tutorial_package_summary(args: dict | None = None, **kwargs: Any) -> str:
    del kwargs
    args = args if isinstance(args, dict) else {}
    data = load_plugin_data()
    payload = {
        'success': True,
        'plugin': PLUGIN_DIR.name,
        'query': args.get('query') or args.get('topic'),
        'description': data.get('description'),
        'lessons': data.get('lessons', [])[:5],
        'official_sources': data.get('official_sources', [])[:5],
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)
