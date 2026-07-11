# Herdr–Hermes profile-aware restore audit

Use this reference only after pinning current releases again. The findings below were verified against Herdr `v0.7.3` and Hermes Agent `v2026.7.7.2`; they are not permanent claims about later versions.

## Why this deserves a separate contract check

A lifecycle integration can correctly report an agent session while still being unable to restore the owning **profile**. Audit conversation identity and profile identity separately. A generic resume command is unsafe whenever the integrated agent stores sessions under isolated homes.

## Exact invariant chain to verify

For Herdr `v0.7.3` + Hermes Agent `v2026.7.7.2`, tagged source established all of these:

1. `src/integration/env.rs::hermes_dir()` resolves OS-home `~/.hermes`; it does not consult `HERMES_HOME`.
2. `src/integration/targets.rs` installs/enables `herdr-agent-state` in that root home.
3. The official Hermes plugin reports `agent_session_id` but neither `ctx.profile_name`, `HERMES_HOME`, nor a profile field.
4. `src/persist/snapshot.rs::PaneSnapshot` persists CWD, launch argv, and agent-session data but no profile or extra environment.
5. `src/persist/restore.rs` reconstructs restore environment with `PaneLaunchEnv::from_extra(Vec::new())`.
6. `src/agent_resume.rs` plans Hermes resume as `hermes --resume <id>` with no `-p/--profile`.
7. Hermes profile wrappers and early CLI selection use explicit `-p <profile>`/`HERMES_HOME`; `PluginContext.profile_name` is available for a future typed reporter.

Only conclude profile-safe native restore if every link is re-checked in the new release. A fix to just one layer may still leave the chain broken.

## Read-only verification technique

Prefer a small in-memory invariant verifier over a large narrative search:

- Under a literal no-file-creation constraint, do not use `web_extract`; it may automatically persist long docs and source files to cache. Fetch tagged raw files with `curl`/`urllib` to stdout or inspect official docs through the browser DOM.
- Resolve each release tag to its commit SHA through the GitHub API, then fetch only the minimum tagged files needed for the invariant chain.
- Isolate the relevant struct/function text and add line numbers in memory; do not clone, redirect output, or create scratch scripts.
- Assert both positive fields and meaningful absences (`profile`, persisted env, `--profile`).
- Print one PASS/FAIL line per invariant and a final count.
- Keep live probes separate: versions, integration status, active profile, plugin discovery per profile, server environment key presence, socket ownership/mode, and current restore configuration.
- Never imply a destructive restart/resume test ran when the user prohibited state changes.
- If a managed tool nevertheless creates cache/result files, disclose every exact path and leave deletion to the user.

## Safe interpretation by deployment mode

### Supported baseline

- Detach/reattach keeps the original PTY and therefore preserves an explicitly selected named profile.
- A full server restart is different: it reconstructs processes and invokes the generic resume planner.
- If only the default profile has the official plugin, named-profile panes generally lack an official session reference and degrade to restored shells rather than being resumed into a wrong profile.

### Safe degraded multi-profile mode

Until profile identity is part of the official persisted resume contract:

- launch every pane with explicit `hermes -p <profile>`;
- retain the official lifecycle plugin as the sole `herdr:hermes` authority;
- do not enable native restore for named-profile panes, or disable agent restore for the whole Herdr session if profile mixing cannot be separated;
- manually resume the intended profile/session after a true Herdr server restart.

### Provisional isolation workaround

One Herdr named session/server per Hermes profile may work if a managed launcher always starts that server with the matching `HERMES_HOME`, because child PTYs normally inherit server environment. Treat this as proposed until an end-to-end stop/restart test proves it. It fragments the unified Herdr view and does not fix the profile-unaware installer.

### No-upstream compatibility restore

When upstream changes are explicitly out of scope, a user-local compatibility layer can reproduce profile-aware restore without claiming that Herdr's built-in restore supports profiles:

1. Disable built-in native agent restore for a shared multi-profile Herdr session so the generic planner cannot launch a session under the wrong profile.
2. Keep normal detach/reattach unchanged; live PTYs already preserve explicit profile selection.
3. Have a supplemental profile-aware Hermes plugin report `ctx.profile_name`, Hermes session ID, and current Herdr topology to a reviewed local bridge. It must not compete with the official `herdr:hermes` lifecycle authority.
4. Persist only the restore tuple and topology under bridge/plugin-owned state: Herdr session, terminal/current pane identity, logical workspace/tab labels, cwd/layout, Hermes profile, and Hermes session ID. Do not store transcript or memory content.
5. Restore through a human-invoked or separately approved Herdr plugin action using structured argv equivalent to `hermes -p <profile> --resume <session-id>`. Missing profiles, ambiguous identities, and duplicate tuples must fail to a shell or visible warning—never to the sticky default profile.
6. Keep automatic event-triggered restore off until duplicate suppression, reconnect reconciliation, and full restart tests pass.

This is a supported-surface proposal, not native built-in behavior. Validate it as a separate authority and report its status as custom compatibility logic.

### Correct upstream contract

Prefer a typed, validated field, not persisted arbitrary argv/environment:

```text
agent_session:
  source: herdr:hermes
  id: <session-id>
  resume_context:
    hermes_profile: <validated-profile-name>
```

Restore with structured argv equivalent to:

```text
hermes -p <profile> --resume <session-id>
```

Required behavior: validate profile syntax and existence, include profile in dedupe identity, never silently fall back to the sticky active profile, and restore to a shell when the profile is unavailable.

## Additional lifecycle hazards

### Session rotation

Inspect whether a same-owner lifecycle report may replace an existing session reference. In the audited Herdr state logic, recognized replacement reasons existed for selected integrations but not Hermes. Hermes `v2026.7.7.2` does expose `on_session_reset`, and its documented gateway order is `on_session_finalize(old) → swap → on_session_reset(new) → on_session_start(new)`, but the bundled Herdr plugin registers finalize/start rather than reset. Finalize may release the old Herdr authority before the new start, yet that does not prove every CLI/TUI/reset path rotates the persisted Herdr reference correctly. Treat `/new`, `/reset`, `/clear`, compression-triggered rotation, and gateway idle rotation as separate acceptance cases before enabling automatic restore.

### Multi-session processes

Do not model a multi-user Hermes gateway as one resumable Herdr pane. One gateway process can host many concurrent conversations, while the pane has one lifecycle authority/session reference. Keep gateways and cron as Hermes-managed services outside interactive Herdr panes; observe logs or service health instead.

### Delegation/nested runs

Nested or background Hermes work may inherit `HERDR_*` pane identity and emit the same lifecycle source. Verify that it cannot replace the root session reference or leave misleading aggregate state. Strip pane identity from unrelated child processes when feasible; never create a competing lifecycle reporter.

## Native-primitives architecture rule

- **Profiles:** identity/security boundary.
- **Herdr session/workspace/tab/pane:** runtime and terminal layout.
- **Official `herdr-agent-state`:** sole telemetry/session authority.
- **Supplemental Hermes plugin:** profile metadata and narrow structured tools only; default read-only, mutators separately enabled and approval-gated.
- **Herdr plugin:** reviewed launcher/dashboard panes after verifying the installed Herdr version exposes that plugin surface; Herdr plugins are unsandboxed user code.
- **Skills:** teach CLI use but do not create profile-safe persistence.
- **Memory/session DB/goals:** remain profile-local and authoritative in Hermes.
- **Kanban/delegation/cron/gateway:** remain Hermes-owned; Herdr observes rather than mirrors their state machines.
- **MCP/webhooks:** optional adapters, never direct exposure of the local Herdr socket; authenticated payload fields remain untrusted.

Do not expose arbitrary `pane.run` as a normal model tool: typing a shell command into another PTY can bypass Hermes terminal approval. Use fixed argv allowlists, narrow tools, explicit approvals, bounded/redacted pane reads, and treat pane output as untrusted content.

## Additional no-upstream deployment findings

### Public pane IDs and topology mutation

Herdr documents that a cross-workspace `pane.move` keeps the underlying live terminal/process but assigns a new public pane ID. The bundled Hermes plugin captures `HERDR_PANE_ID` from its launch environment, and a running process cannot have that environment rewritten. Unless a release documents an alias/rebinding path, treat cross-workspace moves of active Hermes panes as unsupported: same-workspace tab moves may be acceptable, but cross-workspace moves can strand lifecycle reports on the old ID. Test every post-move hook and prohibit the operation in the supported baseline until it passes.

### Event reconnect contract

`session.snapshot` is bootstrap state, not a durable event cursor. For a bridge cache, acknowledge an event subscription first, buffer events, fetch a fresh snapshot on a separate connection, replace local state, then apply buffered events idempotently. Repeat after every reconnect. Do not claim replay, exactly-once delivery, or an atomic snapshot/subscription cut unless a later protocol adds an explicit cursor.

### Profile-distribution packaging

Hermes profile distributions do not own `plugins/` by default, but `distribution_owned` can explicitly name profile-local plugin directories and plugins are not among the hard-excluded secret/runtime paths. A reviewed distribution can therefore carry the exact unmodified official `herdr-agent-state` asset plus a separate companion plugin. Check all four conditions:

1. plugin paths are explicitly distribution-owned;
2. both plugins are in `plugins.enabled` on first install;
3. updates preserve local `config.yaml` by default, so copied plugin updates do not prove enablement/config updates applied;
4. distributions are unsigned and have no shipping lockfile, so operators review and pin the source commit/tag externally.

### Remote thin-client versus Hermes Desktop

Herdr `--remote` is a terminal thin client over SSH: the Herdr server and Hermes pane process live on the VPS, while mouse rendering, local keybindings, and clipboard bridging live on the client. Hermes Desktop remote mode instead connects to `hermes serve` over authenticated HTTP/WebSocket. These are parallel first-party frontends, not one shared process-control channel. Avoid simultaneous writers to one conversation unless an explicit ownership protocol is documented.

### Platform-specific trust

On Unix, Herdr restricts its socket file to owner mode `0600`, which still grants every same-user process full API control. In `v0.7.3`, the Windows permission helper is a no-op and the official integration support gate excludes Hermes even though a Windows Hermes install-layout detector exists. Native Windows Herdr remote attach is also unsupported. Treat Windows named-pipe ACLs, user-local plugin fallback, and any WSL clipboard bridge as independent tests rather than parity claims.

## Adversarial acceptance matrix

Before calling multi-profile integration complete, test:

1. default plus two named profiles launched explicitly;
2. integration discovery and checksum in every intended profile;
3. lifecycle `idle → working → blocked → working → idle`;
4. session rotation inside a live pane;
5. sticky active profile changed before restart;
6. missing/deleted profile fallback;
7. same session ID present in two profile homes;
8. detach versus full server restart as separate cases;
9. nested delegation and headless runs;
10. gateway kept outside interactive pane ownership;
11. socket owner/mode and protocol mismatch;
12. bounded/redacted pane reads with prompt-injection payloads;
13. control-action deny/timeout yielding zero mutation;
14. same-workspace tab move versus cross-workspace public pane-ID replacement, with post-move hook delivery;
15. no secrets in argv, logs, screen history, metadata, or event payloads;
16. subscribe/buffer/snapshot reconciliation after an event-stream outage, without replay assumptions;
17. distribution install/update with explicit plugin ownership, preserved config, enablement checks, and no user data;
18. Unix same-user socket control and Windows named-pipe/support-gate behavior;
19. local Herdr thin-client and Hermes Desktop treated as separate writers/frontends;
20. strict one-profile/Herdr-session restore after remote server restart, including proof that the restarted server retained the intended `HERMES_HOME`.

## First-party source map

- Herdr release: `https://github.com/ogulcancelik/herdr/releases/tag/v0.7.3`
- Hermes release: `https://github.com/NousResearch/hermes-agent/releases/tag/v2026.7.7.2`
- Herdr integration: `src/integration/{env.rs,targets.rs,assets/hermes/__init__.py}`
- Herdr restore: `src/{agent_resume.rs,persist/snapshot.rs,persist/restore.rs,terminal/state.rs}`
- Hermes profile selection: `hermes_cli/{main.py,profiles.py}`
- Hermes plugin profile awareness: `hermes_cli/plugins.py`
- Public docs: Herdr integrations/session-state/socket/plugins; Hermes profiles/plugins/hooks/security/sessions/MCP/webhooks.

## Reuse warning

Re-run the invariant chain on the latest stable tags. If later releases add profile-aware installation or typed resume context, replace this reference's version-specific conclusion rather than carrying it forward as a refusal.
