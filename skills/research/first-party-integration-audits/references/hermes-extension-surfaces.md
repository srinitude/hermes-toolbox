# Hermes Agent extension and orchestration surfaces

Session-specific reference from a first-party, read-only audit of official Hermes docs and `NousResearch/hermes-agent`. Re-check live docs and source before reuse; the repository moves quickly.

## Baseline

- Official docs: `https://hermes-agent.nousresearch.com/docs/`
- Official repo: `https://github.com/NousResearch/hermes-agent`
- Source snapshot finally audited: `3a1a3c7e6727a31df89b61b27bad313430bdac45` (2026-07-09)
- Stable external compatibility boundary: `GET /v1/capabilities`

During the audit, `main` advanced by hundreds of commits relative to an earlier captured SHA. The final report re-resolved `main` and re-scanned every cited surface. For fast-moving repositories, resolve the branch at the end, not only at the beginning.

## Recommended Herdr integration hierarchy

1. User-local Hermes plugin for native tools, hooks, slash commands, CLI subcommands, and namespaced read-only skills.
2. Authenticated API server for out-of-process sessions, runs, approvals, status, skills, and toolset discovery. Feature-detect via `/v1/capabilities`.
3. Kanban for durable, restart-safe, multi-profile work.
4. `delegate_task` only for transient child-agent fan-out; scheduling semantics vary by caller/surface.
5. Whole-process OS isolation when inputs or extensions are untrusted.

## Plugin SDK contracts

User plugins are discovered from `$HERMES_HOME/plugins`; normally `~/.hermes/plugins`, and profile-specific under named-profile homes. Python entry points use group `hermes_agent.plugins`. Project plugins under `./.hermes/plugins` require `HERMES_ENABLE_PROJECT_PLUGINS=1`. Third-party plugins are opt-in; safe mode suppresses discovery.

Documented `PluginContext` surface relevant to integrations:

- `register_tool(name, toolset, schema, handler, check_fn=None, requires_env=None, is_async=False, description="", emoji="", override=False)`
- `register_command(name, handler, description="", args_hint="")` for `/name`
- `register_cli_command(name, help, setup_fn, handler_fn=None, description="")` for `hermes name`
- `register_hook(hook_name, callback)`
- `register_skill(name, path, description="")`
- `dispatch_tool(tool_name, args, **kwargs)`
- `profile_name`

Prefer `dispatch_tool()` over importing internal registries or agent objects. Built-in slash-command collisions are rejected. Replacing a built-in tool needs `override=True` plus operator opt-in at `plugins.entries.<id>.allow_tool_override`.

## Hook distinctions

Hermes has three hook systems:

- Plugin hooks: CLI + gateway, same-process Python.
- Gateway hooks: gateway only, `$HERMES_HOME/hooks/<name>/HOOK.yaml` + `handler.py`.
- Shell hooks: CLI + gateway, JSON stdin/stdout subprocesses configured under `hooks:` and protected by explicit consent.

Behavior-changing plugin hooks include `pre_tool_call`, `pre_llm_call`, `pre_verify`, `pre_gateway_dispatch`, and the transform hooks. Approval hooks are observers only. `pre_gateway_dispatch` runs before normal auth/pairing dispatch, so treat its input as untrusted.

Hook exceptions are isolated, but same-process plugin callbacks have no containment: they can hang, mutate process state, or read credentials. “Non-blocking” in prose means failures do not crash the pipeline, not that callbacks are async or time-bounded.

Shell-hook consent keys on exact command text, not script hash. Script edits remain trusted; `hermes hooks doctor` detects drift. Shell hooks run with full user credentials.

## Profiles and skills

Profiles provide separate `HERMES_HOME` state (config, credentials, sessions, skills, plugins, memory, cron), selected with `hermes -p <name>`. Do not use sticky `hermes profile use` for routine orchestration. Profiles are not filesystem sandboxes.

Plugin skills registered via `ctx.register_skill` are loaded as `plugin:skill`, do not enter the flat user skill tree, and are read-only through the plugin registry. External skill directories are read-only only to autonomous curation; foreground user-directed writes may still be possible.

## Terminal and process orchestration

Supported model-facing surface:

- `terminal(..., background=True, notify_on_complete=True)`
- `process(action=list|poll|log|wait|kill|write|submit|close, session_id=...)`

Treat `proc_*` IDs as opaque. `processes.json`, output-buffer sizes, recovery rules, and registry classes are implementation details. Gateway restart recovery only re-adopts valid local-host PIDs as detached processes; historical output/stdin state is not generally recoverable, and sandbox-local PIDs are not re-adopted.

`HERMES_SESSION_ID` is a documented subprocess correlation variable. It is distinct from `--pass-session-id`, which puts the ID into the model prompt.

## MCP

Use profile-local `mcp_servers` config, `tools.include`/`exclude`, and the runtime `mcp-<server>` toolset alias. Discover concrete tools via `/v1/toolsets`; do not hardcode generated MCP tool names.

Observed documentation drift at the audited snapshot:

- Docs showed `mcp_<server>_<tool>`.
- Source generated `mcp__<server>__<tool>`.

MCP stdio environment filtering reduces accidental leaks but is not containment. Configured commands remain arbitrary local code. The built-in suspicious-config scanner is intentionally a narrow abuse-shape filter, not a whitelist. Terminal-backend isolation does not contain MCP subprocesses.

## Kanban versus delegation

Kanban is the durable primitive: shared SQLite-backed boards, task dependencies/comments/runs, named-profile OS workers, model-facing `kanban_*` tools, human CLI/slash commands, and documented monitor endpoints. Worker destructive lifecycle calls are task-scoped; orchestrator-only list/unblock tools are hidden from task workers. DB schema, dispatcher locks, worker env layout, and metadata fields such as `worker_session_id` are implementation details.

Delegation creates fresh child-agent context and restricted toolsets, but remains process-local/transient. The audited docs described synchronous behavior while current source forced top-level model-originated delegation into background mode when the delivery surface supports it; direct Python calls retained synchronous default and stateless HTTP fell back to synchronous. Therefore do not build durable orchestration around delegation scheduling semantics; use Kanban.

## Sessions and programmatic control

Preferred external contracts:

- API server: `/v1/capabilities`, `/v1/runs/*`, `/api/sessions/*`, `/v1/skills`, `/v1/toolsets`.
- TUI JSON-RPC for tightly coupled hosts: `session.status`, `commands.catalog`, `command.dispatch`, `delegation.status`, `subagent.interrupt`, `approval.respond`.
- Headers: `X-Hermes-Session-Id` for transcript continuity and `X-Hermes-Session-Key` for stable channel/memory scope.

Treat session IDs as opaque even when a format is documented. `state.db` is canonical but its schema is not the preferred external write API. Do not construct gateway session keys manually; use supported protocol surfaces.

## Security and write boundaries

Official policy: the operating system is the only boundary against an adversarial LLM.

- Plugins, Python hooks, and skill code execute with full agent-process privileges.
- Terminal-backend isolation confines shell/file operations only, not plugins, hooks, MCP, or host-side code execution.
- Profiles, approvals, redaction, file guards, tool allowlists, Skills Guard, and MCP scanning are defense-in-depth heuristics.
- File tools hard-refuse selected system paths and direct Hermes config writes, but cross-profile guards are explicitly soft and the same-user terminal can bypass them.
- For untrusted inputs, use whole-process container/OS isolation plus authenticated/allowlisted network surfaces.

## Literal read-only audit pitfall

Some web extraction tools automatically persist large-page caches even when the analyst does not request a file. Under a literal “do not create files” constraint, prefer browser inspection or network reads that print to stdout. If a managed tool creates an automatic cache anyway, disclose the exact cache artifact separately from project/config mutations; do not delete it without permission.