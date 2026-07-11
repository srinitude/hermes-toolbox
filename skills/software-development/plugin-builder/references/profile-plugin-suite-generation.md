# Profile plugin-suite generation and validation pitfalls

Use this reference when building a large profile-local plugin suite from a profile specification, especially when many plugins are generated at once and enabled together.

## Lessons

- Treat a blanket user approval for a profile spec as approval for the named profile/workspace/plugin surfaces only. Preserve the spec's own gates: do not run paid APIs, publish, enter credentials, grant OAuth, create accounts, sync browser profiles, or execute mutating external commands merely because the profile spec was approved.
- For profile-installed plugin suites, validate against the active profile home, not the default Hermes home. In Python verifiers, set `HERMES_HOME=/path/to/profile` before loading plugin manager/registry state.
- Use `get_plugin_manager()` rather than constructing a separate `PluginManager()` when validating hook behavior. The global manager is what `get_pre_tool_call_block_message()` and registry-backed integration checks use.
- Run validation with `PYTHONDONTWRITEBYTECODE=1` and delete `__pycache__/`, `*.pyc`, and `*.pyo` before runtime hygiene scans. Otherwise the verifier can create the bytecode artifacts it later flags as private/generated runtime debris.
- Check generated plugin tool names for collisions across the whole enabled suite before loading. If two plugins declare the same tool name, Hermes rejects the later registration unless an explicit override is requested and allowed. Prefer renaming/removing the duplicate; do not set `allow_tool_override: true` as a shortcut.
- When code-generating Python files, compile at least one generated file before bulk validation. Common template mistakes include preserving indentation after a top-level docstring and accidentally embedding literal newlines inside string literals.
- If Kanban board selection looks wrong after `boards switch`, inspect environment precedence. `HERMES_KANBAN_BOARD` overrides the persisted `<root>/kanban/current` file; unset it for CLI validation when you need to prove the persisted active board.
- If a seeded Kanban board starts workers during validation, record what happened and verify side effects stayed inside the approved scope. Do not mistake worker-created planning artifacts for external publishing/spend actions.

## Focused verifier pattern

A profile plugin-suite verifier should prove:

1. profile home and workspace exist;
2. expected config keys are set;
3. expected plugin manifests are enabled and `allow_tool_override` is false unless explicitly approved;
4. plugin directories contain no `.env`, `auth.json`, `state.db*`, `__pycache__/`, `*.pyc`, or `*.pyo`;
5. expected bootstrap skills exist;
6. `get_plugin_manager().discover_and_load(force=True)` reports no plugin errors;
7. every manifest-declared tool is registered in `tools.registry`;
8. representative tool dispatches return JSON strings;
9. a representative high-risk tool call without `approval_id` is blocked by `pre_tool_call`;
10. Kanban board/cards exist when the spec includes them;
11. no raw secret patterns appear in authored Markdown/YAML/Python/JSON files.

Label this as focused integration verification, not as proof that paid/vendor/API flows succeeded unless those flows actually ran under scoped approval.
