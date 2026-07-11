# Hermes Agent v2026.7.7.2 integration map

Session-specific reference from a first-party-only, read-only audit. Revalidate against the selected stable release before reuse.

## Immutable baseline

- Release: `v2026.7.7.2`
- Commit: `9de9c25f620ff7f1ce0fd5457d596052d5159596`
- Annotated tag object: `b7751df34688835a108e0d630f3495fc11f3df79`
- Official repo: `https://github.com/NousResearch/hermes-agent`
- Raw base: `https://raw.githubusercontent.com/NousResearch/hermes-agent/v2026.7.7.2/`

## Recommended no-core-change boundary

Hermes owns profiles/HERMES_HOME, credentials, sessions, memory, skills, goals, todo hydration, terminal/process state, Kanban, cron, webhooks, checkpoints, and approvals. An external control plane should keep only opaque Hermes IDs and use documented CLI/API/MCP/webhook/plugin surfaces. Never read or mutate `state.db`, `sessions.json`, `kanban.db`, `jobs.json`, `processes.json`, profile `.env`, or snapshot/checkpoint internals directly.

Preferred integration order:

1. External service exposes an MCP server to Hermes.
2. External service consumes `hermes mcp serve` over local/SSH stdio for conversation events, messages, attachments, channels, and approval list/respond.
3. Signed native webhooks for event-driven ingress.
4. Kanban CLI `--json` or authenticated dashboard REST/WS for durable jobs.
5. Profile-local plugin for tools, hooks, `/commands`, CLI subcommands, dashboard routes, auth, or a gateway platform.
6. Authenticated Desktop/dashboard remote backend for operators.
7. OpenAI-compatible API for stateless request/response; ACP for IDE sessions.

## Ownership and identity rules

Keep these identities separate: OS process, Hermes profile, project/workspace, conversation session, gateway session key, terminal process (`proc_*`), delegated child, Kanban board/task/run, cron job, and external correlation chain. Profiles isolate Hermes state but do not sandbox the filesystem or necessarily external CLI credentials. `terminal.home_mode: profile` is required for profile-local subprocess HOME; workspace comes from `terminal.cwd`/Project/task workdir and is a separate concept.

## High-value primitive distinctions

- **Todo:** per-agent/session in-memory planning state, hydrated from transcript and reinjected after compression; not a durable queue.
- **Goal:** persistent session control state with judge-driven continuation and wait barriers; invoke through commands, never edit state metadata.
- **Delegation:** fresh child context and restricted tools, but process-local/transient; not durable orchestration.
- **Kanban:** durable, single-host, named-profile work queue with runs, comments, dependencies, retries, human blocks, and gateway dispatcher.
- **Background terminal process:** tracked shell process; completion delivery requires a persistent channel. Stateless HTTP must poll/wait.
- **`/background`:** isolated gateway agent run with result delivered to the originating chat; not a durable cross-process queue.
- **Cron:** gateway-owned scheduled fresh sessions or no-agent scripts; not a substitute for cross-host orchestration ownership.
- **Checkpoints:** opt-in project filesystem safety snapshots; not profile backups.
- **State snapshots:** source-visible quick-state mechanism without an equally clear release-tagged public contract; treat layout as internal and prefer documented profile export/import or backup commands.

## Document/source discrepancies found inside the tag

### Delegation

The tagged delegation guide describes `delegate_task` as synchronous fork/join. Tagged `tools/delegate_tool.py` makes top-level model-facing calls background work on persistent delivery surfaces, reinjects completion, falls back to synchronous on stateless HTTP, and keeps direct Python callers historically synchronous. Do not depend on timing or internal delegation handles; use Kanban for durability.

The guide/tool schema says each child has its own terminal session, while tagged terminal source collapses ordinary child task IDs into the shared default long-lived sandbox unless an explicit isolation override is registered. Treat child conversational isolation as real, but do not infer filesystem/container isolation.

### Dashboard plugin authentication

Tagged prose says plugin API routes bypass auth because the dashboard binds to localhost. Tagged `hermes_cli/web_server.py` and `dashboard_auth/middleware.py` require the loopback ephemeral token or the remote cookie/bearer gate for `/api/plugins/*`, with auth intentionally evaluated before plugin enablement. Report both support prose and actual release behavior; integrations must authenticate and remain version-pinned.

### Profile builder

`docs/design/profile-builder.md` is explicitly a design proposal marked not implemented. Supported creation remains `profile create` with clone/clone-all/clone-from/description/no-skills plus existing dashboard creation fields. Never promote proposal request bodies to shipped API.

## Security reminders

- Dashboard can edit secrets and run agent commands. Remote binds must use the fail-closed OAuth/OIDC/basic/custom-auth gate; `--insecure` is not an internet-facing option.
- Webhook HMAC authenticates the sender, not business-field text. Narrow prompts and toolsets and keep approvals/sandboxing enabled.
- MCP and plugins execute trusted code outside terminal-backend containment. Filter tools and stdio environment; use whole-process isolation for adversarial inputs.
- Dashboard auth provider hooks and token-authable routes are the supported machine-auth extension seam; do not invent bearer acceptance on arbitrary endpoints.
- Kanban is single-host and uses host-local worker/PID assumptions. Tenants are soft filters; boards are the hard queue boundary.

## Read-only audit lesson

Budget stdout before streaming large pages. Hermes may spill oversized terminal output to `/tmp/hermes-results/`, which violates a literal zero-file-creation interpretation even when `curl` writes only to stdout. Emit headings, compact parsed inventories, selected ranges, and byte/line-counted excerpts. Disclose any tool-managed spill separately and do not delete it without permission.
