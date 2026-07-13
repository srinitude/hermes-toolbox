# Fresh-process Hermes Kanban override validation

Use this pattern for a staged plugin that replaces the nine native `kanban_*` tools. Re-pin every source range against the target Hermes commit.

## Minimal real setup

Run the allowed and denied cases in **separate Python subprocesses**. The registry singleton and plugin override-policy map are process-global and durable; force rediscovery is not a clean reset.

For each case:

1. Create a disposable fake home and set `HERMES_HOME=$HOME/.hermes` so `PluginContext.profile_name` resolves to `default`, not `custom`.
2. Copy only the plugin package into `$HERMES_HOME/plugins/<canonical-key>/`, excluding `__pycache__` and `*.pyc`.
3. Write `$HERMES_HOME/config.yaml` with `plugins.enabled: [<canonical-key>]`.
4. In the allowed case set `plugins.entries.<canonical-key>.allow_tool_override: true`. In the denied case omit the entry entirely to prove fail-closed default behavior.
5. Use a minimal environment with the pinned Hermes checkout and candidate `src/` on `PYTHONPATH`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONNOUSERSITE=1`, and disposable XDG roots. Do not inherit `HERMES_SAFE_MODE`, `HERMES_ENABLE_PROJECT_PLUGINS`, `HERMES_KANBAN_TASK`, credentials, or broker variables.
6. Do not dispatch handlers; discovery and registry inspection are enough and avoid broker/network effects.

## Smallest native registry initialization

Import only:

```python
from tools import kanban_tools
from tools.registry import registry
```

`tools.kanban_tools` performs the nine native top-level registrations. `discover_builtin_tools()` is valid but imports every built-in tool module and is not the smallest probe.

Snapshot each native `ToolEntry` and handler identity before plugin discovery.

## Real discovery path

Use the global APIs:

```python
from hermes_cli.plugins import discover_plugins, get_plugin_manager, get_plugin_toolsets

discover_plugins()
manager = get_plugin_manager()
loaded = manager._plugins[canonical_key]
```

Do not instantiate `PluginContext` or call the candidate's `register()` manually. The manager imports the copied package, constructs the real context, calls `register(ctx)`, catches load errors, and records attribution.

Assert provenance: `manifest.source == "user"`, the canonical key matches, and `loaded.module.__file__` resolves to the copied package under the disposable `HERMES_HOME`.

## Positive-control ownership checks

For all nine names require:

- `loaded.enabled is True`, `loaded.error is None`;
- `set(loaded.tools_registered)` equals the exact nine-name contract;
- final handler identity differs from the snapshotted native handler;
- `entry.handler.__globals__["__name__"]` equals the exact generated namespace, e.g. `hermes_plugins.hermes_kanban_policy_broker`;
- when pinning implementation internals, `registry._plugin_owner_of(entry.handler)` returns that same namespace;
- schema equals the corresponding pinned native schema constant;
- toolset equals `kanban`.

Do not accept `handler.__module__ != "tools.kanban_tools"` as ownership proof: any unrelated replacement satisfies that weak condition.

Assert toolset attribution via the real API:

```python
[key for key, _, _ in get_plugin_toolsets()]
```

Assert actual schema visibility through `resolve_toolset("kanban")` plus `registry.get_definitions(...)`, not merely by reading `entry.toolset`.

## Negative trust-gate control

In the separate ungranted process require:

- plugin disabled;
- error mentions both `allow_tool_override` and the first attempted native tool;
- `tools_registered == []`;
- every final handler is the identical snapshotted native handler;
- no plugin toolsets are reported.

This catches partial-load residue as well as an incorrect pass through the trust gate. Registration is not transactional, so preservation must be checked for every name.

## Visibility parity trap

Native Kanban entries carry two different checks: lifecycle tools are available to task workers or profiles enabling Kanban, while `kanban_list` and `kanban_unblock` are hidden from task workers. A replacement that omits `check_fn` changes the native visibility matrix:

| Context | Native | Replacement with `check_fn=None` |
|---|---:|---:|
| normal chat, no Kanban config/task | 0 | 9 when the toolset is selected (and potentially under default-all selection) |
| orchestrator with Kanban enabled | 9 | 9 |
| task worker | 7 | 9 |

If the package promises an exact native override, test the `0 / 9 / 7` matrix in fresh processes. A test that only asserts all entries have `toolset == "kanban"` misses this contract break.

## Reporting discipline

For an exact-current-tree audit, record HEAD and initial/final status. If parent-owned files change concurrently, re-read consequential files, optionally record final hashes, and state that findings refer to the final snapshot. Never attribute concurrent edits to the audit. Distinguish the executable future probe from tests actually run under a read-only boundary.
