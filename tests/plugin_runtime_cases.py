"""Complete plugin source variants for real-manager behavior regressions."""
from __future__ import annotations

from pathlib import Path

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


SIDE_EFFECT_PLUGIN = '''from __future__ import annotations

import json
from pathlib import Path

MARKER = Path({marker!r})
SCHEMA = {{
    "name": "effect_tool",
    "description": "Exercise an observable local handler.",
    "input_schema": {{"type": "object", "properties": {{}}}},
}}


def record(event):
    with MARKER.open("a", encoding="utf-8") as stream:
        stream.write(event + "\\n")


def effect_tool(args):
    record("tool:object" if isinstance(args, dict) else "tool:malformed")
    if not isinstance(args, dict):
        return json.dumps({{"success": False, "plugin": "side-effect-plugin"}})
    return json.dumps({{"success": True, "plugin": "side-effect-plugin"}})


def effect_status(args):
    record("command")
    return "side-effect-plugin ready"


def observe(**kwargs):
    record("hook")
    return None


def setup_cli(parser):
    record("cli:setup")
    return None


def run_cli(args):
    record("cli:handler")
    return 0


def register(ctx):
    ctx.register_tool("effect_tool", "fixture", SCHEMA, effect_tool)
    ctx.register_command("effect-status", effect_status)
    ctx.register_hook("pre_tool", observe)
    ctx.register_cli_command("effect", "Effect command", setup_cli, run_cli)
'''


SIDE_EFFECT_MANIFEST = '''name: side-effect-plugin
kind: standalone
version: 0.1.0
description: Real local side-effect probe plugin.
provides_tools: [effect_tool]
provides_commands: [effect-status]
requires_env: []
'''


def write_side_effect_plugin(base: Path, marker: Path) -> Path:
    package = base / 'side-effect-plugin'
    package.mkdir()
    (package / '__init__.py').write_text(
        SIDE_EFFECT_PLUGIN.format(marker=str(marker)), encoding='utf-8')
    (package / 'plugin.yaml').write_text(
        SIDE_EFFECT_MANIFEST, encoding='utf-8')
    return package


CLI_PLUGIN = '''from .commands import run_cli, setup_cli


def register(ctx):
    ctx.register_cli_command({command!r}, "Owner probe", setup_cli, run_cli)
'''


MIXED_CLI_PLUGIN = '''from json import dumps as setup_cli

from .commands import run_cli


def register(ctx):
    ctx.register_cli_command({command!r}, "Owner probe", setup_cli, run_cli)
'''


CLI_COMMANDS = '''def setup_cli(parser):
    return None


def run_cli(args):
    return 0
'''


def write_cli_plugin(
    base: Path, key: str, command: str, manifest_name: str | None = None,
    mixed_setup: bool = False,
) -> Path:
    package = base / key
    package.mkdir()
    source = MIXED_CLI_PLUGIN if mixed_setup else CLI_PLUGIN
    (package / '__init__.py').write_text(
        source.format(command=command), encoding='utf-8')
    (package / 'commands.py').write_text(CLI_COMMANDS, encoding='utf-8')
    name = manifest_name or key
    manifest = f'''name: {name}\nkind: standalone\nversion: 0.1.0\ndescription: Real CLI ownership probe.\nrequires_env: []\n'''
    (package / 'plugin.yaml').write_text(manifest, encoding='utf-8')
    return package


BROKEN_BEHAVIORS = (
    ('bad-success', '{"success": true}', '{"success": true}', 'ready'),
    ('normal-failure', '{"success": false}', '{"success": false}', 'ready'),
    ('malformed-empty', 'not-json', 'not-json', ''),
)
