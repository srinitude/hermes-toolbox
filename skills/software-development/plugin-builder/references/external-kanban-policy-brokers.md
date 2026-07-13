# External Kanban Policy Brokers Without Core Edits

Use this reference when a user asks for system-wide or universal Kanban policy enforcement while explicitly prohibiting edits to the Hermes Agent source checkout.

## Fundamental boundary

A profile plugin cannot veto mutations made by processes that did not load it. Native CLI, `/kanban`, dashboard REST, gateway dispatcher, cron/scripts, direct Python imports, and direct SQLite access remain independent entry points.

Therefore separate two meanings of compatibility:

- **Semantic compatibility:** every native operation has a broker route, adapter, or visible fail-closed result.
- **Unchanged native mutation UX:** the original CLI/dashboard continues writing authority directly.

Without core changes, universal enforcement and unchanged direct-native mutation authority cannot both be guaranteed. State this before planning. Do not hide the conflict behind hooks or aliases.

## Strongest no-core architecture

Use an external reference monitor:

1. A dedicated OS identity owns authoritative Kanban databases outside user-writable `$HERMES_HOME`.
2. A broker evaluates policy and is the sole authoritative writer.
3. Normal Hermes/gateway/dashboard/cron/worker processes have no authoritative DB write access.
4. Human plugin/CLI surfaces call the broker over an authenticated local IPC channel.
5. Native direct mutation paths are broker-shimmed or visibly denied; they never silently become authoritative.
6. The embedded native dispatcher is disabled. An external dispatcher claims through the broker.
7. A user-side launcher resolves Project workspaces/worktrees and starts workers with the correct profile credentials, while remaining unable to write authority.

This is deployment-level enforcement, not a first-party/core policy API. `root`, the broker identity, kernel compromise, and replacement of the broker deployment remain explicit trust boundaries.

## Privileged production no-go gates

Before privileged deployment or live cutover, require all of these. Failure of any gate means **NO-GO**, not “best effort”:

1. **Immutable trusted code:** the broker imports only a root-owned, hash-pinned wheel/venv or container image. Never let a privileged broker import a user-writable Hermes checkout, `PYTHONPATH`, `.pth`, `sitecustomize`, plugin tree, or working directory.
2. **Distinct principals:** broker/database owner, human mutation client, and workers are separate OS/security principals. Do not place reusable human credentials where same-UID workers or descendants can read or invoke them. `SO_PEERCRED` identifies a UID, not a task/run; workers still need run-scoped capabilities.
3. **Complete filesystem boundary:** protect every authoritative DB ancestor and sibling sidecar/lock/metadata path, not only `kanban.db`. Ordinary users must be unable to create, unlink, rename, replace, symlink, or write DB, WAL, SHM, journal, lock, metadata, backup, or parent paths.
4. **Pure read plane:** do not grant native dashboard/CLI readers direct authoritative access. Native `connect()` and apparently read-only paths may create directories, enable WAL, migrate schema, or recompute state. Use broker reads or consistent online snapshots.
5. **No ambient multi-board DB pin:** every request names a canonical board and the broker verifies `PRAGMA database_list` against the expected canonical path. A process-global `HERMES_KANBAN_DB` can override apparent board selection and collapse multiple boards onto one DB.
6. **Single writer and restore fencing:** lock/path/schema mismatch, a second broker, unknown migration, or generation mismatch prevents startup. Backup uses SQLite online backup only; restore requires all old-generation readers/writers/snapshotters stopped and switches to a validated new generation.
7. **Broker-side lifecycle authority:** liveness, heartbeat, reclaim, launch leases, and worker termination are broker/supervisor responsibilities. Use cgroup/process-handle supervision rather than trusting a wrapper PID or snapshot heartbeat.
8. **Compatibility restrictions are explicit:** reject `goal_mode`, Projects/worktrees, arbitrary directories, attachments, auto-decompose, review lanes, and native notification behavior until each has a real end-to-end test proving no confused deputy, split brain, or bypass.

The service account must have no model/API/user credentials, login shell, user profile home, or writable source. Do not claim root-resistant enforcement; root/kernel/deployment replacement remain trusted boundaries.

## Why dispatch must be split

Current native dispatch resolves or creates a task workspace before calling its pluggable `spawn_fn`. A DB-owning service account should not receive broad access to user repos, profile auth, or Project worktrees merely to reuse `dispatch_once()`.

Split the path instead:

- Broker: promotion, selection, claim, policy decision, launch lease, PID/result recording.
- User launcher: resolve Project owner, create workspace/worktree as the user, launch the assignee profile, report PID/workspace/exit.

Project ids are per-profile. Store Project references as `(profile, project_id)` and treat board slug as a separate global authority key. If project and board selectors disagree, deny rather than widen scope.

## Worker compatibility pattern

To preserve native `HERMES_KANBAN_TASK`, KANBAN_GUIDANCE, and `kanban_*` schemas without exposing authority:

1. Install a trusted broker-client plugin in workflow profiles.
2. Use `ctx.register_tool(..., override=True)` only with explicit `plugins.entries.<plugin>.allow_tool_override: true` in those profiles.
3. Override every currently exposed native Kanban model tool with an exact-schema broker handler.
4. Give each worker a writable per-run compatibility snapshot through `HERMES_KANBAN_DB`.
5. Broker handlers mutate authority, then mirror only accepted status needed by worker-side core behavior into the snapshot.
6. Direct native/SQLite writes by the worker affect only its snapshot.

Tool override is a high-trust exception. Verify real registry handler ownership, standard agent dispatch, and alternative transports such as the Codex app-server MCP bridge. Normal profiles should keep override disabled.

### Installed-plugin verification gate

Source-tree imports are insufficient evidence for an override plugin. Build and install the wheel into a fresh environment, then prove:

1. The wheel contains the plugin manifest plus every immutable compatibility contract/operation ledger needed at runtime. Repository-root `data/` paths commonly disappear after installation; package them explicitly and resolve source-tree versus installed-package locations without duplicating authoritative tracked content.
2. A fresh real `PluginManager` process with native tools registered and `allow_tool_override: false` leaves every native handler owned by the native module and records the plugin load failure/disable state.
3. A separate fresh process with explicit `allow_tool_override: true` loads successfully and reports plugin ownership for the complete exact tool set, byte/structure-equivalent schemas, and the original toolset namespace.
4. The probe runs with the installed wheel and pinned Hermes only—no broker source checkout on `PYTHONPATH`—so editable imports cannot mask missing package data.
5. Unrelated optional bundled-plugin dependency warnings are classified separately; the target plugin’s enabled/error state and registry ownership decide this gate.

If any required contract file, manifest, handler, schema, or ownership assertion fails, remain in `compatibility_hold`; do not install the consumer plugin or claim wheel readiness.

## Approval and capability contracts

- Human approval tokens bind canonical profile, board, Project reference, task, operation, normalized arguments, policy version, actor, and expiry.
- Model-callable preview tools never mint or consume human tokens.
- Worker capabilities bind persisted worker principal class/profile, kernel UID/PID, board, task, run, claim, allowed operations, expiry, revocation, and terminal state.
- Store token digests, not plaintext tokens; never place plaintext tokens in logs, audit events, operation intents, result objects, or object representations.
- Use kernel-derived `SO_PEERCRED` on local Unix sockets, then validate every scoped field against broker storage. Caller-supplied actor/profile strings are context hints, not identity evidence.
- Human authorization must bind and revalidate the exact `(principal, profile, UID, PID, process start time, binding generation, session expiry)` tuple on every request. PID/UID alone is vulnerable to PID reuse; unreadable or ambiguous `/proc`/pidfd state fails closed.
- Bind approval challenges to that same operator session tuple, including start time and generation. Rebinding or session expiry invalidates outstanding challenges even when UID/profile and request fingerprint still match.
- Do not expose a generic public `operator.enroll` request. Prefer a private registrar socket available only to a distinct registrar identity: the registrar spawns the CLI as a gated direct child, sends only its PID, and the broker derives UID/parent/start-time from the kernel, holds a pidfd, CAS-binds one active operator session, acknowledges durable binding, then permits gate release. No reusable enrollment bearer secret is needed.
- A production CLI must perform preview, exact `/dev/tty` confirmation, and execution in the same enrolled process. Keep approval plaintext only in that process memory—never argv, environment, disk, logs, worker inheritance, or subprocesses—and never fall back to native authority on broker failure.
- `SO_PEERCRED` alone does **not** distinguish a human client from an agent process running under the same UID. A worker can also spawn a different PID. Production human-approval minting therefore needs a distinct OS/security principal or an out-of-band server-side operator grant that workers cannot read or invoke. If neither exists, record same-UID human/model separation as an explicit residual trust assumption and fail the strong-enforcement gate.
- Treat any in-process `TrustedHumanContext`-style object as a capability, not a descriptive dataclass. Caller-constructible fields such as principal id, kind, UID, profile, or PID are forgeable even when they match persisted rows. The broker should issue an opaque or broker-keyed proof bound to the kernel peer PID/UID and persisted principal, keep that proof out of representations/wire requests, and revalidate it at both challenge mint and reservation. A public constructor with matching strings is not trusted context.
- Reserve the approval challenge and matching operation-journal intent in one SQLite transaction. A journal conflict or constraint failure must leave the challenge pending.
- Apply the mutation idempotently, persist the journal result, and only then consume the exact reserved approval with a CAS bound to request id and fingerprint. Concurrent reservation/consumption has one winner.
- Recovery lists reserved, unconsumed approvals with their journal state/result. Resolve ambiguous crashes by comparing authoritative post-state; never blindly replay.

## Multiple boards and workflows

- Require an explicit canonical board for every mutation; never rely on a process-global current-board pointer at the policy boundary.
- Forbid cross-board links.
- Assign each board a versioned policy. Unknown boards enter read-only quarantine.
- Do not force an existing domain workflow into a generic lifecycle. Import existing tasks unchanged and require an approved board-specific policy before enforce-mode writes.
- Preserve `work_key`, `work_run`, `context_bundle`, dependency promotion, supported block kinds, design exceptions, approval gates, and cancellation semantics.

## Version-pinned compatibility reconnaissance

Before designing adapters, inspect the exact installed commit rather than trusting an older audit or even this reference. Record findings in the compatibility ledger and re-run them after every Hermes upgrade. On Hermes Agent `v0.18.0` at commit `c67aab763dd68a26a07bd3c7aec0443268c76225`, the useful regression facts were:

- There are nine native model tools: `show`, `list`, `complete`, `block`, `heartbeat`, `comment`, `create`, `unblock`, and `link`. Scoped workers see seven; `list` and `unblock` are orchestrator-only. Count only native registrations, not separate `kanban_workflow_*` plugin tools.
- `HERMES_KANBAN_DB` overrides even an explicit `board=` argument. Test isolation must unset direct DB/workspace/attachment pins as well as setting temporary `HERMES_KANBAN_HOME` and `HERMES_HOME`.
- Native `connect()` and every non-board CLI command may create paths, enable WAL, or migrate schemas. `list` also calls dependency promotion. Do not label a native read route filesystem- or database-read-only without a real probe.
- `dispatch --dry-run` still performs stale-claim release, crash/timeout handling, dependency promotion, and possible worker termination before its dry-run branch. Never use it as shadow-mode evidence.
- Project ids are profile-local. Unknown `project_id` values can silently fall back to unlinked tasks, and a Project `board_slug` does not route a supplied Kanban connection. Broker selectors must reject unknown or mismatched `(profile, project_id, board)` tuples before native calls.
- Native create idempotency lookup is not uniqueness-backed; board metadata and several multi-step CLI operations cross transactions/filesystem effects. The broker operation journal must supply the stronger idempotency and recovery contract.
- Plugin override registration is per-tool, non-atomic, and not rolled back when later registration fails. Preflight every schema before the first override and use a supervisor startup gate to verify all handler ownership before serving work.
- The Codex MCP transport must be validated with a real `tools/list`: the inspected path obtained authoritative schemas but did not pass them to `FastMCP.add_tool()`. If exact input schemas cannot be proven, put that transport in `compatibility_hold` rather than claiming parity.
- Goal-loop budget exhaustion, the normal turn finalizer, and automatic heartbeats include direct database writes outside tool handlers; the Codex early-return path also bypasses the normal finalizer. Keep `goal_mode` unsupported in enforce mode until broker/supervisor reconciliation is proven end to end.

These are regression probes, not timeless product claims. If current first-party source or live CLI behavior differs, current evidence wins and the broker remains in `compatibility_hold` until its contract and tests are deliberately updated.

## Native-surface treatment

- **CLI:** a shim may preserve `hermes kanban` syntax, but direct real-binary writes must still lack authority.
- **`/kanban`:** route if a supported command interception exists; otherwise deny visibly against protected authority.
- **Dashboard:** without a supported upstream adapter, use broker-backed reads and disable/deny native mutations. Do not rewrite bundled JavaScript as a workaround.
- **Notifications:** broker-owned subscriptions/event stream should feed gateway/TUI clients; notification failure must not roll back task state.
- **Projects:** live Project changes are not Kanban authority. Compare them to broker bindings and report drift.

## Long-running implementation discipline

- Use one writer at a time for a shared repository. A delegated TDD worker may intentionally leave its files RED between the test and implementation steps; do not launch a second repair writer against those paths.
- Delegate bounded vertical slices that can finish within the worker's tool budget. Require either a clean verified commit or an explicit uncommitted handoff listing files, last RED/GREEN evidence, and remaining behavior.
- After every handoff, re-read files the worker touched before editing. Run the narrow pending GREEN first, then the full suite and structural/security checks before committing.
- Treat live pinned source and real CLI/runtime probes as authoritative over saved-plan prose or prior delegated audits. Correct a disproven assumption with a witnessed failing regression test, not by encoding a false permanent compatibility hold.
- For concurrency contracts, prefer real temporary SQLite plus threads/processes and CAS assertions with exactly one winner; for identity, use real Unix socket pairs and kernel credentials. Do not substitute mocks for reference-monitor boundaries.
- Enforce source/test file, construct, and nesting limits with a parser-based verifier before every commit, then remove temporary verifier artifacts.

## Upgrade and migration gates

Pin the deployed broker adapter to the exact installed Hermes version/commit and generate a compatibility ledger covering:

- every CLI verb and flag;
- all model tool schemas;
- adapter function signatures;
- environment/path precedence;
- dashboard/gateway/dispatcher entry points.

Unknown commits, new verbs, changed schemas, or missing functions place writes in `compatibility_hold`; read-only health/explain may continue.

Before cutover:

1. Stop native gateway dispatch and verify no active worker.
2. Pause backup/publisher automation that could race or publish source.
3. Take a consistent SQLite online backup; do not copy a live DB without accounting for WAL.
4. Validate restore in a disposable root.
5. Import boards and policies, then compare ids, counts, tasks, links, comments, events, runs, metadata, and timestamps.
6. Keep source creation, consumer installation, root deployment, cutover, and publication as separate approvals.

## Adversarial validation threshold

At minimum prove:

- direct CLI, `/kanban`, dashboard, Python, and SQLite attempts make zero authoritative mutation;
- wrong/replayed/expired/altered approval tokens make zero mutation;
- workers cannot cross task/run/board/profile scope;
- broker outage fails closed;
- embedded dispatch remains disabled after restart and across profile gateways;
- cross-board links, Project/board mismatch, and implicit board scope are denied;
- authoritative DB writable handles belong only to the broker identity;
- backup/restore is exact;
- compatibility drift triggers hold;
- audit records every allow/deny/recovery without secrets;
- the upstream source checkout has no new diff.

## Pitfalls

- Claiming a plugin hook is universal enforcement.
- Using aliases/wrappers as the only security boundary.
- Running the broker as the same OS user that owns the DB.
- Letting the DB-owning service resolve user Project worktrees.
- Giving workers a readable authoritative DB when a disposable snapshot suffices.
- Treating profile-local Project ids as globally unique.
- Preserving a dashboard success response that changed only a shadow DB.
- Auto-migrating a custom board to a generic lifecycle.
- Resuming a public publisher merely because the package is reusable.
