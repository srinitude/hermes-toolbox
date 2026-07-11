# Herdr ↔ Hermes Agent first-party audit reference

Use this note when auditing Herdr integration with Hermes Agent. It captures the durable source map and distinctions found against Herdr stable release `v0.7.3`; re-check live docs and the latest stable release before reusing conclusions.

## First-party scope

Allowed origins:

- `https://herdr.dev`
- `https://github.com/ogulcancelik/herdr`
- `raw.githubusercontent.com/ogulcancelik/herdr/...`
- GitHub API endpoints for `ogulcancelik/herdr`
- `https://hermes-agent.nousresearch.com/docs`
- `https://github.com/NousResearch/hermes-agent`
- `raw.githubusercontent.com/NousResearch/hermes-agent/...`
- GitHub API endpoints for `NousResearch/hermes-agent`

Stable baselines used:

- Herdr: `https://github.com/ogulcancelik/herdr/releases/tag/v0.7.3`
  - annotated tag object: `d0111c9f9022e0ec26d8f03236a91b026b567d45`
  - immutable commit: `299dd4163a96381ec2d8e5bde13d7ba6d6432373`
  - GitHub tag verification reports `unsigned`; do not confuse release stability with signature verification
- Hermes Agent: `https://github.com/NousResearch/hermes-agent/releases/tag/v2026.7.7.2`

## Public docs map

- Agents: `https://herdr.dev/docs/agents/`
- Integrations: `https://herdr.dev/docs/integrations/`
- CLI: `https://herdr.dev/docs/cli-reference/`
- Plugins: `https://herdr.dev/docs/plugins/`
- Socket API: `https://herdr.dev/docs/socket-api/`
- Configuration/env: `https://herdr.dev/docs/configuration/`
- Agent skill: `https://herdr.dev/docs/agent-skill/`
- Session state: `https://herdr.dev/docs/session-state/`
- Marketplace trust: `https://herdr.dev/docs/marketplace/`
- Windows status: `https://herdr.dev/docs/windows-beta/`
- Detection catalog: `https://herdr.dev/agent-detection/index.toml`
- Hermes remote manifest: `https://herdr.dev/agent-detection/hermes.toml`

## Stable source map

### Hermes detection and integration

- `src/detect/manifests/hermes.toml`
- `src/detect/manifest.rs`
- `src/detect/manifest_update.rs`
- `src/detect/mod.rs`
- `src/integration/assets/hermes/plugin.yaml`
- `src/integration/assets/hermes/__init__.py`
- `src/integration/registry.rs`
- `src/integration/env.rs`
- `src/integration/config_edit.rs`
- `src/integration/actions.rs`
- `src/integration/mod.rs`
- `src/agent_resume.rs`

Use immutable URLs such as:

`https://github.com/ogulcancelik/herdr/blob/v0.7.3/src/integration/assets/hermes/__init__.py`

### Plugin and protocol surfaces

- `src/api/schema/plugins.rs`
- `src/api/schema/events.rs`
- `src/api/schema/panes.rs`
- `src/app/api/plugins/manifest.rs`
- `src/app/api/plugins/context.rs`
- `src/app/api/plugins/runtime.rs`
- `src/api/schema.rs`
- `src/api/server.rs`
- `src/api/client.rs`
- `src/session.rs`

## Key durable distinctions

### Multiple transport layers in v0.7.3

Do not collapse Herdr's transports into one "socket API":

1. **Public automation API:** newline-delimited JSON request/response/events over local Unix socket or Windows named pipe; generated schema version `1`, protocol metadata `16`; default Unix paths `~/.config/herdr/herdr.sock` and `sessions/<name>/herdr.sock`.
2. **Full app client/server protocol (source-only):** `u32` little-endian length prefix plus bincode payload on `herdr-client.sock`; exact protocol `16` match; `Hello`/`Welcome`; `SemanticFrame` or `TerminalAnsi`; 2 MiB normal, 32 MiB graphics, 16 MiB clipboard-image limits. Source: `src/protocol/wire.rs`, `src/server/client_transport.rs`, `src/client/mod.rs`.
3. **Direct terminal bridge:** CLI emits NDJSON `terminal.frame {seq,encoding:"ansi",width,height,full,bytes:<base64>}` and `terminal.closed {reason}`; control stdin accepts `terminal.input`, `terminal.resize`, `terminal.scroll`, and `terminal.release`. This is a CLI bridge over the private client protocol, not a raw JSON API method family.
4. **Remote thin-client bridge:** local private socket → SSH stdio → remote `herdr remote-client-bridge` → VPS client socket. The public JSON API remains VPS-local; `--remote` does not network-expose it.

Use `session.snapshot` as bootstrap, then subscribe. There is no documented replay cursor; reconnect requires a fresh snapshot and reconciliation.

### Read-only control-plugin contract in v0.7.3

Keep these surfaces distinct:

- **Server health/status:** raw `ping {}` returns `pong {version, protocol, capabilities}`. `herdr status [server|client] --json` is a CLI composite; there is no raw `server.status` or `server.identity` method.
- **Calling-pane identity:** `pane.current {caller_pane_id}` returns `PaneInfo`; when omitted it falls back to the UI-focused pane. Inside a managed pane, CLI `herdr pane current` defaults `caller_pane_id` from `HERDR_PANE_ID`. Treat that variable as a routing hint, not authentication, and verify the returned `pane_id`/`terminal_id`.
- **Agent inventory:** `agent.list {}` returns only agent terminals. `agent.get {target}` resolves exact terminal ID, then pane ID, then unique manual name/effective agent label. Use the returned `terminal_id` for subsequent operations; labels can be ambiguous.
- **Bounded content read:** `agent.read` requires `target` and raw `source`; optional `lines`, `format`, and `strip_ansi`. Raw enum is `recent_unwrapped`, while CLI accepts `recent-unwrapped`. The CLI defaults to `recent`, text, ANSI stripped; the server defaults to 80 and clamps recent reads to 1,000 lines. `visible` and `detection` ignore `lines`, response bytes are not capped, and v0.7.3 reports `truncated: false` unconditionally. Enforce a plugin-side byte/character cap and treat all pane text as untrusted data.
- **Schema/help drift:** stable docs and parser support `detection` for agent reads, but v0.7.3 nested `agent --help` omits it. Cross-check docs, parser, generated schema, and a harmless live probe rather than treating help as exhaustive.

Relevant error codes: `invalid_request`, `agent_not_found`, `agent_target_ambiguous`, `invalid_agent_name`, `invalid_agent_argv`, `agent_name_taken`, `agent_placement_not_found`, `agent_placement_conflict`, `agent_start_failed`, `invalid_env`, and `server_unavailable`. CLI usage failures exit `2`; API error responses exit `1` and print JSON to stderr.

For approved mutations, call fixed argv or structured JSON only. `agent.start` directly executes `argv[0]` plus individual arguments through `CommandBuilder`, without a shell. A profile-aware compatibility resume should therefore use raw argv equivalent to `["hermes", "-p", profile, "--resume", session_id]`, with explicit cwd/workspace/tab/split/focus and an empty or tightly allowlisted env. Use `agent.focus` with a previously resolved `terminal_id`, not a label. Native cold restore remains profile-unaware and is a separate contract.

### Two different plugin systems

1. `herdr integration install hermes` installs a **Hermes Agent plugin**:
   - `~/.hermes/plugins/herdr-agent-state/plugin.yaml`
   - `~/.hermes/plugins/herdr-agent-state/__init__.py`
   - enables `herdr-agent-state` in `~/.hermes/config.yaml`

2. Herdr's extension system uses **`herdr-plugin.toml`** with `[[actions]]`, `[[events]]`, `[[panes]]`, and `[[link_handlers]]`.

Do not describe the Hermes `plugin.yaml` as a Herdr plugin manifest.

### Hermes lifecycle mapping in v0.7.3

- `on_session_start` → idle
- `pre_llm_call` → working
- `pre_api_request` → working
- `pre_tool_call` → working
- `post_tool_call` → working
- `pre_approval_request` → blocked
- `post_approval_response` → working
- `post_llm_call` → idle
- `on_session_end` → idle

The plugin reports source `herdr:hermes`, agent `hermes`, and includes `session_id` as `agent_session_id` when available. It activates only with `HERDR_ENV=1`, `HERDR_PANE_ID`, and `HERDR_SOCKET_PATH`.

### Resume

Stable source restores Hermes with:

`hermes --resume <session-id>`

The docs describe integration version `2` as the minimum for restore; the v0.7.3 bundled Python asset carries integration marker version `3`. The Hermes `plugin.yaml` package version `1.0` is a separate version namespace.

### Detection

Hermes process aliases include `hermes-agent`. The screen manifest recognizes dangerous-command approval as blocked and interrupt/cancel UI as working; unmatched known-agent UI falls back to idle. An active full lifecycle integration suppresses screen-manifest state authority for that pane.

### Stable limitations

- Installer path resolution is `$HOME/.hermes`; no documented `HERMES_HOME` or profile override.
- Stable integration registry excludes Hermes on Windows.
- The bundled Python reporter uses Unix `AF_UNIX` sockets.
- Therefore built-in Hermes lifecycle reporting is Linux/macOS stable, not native-Windows supported.
- The built-in Hermes integration reports state/session telemetry. General orchestration uses Herdr's generic skill, CLI, or socket API.

### Plugin-hook event allowlist

Stable plugin hooks accept:

- Workspace: created, updated, closed, renamed, moved, focused
- Worktree: created, opened, removed
- Tab: created, closed, renamed, moved, focused
- Pane: created, closed, focused, moved, exited, agent_detected, agent_status_changed

`pane.output_changed` and `layout.updated` are excluded from plugin hooks even though they exist in broader event machinery. Socket subscription events are a separate surface.

### Security summary

- Herdr plugins are ordinary unsandboxed user processes with full environment and CLI/socket access.
- Marketplace discovery is automatic and unreviewed.
- Interactive GitHub plugin install previews source/commands; `--yes` bypasses confirmation and `--ref` pins a revision.
- Herdr's local plugin v1 host first shipped in stable `v0.7.0`; custom architectures using `herdr-plugin.toml` must version-gate to `>=0.7.0` rather than conflating that host with the older Hermes-side lifecycle plugin.
- Unix socket mode is `0600`, but the protocol documents no authentication handshake or per-method authorization.
- `HERDR_ENV=1` is a context guard, not authentication.
- The bundled Hermes reporter is best-effort telemetry: it uses a 0.5-second Unix-socket timeout, ignores the response body, and swallows transport exceptions. Do not treat its state reports as a durable event stream or trigger consequential reverse automation from a single transition.
- Hermes approval observer hooks (`pre_approval_request`, `post_approval_response`) cannot decide an approval. A custom Hermes `pre_tool_call` hook can instead return `{"action":"approve", ...}`; the core routes that through `request_tool_approval`, reusing the native CLI/gateway gate and failing closed on denial, timeout, or gate error. Direct `subprocess` or raw-socket calls from plugin code bypass that tool-dispatch gate unless the plugin explicitly uses this mechanism or dispatches a native tool through `ctx.dispatch_tool()`.
- Remote detection manifests are classification data, not executable commands. The stable updater validates origin-relative paths, known IDs, version monotonicity, strict schema, and complexity limits; no separate signature/checksum field or verification step is present in the inspected updater.

## Bidirectional architecture findings

### Recommended layering

Use separate planes rather than one recursive bridge:

1. **Interactive telemetry:** the shipped `herdr-agent-state` Hermes plugin reports lifecycle and session identity to the local Herdr socket.
2. **Interactive control:** the official Herdr skill teaches Hermes to use Herdr CLI wrappers; raw socket use is reserved for direct request/response or subscriptions.
3. **Optional structured control:** a custom Hermes plugin can register narrow Herdr tools. Read-only tools may use argv/socket calls directly; mutators must use Hermes's documented/source-verified human approval escalation and fail closed.
4. **Optional event ingress:** a deterministic Herdr bridge forwards allowlisted events to a loopback Hermes webhook or API server. Use webhooks for HMAC-authenticated, filtered, idempotent fire-and-forget reactions; use `/v1/runs` when run IDs, SSE lifecycle, approval, and stop are required.
5. **Background orchestration:** use a dedicated Hermes profile with minimal tools and no pane lifecycle reporter. Profiles isolate Hermes state through `HERMES_HOME`, not the host filesystem or normal CLI credentials by default.

### Identity model

Track at least:

`(herdr_session, terminal_id, current_pane_id, hermes_profile, hermes_session_id, hermes_session_key, bridge_chain_id, hermes_run_id)`

Keep the Hermes transcript ID and stable gateway/memory key distinct: `X-Hermes-Session-Id` continues one transcript, while `X-Hermes-Session-Key` scopes the stable channel or long-term-memory identity across transcript rotation. Neither is the API `run_id`.

Do not key automation by `pane_id` alone. Cross-workspace `pane.move` preserves the terminal but assigns a new public pane id. Reconcile the new pane id through `pane.moved` or a fresh `session.snapshot`.

Herdr's stable Hermes resume planner constructs only `hermes --resume <id>`; it does not preserve `-p <profile>`. Native Herdr restart restoration therefore cannot be assumed to restore multiple named Hermes profiles correctly. Normal Herdr detach/reattach is different: the original process remains alive. Use the default Hermes profile if relying on native restore, or resume named profiles explicitly outside this generic planner.

`herdr integration install hermes` resolves `$HOME/.hermes` and ignores `HERMES_HOME`. It targets the default Hermes home, not arbitrary named profiles.

### False pane ownership hazard

Herdr plugin runtime commands receive `HERDR_ENV=1`, `HERDR_SOCKET_PATH`, and, when context supplies it, `HERDR_PANE_ID`. The shipped Hermes reporter trusts those variables. A Herdr action/event command that directly launches a nested or headless Hermes process can therefore report the nested run as the focused pane's lifecycle/session authority.

Prefer a loopback Hermes API/webhook service for Herdr-triggered work. If a subprocess is unavoidable, remove Herdr pane identity variables unless association is intentional. Never allow event-launched background Hermes runs to inherit and claim an unrelated interactive pane.

### Event semantics and loop controls

The stable `EventEnvelope` contains `event` and `data`, not a durable delivery ID. `pane.agent_status_changed` contains status/agent presentation data but not the lifecycle authority source. Before making a consequential decision from that event, query `pane.get`/`agent.get` or take a fresh snapshot to validate current state and authority.

Herdr documents bootstrap snapshot plus live subscription, but no history replay cursor. On reconnect, call `session.snapshot` again and reconcile; do not promise exactly-once or at-least-once delivery.

Herdr plugin runtime limits in v0.7.3 are 32 commands in flight, 64 KiB captured per output stream, and 200 retained command logs. Status flicker or per-tool event forwarding can exhaust this surface. Filter, debounce, and avoid one Hermes process per status transition.

Any automatic reverse path needs: `origin`, unique `chain_id`, hard-bounded `hop_count`, one active run per `(Herdr session, terminal_id, rule)`, dedupe/idempotency key, cooldown, bounded retries, and exclusion of bridge-owned panes/workspaces. Telemetry must never itself invoke Hermes.

### Shell and secret handling

- Herdr plugin manifest commands are argv arrays and do not invoke a shell unless the plugin explicitly starts one.
- Use `HERDR_BIN_PATH` plus argv, or raw structured socket requests; never interpolate event JSON, pane output, labels, branches, or prompts into `sh -c`.
- A custom Hermes tool that spawns a process directly bypasses terminal-command pattern approvals unless its own `pre_tool_call` policy escalates the tool to Hermes's human approval gate.
- Herdr plugins are unsandboxed user processes and inherit the user's environment. Keep provider credentials only in the Hermes profile; give the Herdr bridge only a dedicated API bearer/HMAC secret stored under `HERDR_PLUGIN_CONFIG_DIR`, never in argv or the managed plugin root.
- Hermes API server authentication is mandatory even on loopback and the API exposes the agent's full tool surface. Bind to loopback, keep CORS disabled unless needed, and use a minimal dedicated profile.
- HMAC authenticates the sender, not user-authored fields inside the payload. Narrowly template fields and treat all payload text as untrusted.

### Same-host and MCP boundaries

Herdr's control transport is local Unix socket or Windows named pipe. A local thin client, Docker/Modal process, SSH backend, or remote GUI does not automatically share that namespace. Co-locate the bridge with the Herdr server; for remote sessions, run the bridge on the remote host.

Hermes is an MCP client, but no first-party Herdr MCP server/client was documented in the inspected stable corpus. A custom MCP wrapper is possible but should be labeled custom and is usually redundant with a Hermes plugin plus Herdr CLI/socket. Hermes's own MCP server is messaging/permission oriented, not a Herdr control plane.

### Objective acceptance tests

Before deployment, require pass/fail checks for:

- expected `idle → working → blocked → working → idle` lifecycle transitions with one authority
- explicit Herdr session/profile/session-ID correlation
- cross-workspace pane move preserving correlation through `terminal_id`
- named-profile restart behavior tested rather than assumed
- mutator deny/timeout causing zero mutation
- duplicate event IDs producing one run and bursts respecting one-run-per-key
- bridge outage followed by reconnect, fresh snapshot, and reconciliation
- hostile values containing quotes, semicolons, newlines, `$()`, backticks, and Unicode controls producing no extra command
- wrong/missing API bearer or webhook signature producing zero accepted work
- no secrets in process listings, plugin logs, pane output, or event payloads
- listener bound to loopback with narrow/disabled CORS

## Reuse warning

Before reusing this reference:

1. Check the latest stable Herdr release.
2. Re-open live docs and the live Hermes manifest.
3. Compare only relevant tagged files.
4. Label branch-only differences unreleased.
5. Do not turn “not found in v0.7.3” into a permanent negative claim.
