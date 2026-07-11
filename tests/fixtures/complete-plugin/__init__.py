"""Minimal complete plugin fixture used by the public export pipeline tests."""
from __future__ import annotations

import json

PLUGIN_NAME = 'complete-plugin'
FIXTURE_ECHO_SCHEMA = {
    'name': 'fixture_echo',
    'description': 'Echo a message back as structured JSON.',
    'input_schema': {
        'type': 'object',
        'properties': {'message': {'type': 'string', 'description': 'Text to echo.'}},
    },
}


def fixture_echo(args: object) -> str:
    if not isinstance(args, dict):
        return json.dumps({'success': False, 'plugin': PLUGIN_NAME,
                           'error': 'arguments must be an object'})
    return json.dumps({'success': True, 'plugin': PLUGIN_NAME,
                       'echo': str(args.get('message', ''))})


def fixture_status(args: str) -> str:
    return f'{PLUGIN_NAME} is installed and responding (args: {args or "none"})'


def register(ctx) -> None:
    ctx.register_tool('fixture_echo', 'fixture', FIXTURE_ECHO_SCHEMA, fixture_echo,
                      description='Echo a message back as structured JSON.')
    ctx.register_command('fixture-status', fixture_status,
                         description='Report fixture plugin status.')
