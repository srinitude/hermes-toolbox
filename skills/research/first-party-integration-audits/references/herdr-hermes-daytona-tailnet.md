# Herdr–Hermes–Daytona Tailnet integration audit

Use this reference when planning a no-upstream-change control plane where Herdr clients run on local computers, Herdr/Hermes processes run on a VPS, and Daytona sandboxes optionally join the same Tailscale network.

Revalidate all live releases, docs, installed versions, organization tier, and host inventory before reuse. The findings below were checked on 2026-07-11 against Herdr `v0.7.3`, Hermes Agent `v2026.7.7.2`, and Daytona `v0.190.0`.

## First-party sources

- Herdr docs/repo: `https://herdr.dev/docs/`, `https://github.com/ogulcancelik/herdr`
- Hermes docs/repo: `https://hermes-agent.nousresearch.com/docs/`, `https://github.com/NousResearch/hermes-agent`
- Daytona docs/repo: `https://www.daytona.io/docs/en/`, `https://github.com/daytonaio/daytona`
- Tailscale security/auth policy: `https://tailscale.com/kb/`

Pin stable tags through GitHub `releases/latest`, dereference annotated tags to immutable commits, and treat live docs/default-branch material as a separate current-contract or unreleased axis.

## Correct topology

- The VPS is the process/control host. Its Herdr server owns PTYs, workspaces, tabs, panes, layouts, and interactive agent processes.
- Local computers run Herdr thin clients over SSH on the tailnet: `herdr --remote <vps-alias> --session <name>`.
- The Herdr public automation socket remains VPS-local. `--remote` is a terminal client bridge; it does not expose that socket over the tailnet.
- Named Hermes profiles run on the VPS with explicit `hermes -p <profile>`. Profiles own config, credentials, sessions, memory, skills, plugins, cron, and gateway state; they are not filesystem or process sandboxes.
- Daytona is controlled first through its official CLI/MCP. A sandbox is a separate execution/GUI host, not a Herdr pane or Hermes profile.
- VNC renders in a browser. A Herdr pane can host control/status/SSH and display a URL, but it is not a VNC renderer.

## Primitive ownership rule

For “complete integration” requests, map primitive families by ownership rather than inventing one-to-one equivalence:

- Hermes profile ↔ explicitly launched agent process plus profile metadata.
- Hermes Project/cwd/repo ↔ Herdr workspace/worktree, with distinct IDs.
- Hermes conversation session ↔ Herdr pane agent-session reference plus profile identity.
- Hermes terminal/process approval path ↔ model-called shell operations; Herdr owns human-interactive PTY input.
- Hermes delegation stays transient/in-process unless a full visible agent process is intentionally launched in a pane.
- Hermes Kanban remains the durable queue authority; Herdr visualizes workers/tasks but never mirrors or writes its DB internals.
- Hermes goal/todo/memory/cron/gateway/checkpoints remain Hermes-owned; Herdr may show bounded status only.
- Herdr session/workspace/tab/pane/layout/client modes remain Herdr-owned; do not recast them as profile/session primitives.
- Hermes and Herdr plugin systems are distinct trusted-code surfaces joined through documented CLI/socket/API contracts.

Every family should be classified as directly mapped, observed, adapted through a narrow compatibility layer, intentionally separate, or not evidenced.

## Named-profile restore is the critical invariant

Herdr `v0.7.3` has an incomplete invariant chain for named Hermes profiles:

1. The built-in installer targets OS-home `~/.hermes` rather than arbitrary profile `HERMES_HOME`.
2. The bundled reporter emits `agent_session_id` but not `ctx.profile_name`.
3. Herdr snapshots store agent session and launch argv, but no typed Hermes profile field.
4. The resume planner builds `hermes --resume <id>` without `-p <profile>`.

Normal detach/reattach keeps the original PTY and profile. A true Herdr server restart reconstructs processes and is different.

Until every link is fixed in a later release, a shared multi-profile session must either disable native agent restore or use a separately reviewed compatibility layer that:

- records `(Herdr session, terminal/current pane, cwd/layout, Hermes profile, Hermes session ID)` only;
- validates profile existence and ambiguity;
- restores via structured argv equivalent to `hermes -p <profile> --resume <id>`;
- fails visibly to a shell/warning on missing, duplicate, or stale identity;
- never falls back silently to the sticky default profile.

The official Herdr lifecycle plugin must remain the sole lifecycle authority. A supplemental Hermes plugin may report profile metadata or expose narrow tools, but must not compete with `pane.report_agent` lifecycle state.

## Recommended extension layering

1. Install current official Herdr integrations for each actively used agent.
2. Install the pinned official Herdr skill in each intended Hermes profile.
3. Use a dedicated private Hermes orchestrator profile for topology and sandbox control.
4. Configure the official Daytona MCP (`daytona mcp start`) before writing custom Daytona code.
5. If needed, create a generic user-local Hermes plugin with bounded read tools plus preview/token/confirm mutators.
6. If needed, create a Herdr plugin with argv actions/events/terminal panes/link handlers and a bounded identity ledger.
7. Keep private hostnames, tailnet policy, profile selections, and credentials in private profile/config state; generic plugin code can remain identity-neutral.

Source creation, consumer installation, enablement, restart, tailnet policy, paid provisioning, and publication are separate approval gates.

## Daytona and Tailscale gate

Daytona tagged documentation states that connecting a sandbox to a VPN provider such as Tailscale requires organization Tier 3 or higher. Current limits documentation described Tier 3 as requiring a `$500` top-up. Therefore:

- Query the live organization tier and wallet before recommending provisioning.
- Separate the fixed/top-up requirement from CPU/RAM/disk usage charges.
- Require an explicit spend cap before top-up, create/start, VM/GPU, snapshot, public/signed preview, or other billable actions.
- If Tier 3 is unavailable, Daytona SSH and authenticated/signed previews may be usable fallbacks, but they do not satisfy a same-tailnet acceptance criterion.

For an approved tailnet join, prefer an ephemeral tagged node and short-lived/reusable auth flow scoped by ACLs. Never expose a broad personal auth key to the model, pane output, argv, logs, or plugin state. Prove node cleanup after sandbox deletion.

## Computer use and VNC

Daytona `v0.190.0` tagged docs supported Computer Use on Linux and Windows and described macOS as private alpha. Default Linux images include the normal Xvfb/XFCE/x11vnc/noVNC stack.

Acceptance must distinguish:

- control/status/SSH in Herdr panes;
- browser VNC viewing on the local computer;
- programmatic computer-use calls through Daytona MCP/SDK;
- one-controller ownership;
- human approval for click/type/drag mutations;
- prohibition on password, API-key, payment, 2FA, passkey, and permission-dialog automation.

## Event and trust controls

Herdr snapshot+subscribe has no documented durable replay cursor. On connect/reconnect: acknowledge subscription, buffer events, fetch a fresh snapshot on another connection, replace local state, then apply buffered events idempotently.

Every reverse automation path needs `origin`, `chain_id`, bounded `hop_count`, dedupe key, per-identity concurrency lock, cooldown, bounded retries, and bridge-owned-resource exclusion. Telemetry must never itself spawn Hermes.

Do not expose arbitrary `pane.run`, `pane.send_text`, or `agent.send` as normal model tools. Use fixed argv/structured requests, separate reads from mutators, and require exact-operation human confirmation. Treat pane output and authenticated payload fields as untrusted content.

## Read-only planning preflight

Before planning fleet integration, capture without mutation:

- live time/date;
- latest stable tags and immutable commits;
- installed Hermes/Herdr/Daytona/agent versions;
- active Hermes/Herdr/gateway/test/backup/publisher processes;
- Hermes profile list and status;
- Herdr client/server/protocol/session/integration status;
- tailnet peers and reachability;
- per-local-computer OS/architecture/package-manager/Herdr version via existing verified SSH only.

If active writers or publisher automation are found, make quiescence and downstream-publication checks a hard prerequisite before upgrades or plugin-source writes.

## Minimum adversarial acceptance matrix

- Three client hosts attach/detach/reconnect with matching Herdr protocol.
- Default plus two named Hermes profiles maintain correct lifecycle and profile/session identity.
- True server restart never resumes under the wrong profile.
- Sticky-profile changes, deleted profiles, duplicate session IDs, and stale IDs fail visibly.
- Cross-workspace pane moves either preserve reporter binding or remain unsupported.
- Wrong/missing bearer/HMAC/auth key/confirmation token causes zero mutation.
- Deny/timeout/replay/state-change causes zero mutation.
- Quote/newline/semicolon/backtick/`$()`/ANSI/Unicode-control payloads create no extra command.
- Event outage reconnects through fresh snapshot and reconciliation without exactly-once claims.
- No secret appears in argv, process lists, Herdr/Hermes logs, pane history, event payloads, ledgers, or durable memory.
- Approved Daytona sandbox respects resource/spend/auto-stop/archive/delete policy.
- If same-tailnet is claimed, tagged ephemeral node connectivity, ACL denial, and teardown are proven.
- VNC and computer use operate on the same private sandbox desktop with one controller and approval-gated mutation.

## Reuse warning

These are version-specific findings. Re-run the complete profile-aware restore chain and Daytona Tier/VPN contract against the latest stable releases before carrying any limitation or cost forward.
