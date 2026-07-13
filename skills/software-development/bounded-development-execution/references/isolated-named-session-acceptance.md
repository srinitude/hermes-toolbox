# Isolated Named-Session Acceptance Harnesses

Use this pattern when a plugin wraps a local session-oriented CLI and real tests must never fall back to a user's active/default session.

## Harness lifecycle

1. Capture read-only snapshots of every protected live session before bootstrap.
2. Create a dedicated temporary control-plane root and set `XDG_CONFIG_HOME`, `XDG_STATE_HOME`, and `XDG_CACHE_HOME` for the owned server **and every CLI subprocess that targets it**. This isolates session registries, plugin config, plugin state, caches, and sockets from the user's live roots.
3. Remove only the reserved test session if stale; never clean broad runtime directories.
4. Start the reserved named server as a tracked child process with inherited socket/pane selectors removed.
5. Poll native status through the isolated environment and require an explicit semantic readiness marker such as `running: true`. Do not accept socket existence or exit code zero alone: a stopped registered session may retain a stale socket, and some status commands return zero while reporting `running: false`.
6. Bootstrap the minimum real topology needed by acceptance tests through that exact socket.
7. Pass `HERDR_ENV=1`, the exact socket path, and an exact caller pane ID to every fresh consumer process.
8. In fixture teardown, stop through the exact socket, wait for the owned server child, invoke the native session-delete operation, assert the reserved session and socket are gone, then remove only the dedicated XDG test root and compare protected-session snapshots with their baselines.

Teardown assertions are acceptance evidence, not optional cleanup. Ensure command helpers tolerate successful commands with empty stdout, because server-stop commands may return no JSON.

## Native event-hook state paths

A hook process can exit successfully while the expected durable state remains unchanged. Treat `exit_code: 0` and `{ok:true}` as transport evidence only.

- Derive plugin config/state paths from Herdr-injected `HERDR_PLUGIN_CONFIG_DIR` and `HERDR_PLUGIN_STATE_DIR`; do not duplicate platform path formulas in production.
- In real tests, isolate those paths with the dedicated XDG root and assert the resulting ledger/config file is beneath that root.
- Seed only the explicit launch identity the hook is allowed to update, then trigger a real native event and poll the durable file for the exact semantic transition.
- Inspect native plugin logs when the hook reports success but state does not move; this distinguishes event delivery from wrong-path, stale-identity, or merge-contract failures.
- Verify close/exit events remove the exact entry, file mode remains private, and teardown leaves no test plugin state.

This prevents a green hook process from being mistaken for successful reconciliation.

## Production context gate

At the process adapter boundary, before binary lookup or request dispatch:

- require the integration marker's exact value;
- require a bounded absolute path that currently identifies a Unix socket;
- reject missing, relative, stale, and non-socket paths with a typed unavailable result;
- construct a small child environment containing only needed config/locale values plus the exact socket context;
- keep `shell=False` and fixed argv vectors.

This prevents accidental default-session fallback. Test the same missing/invalid context matrix through every public model-facing tool, not only through a helper.

## Snapshot projection

A native session snapshot can contain output-adjacent, filesystem, process, or user-label data. Expose a bounded allowlist instead of returning it directly:

- cap workspaces, tabs, panes, and agents independently;
- retain only IDs, counts, focus relationships, terminal IDs, agent type/status, and revision when required;
- omit cwd, foreground cwd, labels unless explicitly required, scrollback, layouts, pane text, environment, process details, transcripts, and agent-session payloads;
- return per-collection truncation flags;
- assert a serialized response-size ceiling and recursively scan result keys for forbidden data families.

## Stable identity binding

Bind authority to profile, exact socket, named session, and the live caller pane. Resolve the launch-time pane ID through the live current-pane API and fail typed-unavailable when absent or stale.

Only stable pane identity belongs in a confirmation token: pane, tab, workspace, and terminal IDs. Do **not** bind focus, status, or revision as identity fields. Those are mutable preconditions; including them changes a normal intervening focus transition from `stale_precondition` into the misleading `stale_identity` result.

When explicit socket targeting makes a native status command omit the session name, correlate a validated named-session socket shape with its bounded session segment, while still requiring live status to echo the exact resolved socket.

## TDD sequence

Use vertical public slices:

1. missing integration/socket context returns typed unavailable through every model tool;
2. real bounded topology snapshot;
3. profile/socket/session/caller identity and absent/stale caller rejection;
4. hostile-input matrix proving rejection or one-argv preservation;
5. final structural, secret, prohibited-pattern, diff, full-suite, cleanup, and clean-status checks.

For each slice, witness a public RED first, implement minimally, run focused GREEN, then run the full isolated regression suite. Do not claim completion or commit if the hostile-input and final structural gates remain outstanding.
