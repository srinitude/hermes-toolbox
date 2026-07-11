# Hermes Public Package Runtime Validation

Release-pinned notes for auditing staged Hermes Agent plugins and profile distributions without fake contexts, model calls, or writes to live profiles. Revalidate against the target release before use.

## General plugin discovery

Use Hermes's own interpreter and a fresh disposable home. A launcher may unset `PYTHONPATH`, so invoke the installed Hermes venv Python for direct imports.

```python
from hermes_cli.plugins import (
    PluginContext,
    PluginManager,
    discover_plugins,
    get_plugin_manager,
    get_plugin_commands,
    resolve_plugin_command_result,
)
from tools.registry import registry

discover_plugins()
manager = get_plugin_manager()
assert isinstance(manager, PluginManager)
```

Do not instantiate `PluginContext` or call `register()` manually for a discovery test. `PluginManager` imports the package, creates the real context, calls `register(ctx)`, and records attribution.

### Staged local packages

`hermes plugins install` accepts Git identifiers/URLs, not an ordinary local directory. For an unpublished package:

1. Create an isolated `HOME`, `HERMES_HOME`, and cache root.
2. Copy the candidate under `$HERMES_HOME/plugins/<directory>`.
3. Enable it through the real CLI:

```bash
hermes plugins enable <manifest-name-or-canonical-key> --no-allow-tool-override
```

4. Discover it in a fresh Python subprocess with `PYTHONDONTWRITEBYTECODE=1`.

Use `env -i` with a minimal `PATH` and no credentials. If the no-network guarantee is strict, use an available network namespace such as `unshare -Urn --`; merely omitting API keys does not prevent arbitrary import-time network code.

Do not set `HERMES_SAFE_MODE`: that skips discovery. Leave `HERMES_ENABLE_PROJECT_PLUGINS` unset so project-local plugins cannot contaminate the result. Pip entry points and bundled plugins are still scanned, so select the candidate by canonical key and assert `source == "user"`.

### Registration parity

`PluginManager.list_plugins()` exposes status and counts, not exact names. Exact attribution currently lives on the loaded record:

```python
loaded = manager._plugins[plugin_key]
assert loaded.enabled
assert loaded.error is None
actual_tools = set(loaded.tools_registered)
actual_hooks = set(loaded.hooks_registered)
actual_commands = set(loaded.commands_registered)
```

The core manifest parser consumes `provides_tools` and `provides_hooks`. Fields such as `provides_commands` and `provides_skills` may be package-policy metadata but must be compared separately:

```python
slash_commands = {
    name for name, entry in get_plugin_commands().items()
    if entry["plugin"] == loaded.manifest.name
}
plugin_skills = set(manager.list_plugin_skills(loaded.manifest.name))
```

For every registered skill, require the resolved path to be a real file named `SKILL.md`. Core `register_skill()` checks existence but does not itself enforce that stronger shape.

### Real behavior probes

Exercise safe/local tool handlers through the registry, not by calling the handler object directly:

```python
result = registry.dispatch(
    tool_name,
    safe_args,
    task_id="package-probe",
    session_id="package-probe",
)
```

Use `model_tools.handle_function_call()` only when the test intends to include the full hook/middleware/approval/result-transform pipeline. It is a broader behavior surface and can invoke other enabled plugin code.

Exercise slash commands through their registered handler plus `resolve_plugin_command_result()` so async handlers follow the real bridge. Exercise plugin CLI subcommands by spawning `hermes <registered-command> <safe-local-args>` under the same disposable environment.

Manifest `requires_env` is metadata and installer UX; do not assume it prevents plugin import or `register()` execution. A package with external dependencies is blocked unless its approved local/offline behavior can run with credentials absent and network denied.

`hermes plugins list --json` is metadata discovery only. It does not prove module import, registration, attribution, or handler behavior.

## Profile distribution validation

Use a custom root outside the platform-native Hermes home:

```bash
HERMES_HOME="$ROOT" hermes profile install "$PACKAGE" --name "$TEST_NAME" --yes
HERMES_HOME="$ROOT" hermes profile info "$TEST_NAME"
HERMES_HOME="$ROOT" hermes -p "$TEST_NAME" config check
HERMES_HOME="$ROOT" hermes -p "$TEST_NAME" skills list --enabled-only
```

Also isolate `HOME` and omit `--alias`; aliases write to the user's executable path. Do not use `--force` in a fresh root.

These commands do not require a chat/model call. `skills list` may create bookkeeping directories, so the entire root must be disposable.

### Installer caveats

- Hermes profile install has no native `--dry-run`; a package manager must implement its own side-effect-free preview.
- Hermes requires only a manifest `name`. Stronger requirements such as SOUL, config, README, author, license, and tests are package-policy gates.
- The source package should omit runtime provenance, but the installed manifest is expected to gain `source` and `installed_at`.
- `profile info` can return success while printing that a profile is not a distribution; assert output or inspect the installed manifest.
- `config check` is diagnostic and may exit successfully despite missing configuration or credentials; parse/assert its findings instead of treating exit zero as sufficient.
- Installation previews and then installs, staging/reading the source twice. Pin candidate hashes and ensure source quiescence across the probe.
- Reject symlinks before installation.
- Independently verify every `distribution_owned` path. Some releases parse and serialize that field without using it to constrain the copy implementation.
- Inspect the source package and installed tree separately: source privacy rules and installed runtime-provenance expectations differ.

## Literal read-only audits

Do not execute these probes when the user requested a documentary/source-only audit. Report the exact future command shapes instead. Avoid web extractors that persist large-page caches under a literal zero-write constraint; use browser DOM inspection or tightly bounded streamed reads. If a managed tool refreshes a cache anyway, disclose the exact paths and do not claim global zero writes.