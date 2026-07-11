# Exact Built-in Tool Override Validation

Use this when a non-bundled plugin replaces built-in Hermes tools with `override=True`.

## Required fresh-process matrix

Run separate disposable processes for:

1. **No override grant:** omit `plugins.entries.<plugin>.allow_tool_override` entirely.
2. **Normal chat:** grant override, but no native feature/toolset context.
3. **Orchestrator:** grant override and enable the native toolset/profile context.
4. **Worker/task context:** grant override and set only the native task-scope environment.

Use a normal `$HOME/.hermes` relationship, isolated XDG paths, a minimal environment, `PYTHONNOUSERSITE=1`, and `PYTHONDONTWRITEBYTECODE=1`. Copy only source files, excluding `__pycache__` and `*.pyc`.

## Prove exact ownership—not merely replacement

Import only the native module needed to register the built-ins, snapshot each original handler object, then load the plugin through the real global `discover_plugins()` / `get_plugin_manager()` path.

For the allowed case, require all of the following for every overridden tool:

- plugin load is enabled with no error;
- `loaded.tools_registered` is the exact expected set;
- handler object differs from the native handler;
- `handler.__globals__["__name__"]` and `registry._plugin_owner_of(handler)` equal the exact plugin module namespace;
- schema equals the evaluated native schema;
- `check_fn` is the same native function object;
- toolset name is unchanged;
- manifest source and loaded module path point to the disposable user plugin.

Do not classify `handler.__module__ != native_module` as ownership proof; an unrelated replacement would pass.

For the ungranted case, require:

- plugin disabled;
- error names `allow_tool_override` and the blocked tool;
- no registered plugin tools or plugin toolsets;
- every native handler remains the identical original object;
- no partial override occurred.

## Verify real visibility semantics

Registry membership is not model visibility. Resolve the toolset to tool names with the host's normal resolver, then call the real registry definition API. Prove the native visibility matrix in separate processes—for example, zero tools in ordinary chat, the full orchestrator set, and the reduced worker set.

An exact schema override that drops native `check_fn` functions is not exact: it can expose privileged/orchestrator tools in ordinary chats or workers.

## Installed-wheel acceptance

Build a wheel, install it into a disposable virtual environment, and copy the packaged plugin directory into a disposable Hermes home. Run the same real-manager ownership/schema/check/visibility probe using only the installed wheel plus the pinned Hermes source/runtime.

If compatibility contracts or ledgers live outside the Python package in a source checkout, force-include them into the wheel and resolve them source-tree-first, packaged-data-second. Require the installed probe to load those real files; do not duplicate authoritative JSON in tracked source.

Ignore unrelated bundled-plugin import warnings only when the target plugin reports enabled, exact ownership passes, and the probe exits successfully.

## Acceptance sequence

1. Witness RED on missing ownership, check-function, or visibility parity.
2. Implement the smallest registration correction.
3. Run the focused real-manager matrix.
4. Run handler/integration regressions and structural checks.
5. Run installed-wheel acceptance.
6. Commit only from a quiescent tree, then run one plain foreground test file.
