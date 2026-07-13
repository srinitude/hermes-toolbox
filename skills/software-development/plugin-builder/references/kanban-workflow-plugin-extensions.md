# Kanban Workflow Plugin Extensions

Use this reference when a plugin-building request involves a Kanban workflow, multi-profile pipeline, phase worker, approval UI, side-effect sender, external integration, board automation, context bundles, or phase-gated work.

## Surface-Fit Rule

Prefer existing Hermes primitives before creating a plugin. Use this order by default:

1. **Profile distribution + config/toolsets** when the need is a role, lane, model, toolset, or shareable profile package.
2. **Skill guidance** when the need is reusable worker behavior, phase rules, or handoff instructions.
3. **MCP server** when the need is access to an external service that already has an MCP integration.
4. **Cron, gateway, dashboard, or CLI Kanban commands** when the need is scheduling, human control, or board operations without a new extension surface.
5. **Plugin** only when a new Hermes extension surface is actually needed: model-callable tools, slash commands, CLI commands, hooks, provider/backends, dashboard/provider integrations, or platform behavior.

This surface-fit check prevents a generated plugin from duplicating simpler profile-builder or skill primitives.

## Safe Plugin Roles in Kanban Workflows

A plugin can be a good fit when it provides one of these bounded roles:

- External side-effect sender with an explicit approval gate, e.g. a deployer, notifier, publisher, or domain-specific sender.
- Domain integration tool used by a phase worker, e.g. a design API, issue tracker, repo service, test environment, or artifact registry.
- Review/dashboard helper that surfaces board state through supported APIs without bypassing review.
- Model/provider/backend plugin when one phase genuinely requires a new inference, media, browser, web, TTS/STT, or memory backend.
- Slash/CLI command wrapper for a narrow workflow operation that humans trigger explicitly.

## Unsafe or Blocked Plugin Roles

Block or redesign any plugin proposal that would:

- make direct writes to `kanban.db` without first-party API support;
- invent unsupported lifecycle semantics, block kinds, workflow-template behavior, or tool arguments instead of checking the live CLI/schema;
- block a successful parent task when native dependency promotion requires that parent to reach `done`;
- let a model self-approve a side effect through a schema field such as `confirm: true`;
- claim universal enforcement over external CLI, dashboard, cron, scripts, or profiles/processes where the plugin is not loaded;
- copy profile `.env`, auth stores, sessions, logs, cache, `state.db*`, pairing state, or runtime files;
- read or print raw secrets;
- import heavy SDKs, construct clients, or make network calls at import/register time;
- use private Hermes internals instead of public registration APIs or approved CLI/tool surfaces;
- conflate source creation, consumer installation, candidate export, publication, or plugin approval.

## Kanban Contracts Plugins Must Preserve

Plugins that participate in a workflow must preserve these contracts:

- `work_key` identifies the stable work stream.
- `work_run` identifies the current attempt or pass.
- `context_bundle` carries compact handoff facts: summary, artifacts, decisions, risks, validation evidence, reviewer notes, and next-step requirements.
- Represent ordered phases as separate native tasks connected by supported dependencies unless a first-party workflow engine demonstrably owns the routing. Do not treat forward-compatible workflow fields as an active engine without source/runtime proof.
- Successful phase tasks call `kanban_complete`; dependent children promote only after the parent reaches `done`. Use a supported `needs_input`-style block before an approval-dependent action, then have an unscoped orchestrator perform any later unblock.
- Dispatcher-spawned phase workers receive lifecycle tools through `HERMES_KANBAN_TASK`. Do not grant persistent unscoped orchestration capabilities to phase profiles merely to make worker completion/block tools available.
- Task-scoped workers operate only their current task. Creation, linking, reassignment, remediation, and unblock decisions remain orchestrator-owned unless the live schema explicitly proves otherwise.
- Tool handlers return compact JSON strings, validate inputs, catch exceptions, accept `**kwargs`, and avoid printing secrets.
- Slash/CLI commands are human-triggered, reject unknown flags, resolve human labels to canonical handles, and never silently widen profile or board scope.

## Plugin Spec Additions

When a Kanban plugin is justified, add this compact section to the plugin spec:

```yaml
kanban_integration:
  workflow_role: side_effect_sender | phase_tool | review_helper | dashboard_helper | provider_backend | command_wrapper
  board_source_of_truth: hermes_kanban
  identifiers: [work_key, work_run]
  input_contract:
    required: [work_key, work_run]
    optional: [task_id, phase, context_bundle, reviewer_decision]
  output_contract:
    format: json_string
    fields: [ok, status, summary, artifacts, next_action, error]
  gates:
    human_approval_before_side_effects: true
    supported_block_kind: needs_input
    unblock_owner: unscoped_orchestrator
    model_tools_can_confirm: false
  forbidden_actions:
    - direct writes to `kanban.db`
    - model self-approval through tool arguments
    - caller-selected cross-profile targeting
    - secret printing
    - profile runtime state copying
  validation:
    - real PluginContext discovery/load
    - good-input handler test
    - bad-input and malformed-native-output tests
    - profile/board/task selector ambiguity tests
    - preview-token binding and single-use tests
    - nonzero native-command failure test
    - missing-env behavior
    - installed toolset visibility
    - no-write-outside-approved-path scan
```

## Public APIs and Runtime Contracts

Use supported public plugin APIs only:

- `ctx.register_tool(...)` for model-callable phase/domain tools.
- `ctx.register_command(...)` for slash commands.
- `ctx.register_cli_command(...)` for human CLI helpers.
- `ctx.register_hook(...)` only for fast, bounded event behavior.
- `ctx.register_skill(...)` to bundle read-only worker guidance.
- `ctx.dispatch_tool(...)` to compose existing tools from a slash command or handler.
- Specialized provider/backend APIs only when building a provider plugin.

Do not reach into private internals or assume a plugin can mutate the board by touching storage directly. If board mutation is needed, prefer existing Kanban CLI/tool surfaces or a documented first-party API.

### Registration and active-profile invariants

- Pass `ctx.register_skill()` a `pathlib.Path` to the actual `SKILL.md`, not a directory or string path. A permissive fake context can hide this error, so include one fresh-process real `PluginManager` load.
- Bind profile-local behavior to `ctx.profile_name`. Do not default named sessions from a caller argument or `HERMES_PROFILE`; reject cross-profile targeting unless the final agreement explicitly defines and approves an operator allowlist.
- Manifest `provides_*` fields are descriptive. Runtime `ctx.register_*` calls are authoritative; test the actual registry.
- After enablement, verify both `plugins list --json` and `tools list`. Discovery/enabled status alone does not prove a custom toolset is visible to the model.
- Long-running gateways and sessions may cache plugin discovery. Require a fresh session or an explicitly approved restart before claiming the new plugin is live there.

### Human confirmation for side effects

A boolean in a model-callable schema is not human approval. For side-effecting workflow actions:

1. Keep model-callable route/action tools permanently preview-only.
2. Resolve profile, Project, board, task, operation, and arguments before issuing a preview.
3. For a human slash command, issue a short-lived random token stored in process memory and bind it to a canonical fingerprint of the exact preview.
4. Require the same slash command with `--confirm <token>`; consume the token once, reject mismatch/reuse/expiry, and never issue confirmation tokens from model tools.
5. Execute through `ctx.dispatch_tool()` or an appropriate supported host tool so host approval/audit behavior remains available.
6. Treat nonzero exit, timeout, malformed output, or unsupported result shape as `ok: false`; stop subsequent commands.

For destructive exception paths such as archive/cancel, require a durable reason and document that cancellation is not successful lifecycle completion.

### Human selector and native-output discipline

- Bind every mutation to a canonical board; never silently use the current board.
- Resolve Project/board display names case-insensitively to canonical slugs and verify a Project's bound board when applicable.
- Resolve task titles across the intended board scope. Exact matches precede fuzzy matches; ambiguous choices include board, title, status, and assignee so labels are distinguishable.
- Reject unknown flags and value-less value flags before computing a mutation.
- Parse full native JSON before presentation truncation. Truncating first can turn valid large output into malformed JSON and tempt fail-open ID handling.
- Never reinterpret an unresolved human label as an internal task ID.
- When routing depends on current phase, verify the native task assignee/run evidence and reject caller claims that contradict it.

### Hook scope

A global `pre_tool_call` hook can easily overreach. Restrict it to exact tool fields and mutation signals: target paths for file writers, code text for code execution, and command text for terminal. Do not scan an entire serialized payload and block harmless read-only diagnostics merely because documentation or content mentions `state.db`, logs, or cache. A separate system-wide runtime-store policy requires its own explicit approval.

## Performance Rules

Kanban worker profiles are already prompt-sensitive. Plugins should protect speed and cost:

- keep schemas minimal and descriptions short;
- lazy-load optional dependencies;
- avoid network work at import/register time;
- set timeouts for external calls;
- cache stable metadata;
- keep handler output compact;
- prefer one focused tool over many overlapping tools;
- reserve LLM calls inside plugins for cases where a normal agent turn cannot do the work.

## Routing and Privacy

Apply `references/plugin-profile-routing.md` before selecting a target path:

- User-specific/private plugins route through the deployment-configured private workshop and apply its private prefix when configured.
- Reusable/public plugins route through the configured public plugin source workshop and keep docs/examples identity-neutral.
- Downstream inclusion in a Kanban worker profile is a later, separate approval step.
- Never copy plugin secrets or runtime state into a profile distribution.

## Profile-Bundle Install Surface-Fit

When installing or validating a Kanban workflow bundle, do not create or install plugins merely because `/plugin-builder` is mentioned. First scan the source for plugin markers such as `plugin.yaml`, `plugin.yml`, plugin package directories, or explicit plugin contracts. If the bundle consists only of profile distributions, configs, SOUL files, READMEs, and bundled skills, record the plugin-builder decision as: profile distributions plus bundled skills are the correct surface; no plugin installation is required. Only proceed to a plugin spec when a concrete new extension surface is present and approved.

## Validation Ledger

Before final plugin agreement, prove or surface blockers for:

- surface-fit: why plugin is better than profile/config/skill/MCP/cron/gateway;
- manifest fields and `requires_env` declarations;
- public registration APIs chosen, including a real `PluginContext`/`PluginManager` probe;
- host-bound active-profile behavior and cross-profile rejection;
- handler JSON/error contract, malformed/large native output, timeout, and nonzero exit handling;
- human selectors, ambiguity choices, canonical board binding, and unknown-flag rejection;
- permanent model-tool dry-run behavior plus exact-token human confirmation for side effects;
- native dependency semantics: successful parents reach `done`, phase workers do not assume orchestrator-only tools, and loop-backs explicitly unblock when required;
- preservation of `work_key`, `work_run`, `context_bundle`, HITL, and supported approval gates;
- plugin-profile routing, target write path, atomic staged replacement, and rollback evidence;
- no secrets/runtime-state copying or generated cache drift;
- discovery/load, enabled config, source/install hash equality, and plugin toolset visibility in every approved consumer profile;
- source-profile automation preflight so candidate export/publication does not occur without separate approval.

The final report must separate plugin-local guarantees from first-party/core guarantees. If external CLI/dashboard/cron/scripts remain bypass surfaces, mark universal enforcement partial rather than implying the hook protects processes it cannot observe.

## Source Coverage Summary

This reference incorporates reusable plugin implications from the workflow package's top-level docs, safe installer, profile configs, phase READMEs, phase identities, distribution manifests, and phase worker skills. It intentionally does not copy the workflow package: it converts those files into plugin-builder decisions about extension-surface fit, side effects, routing, runtime contracts, and validation.
