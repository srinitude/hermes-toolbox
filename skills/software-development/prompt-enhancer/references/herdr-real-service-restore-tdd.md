# Herdr real-service restore TDD

Use this reference when a saved plan integrates Herdr plugins, Hermes named profiles, explicit identity ledgers, or full-server restoration.

## Isolated real-service fixture

- Run a real named Herdr server under temporary `HOME`, `XDG_CONFIG_HOME`, `XDG_STATE_HOME`, and `XDG_CACHE_HOME`.
- Write both global and named-session test configs with `resume_agents_on_restore = false`. Do not assume the production config is inherited by an isolated server.
- Snapshot protected real sessions before the fixture and compare them after teardown.
- Delete only the named test session and its temporary roots.
- Assert the child agent executable has not run immediately after restart; otherwise native restoration may be masking the compatibility path under test.

## Public Herdr identifiers

Do not model Herdr pane, tab, or workspace suffixes as decimal-only. Pinned Herdr releases encode public numbers with this Crockford-style alphabet:

```text
123456789ABCDEFGHJKMNPQRSTVWXYZ0
```

Production IDs can therefore look like `w2:pE`, `wA:t0`, or `wZ`. Derive validators from the pinned Herdr source and add acceptance cases above `9`; a test fixture that creates only `p1`/`p2` will miss this defect. Reject lowercase and excluded ambiguous letters such as `I`, `L`, `O`, and `U` when the pinned alphabet excludes them.

## Session identity reporting

Use the official integration source identifier exactly. For Hermes v3 it is `herdr:hermes`, not a punctuation variant such as `herdr.hermes`. An untrusted source can update visible status while its session reference is silently omitted, producing a misleading partial success.

The public agent record exposes the trusted session as a nested object:

```json
{"agent_session":{"agent":"hermes","kind":"id","source":"herdr:hermes","value":"..."}}
```

Normalize only this trusted shape into plugin-owned restore metadata. A visible Hermes TUI or successful response is not enough: query the live Herdr agent record and require the trusted nested shape.

## Explicit identity seeding

When lifecycle events can refresh only previously known mappings, provide a bounded explicit seeding surface rather than inferring profile identity from labels or pane text.

A safe one-time seed flow:

1. Read a private `0600` catalog with an exact schema and bounded entry count.
2. Require terminal, pane, workspace, tab, cwd, existing Hermes profile, and opaque session ID.
3. Compare every field to one live snapshot whose agent is `hermes` and whose `agent_session` has the trusted official shape.
4. Reject duplicate panes/terminals, duplicate profile-session tuples, and one session mapped to multiple profiles.
5. Take the same ledger lock used by close/status events **before** the final live snapshot and validation. Validating before acquiring the lock creates a lost-close race: a pane can close, its event can observe no ledger entry, and then stale state can be written.
6. Atomically write only the validated projection; never copy arbitrary snapshot fields or environment data.
7. Delete the one-time seed catalog only after persistence succeeds. Retain it on failure for visible diagnosis.

Test broad file modes, stale terminal identity, high-suffix public IDs, duplicate mappings, event races, and successful one-time consumption with a real Herdr server.

## Full-restart identity rebind

Do not assume Herdr terminal IDs survive a full server stop/start. A real restart can preserve pane/workspace/tab placement while assigning a new terminal ID.

Persist the pre-restart tuple:

```text
(Herdr session, terminal ID, pane ID, workspace ID, tab ID, cwd,
 Hermes profile, Hermes session ID)
```

After restart:

1. Require exactly one pane matching the saved pane/workspace/tab/cwd slot.
2. Require a new valid terminal ID; an unchanged terminal means no proven restart rebind and must not trigger a duplicate resume.
3. Reject missing or ambiguous slots visibly.
4. Revalidate that the profile exists and that stored argv exactly equals `hermes -p <profile> --resume <opaque-id>`.
5. Require an exact short-lived human-typed token in a terminal pane.
6. After token acceptance, revalidate the current terminal slot and profile immediately before launch.
7. Launch via fixed argv with `shell=False`; never accept free-form shell text.
8. Remove a target only after its launch succeeds. If dispatch fails, retain the target so the operator can diagnose and retry; consuming before dispatch silently loses recoverability.
9. Keep fail-closed warnings visible until the operator dismisses them—short-lived plugin panes can otherwise exit before their output is observable.

## Durable production server

If the named Herdr server must survive the agent/tool session, run it as a dedicated user service rather than a tool-owned background process.

- Use a separate unit per named Herdr session; do not repurpose an unrelated default-session service.
- Set `HOME` and an explicit `PATH` containing the actual Hermes/Herdr/agent executable directories. A service can be healthy while plugin panes fail because `hermes` is absent from systemd's default path.
- Do not apply `ProtectHome`, restrictive `ReadWritePaths`, or similar service sandboxing without proving every child terminal/agent can still write its intended worktree and profile state. Herdr is an orchestrator, so restrictions propagate to its children.
- After restart, expect plugin panes to restore as shell slots when native process restore is disabled. Close those stale shells and explicitly reopen required plugin panes.
- Verify the unit is enabled and active, then run reconnect probes from each approved thin client.

## Pane-output tests

Headless panes may wrap text to a very narrow viewport. Read confirmation prompts with `pane read --source recent-unwrapped --lines N --format text`; parsing `visible` output can split tokens and command summaries across lines.

When polling plugin logs, establish whether results are oldest-first or newest-first. Select the newly invoked record by a captured count/identity or the verified ordering; blindly taking index zero can misclassify a successful retry as the prior failure.

## Acceptance evidence

A credible restore proof records all of the following:

- native auto-restore disabled;
- no child launch immediately after restart;
- post-restart slot/terminal rebind evidence;
- wrong-token denial with target preserved;
- correct-token execution with exact `-p` and `--resume` argv;
- failed launch preserves its target;
- successful launch removes its target exactly once;
- stale/ambiguous target warning visible;
- trusted session-source identity before persistence;
- protected sessions unchanged and isolated test state removed;
- durable production service and client reconnect proof when persistence is required.
