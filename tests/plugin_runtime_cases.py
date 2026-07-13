"""Complete plugin source variants for real-manager behavior regressions."""
from __future__ import annotations

PLUGIN_TEMPLATE = '''from __future__ import annotations

SCHEMA = {{
    "name": "fixture_echo",
    "description": "Exercise a deterministic fixture.",
    "input_schema": {{"type": "object", "properties": {{}}}},
}}


def fixture_echo(args):
    if not isinstance(args, dict):
        return {bad!r}
    return {normal!r}


def fixture_status(args):
    return {command!r}


def register(ctx):
    ctx.register_tool("fixture_echo", "fixture", SCHEMA, fixture_echo,
                      description="Exercise a deterministic fixture.")
    ctx.register_command("fixture-status", fixture_status,
                         description="Report fixture status.")
'''


def plugin_source(normal: str, bad: str, command: str = 'ready') -> str:
    return PLUGIN_TEMPLATE.format(normal=normal, bad=bad, command=command)


BROKEN_BEHAVIORS = (
    ('bad-success', '{"success": true}', '{"success": true}', 'ready'),
    ('normal-failure', '{"success": false}', '{"success": false}', 'ready'),
    ('malformed-empty', 'not-json', 'not-json', ''),
)
