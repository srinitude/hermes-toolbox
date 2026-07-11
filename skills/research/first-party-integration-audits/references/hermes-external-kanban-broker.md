# Hermes external Kanban broker: adversarial review notes

Use this reference when evaluating a no-core-change design that puts the authoritative Hermes Kanban DB behind a dedicated OS-account broker while workers receive compatibility snapshots or plugin tool overrides. Re-check the selected Hermes release because every interface below is implementation-coupled.

## Outcome rule

A separate writer UID and protected DB directory are necessary but not sufficient for a reference monitor. Classify the design as production **NO-GO** until it demonstrates all three properties:

1. **Complete mediation** — every authoritative mutation, including dispatcher transitions, lifecycle fallbacks, dashboard operations, and restores, is mediated.
2. **Tamper resistance** — workers cannot alter broker code, policy, credentials, sockets, lock files, DB sidecars, or the code the broker imports.
3. **Small/verifiable TCB** — the trusted policy boundary is narrow. Importing all of `kanban_db.py` and calling `dispatch_once()` puts its transition, filesystem, Git, profile, plugin, and process behavior inside the TCB; `spawn_fn` intercepts only process creation.

A broker can still be useful when the explicit guarantee is only “ordinary UIDs cannot directly write SQLite.” Do not silently upgrade that into universal workflow-policy enforcement.

## High-value bypass inventory

Trace these separately; a tool override covers only the first class of model-originated calls:

- `kanban_*` registry handlers;
- worker auto-heartbeat writes;
- iteration-budget failure writes in turn finalization;
- `goal_mode` status reads and direct budget/finalization blocks;
- native CLI and slash commands, including the TUI/Desktop persistent `HermesCLI` slash-worker subprocess;
- gateway `/kanban create` followed by its separate auto-subscription write;
- dashboard mutations, bulk operations, direct status SQL, run termination/reclaim, board CRUD, attachments, orchestration/profile-config writes, and `/dispatch`;
- decomposer, specifier, swarm, notifier cursor/subscription writes;
- Projects CLI, GUI-only Project tools, TUI `projects.*` JSON-RPC, active-project state, session-CWD callbacks, and Projects-to-board metadata synchronization;
- backup/import/restore and event/log garbage collection;
- direct Python imports and direct SQLite access.

Also cover filesystem authority outside SQLite: `board.json`, the shared `kanban/current` pointer, attachments, workspaces/worktrees, logs, dispatch locks, and Project paths. A task mutation can span several of these stores.

ACL denial can safely contain native/direct bypasses, but shims and plugins are UX—not the security boundary. A worker can disable plugins, run nested Hermes, import handlers directly, or call the broker protocol itself.

## Native UX versus semantic parity

Always make the guarantee explicit:

- **Semantic parity** means broker-owned commands/tools/APIs reproduce the lifecycle, run, dependency, Project, dispatch, and notification outcomes.
- **Unchanged native mutation UX** means existing CLI, slash, model-tool, dashboard, TUI/Desktop, dispatcher, and goal-mode paths still succeed or receive native-form denials while every forbidden write is rejected before any side effect.

On releases with no synchronous pre-mutation kernel hook, an out-of-process broker can provide semantic parity only by becoming the exclusive writer and redirecting/replacing native mutators. Filesystem ACLs can make bypasses fail closed, but native commands then fail rather than retain unchanged UX. Post-commit hooks, event polling, and compensating rollback are eventual observation—not universal enforcement.

## External/control-plane lane trap

Do not accept worker-lane prose without tracing the dispatcher order. In the audited v0.18.0-shaped implementation, normal and review dispatch call `profile_exists(assignee)` and classify an unknown assignee as `skipped_nonspawnable` **before** invoking the caller-supplied `spawn_fn`. The skipped task is represented in `DispatchResult`; the implementation does not emit the `skipped_nonspawnable` task event promised by the contemporaneous worker-lane documentation.

Consequences:

- A custom `spawn_fn` alone cannot launch non-profile assignees such as `kanban-workflow-*` lanes.
- No public non-profile lane-registration API was evidenced in that snapshot.
- External lanes must pull and claim work themselves, use deliberately matching Hermes profiles, or own/replace dispatch.
- Treat external pull lanes as separate mutation principals and test claim, heartbeat, stale-run rejection, completion/block, and review claims independently.
- Re-check the selected release: this is implementation-coupled and may be fixed upstream.

## Selection and Project fail-open traps

- `HERMES_KANBAN_DB` overrides explicit board routing. Never leave it ambient in a multi-board broker; resolve every request to a canonical DB and verify `PRAGMA database_list`.
- The shared `kanban/current` pointer is process-global state and races across clients. Use an explicit board on every operation.
- Projects are per-profile while boards are shared. Carry Project-owner profile plus canonical Project ID; a slug alone is ambiguous.
- Native task creation may silently discard an unknown Project reference and create an unlinked scratch task. A broker that promises Project governance should reject unresolved links rather than inherit this fail-open behavior unknowingly.

## Compatibility-snapshot split brain

A writable snapshot lets unmodified worker internals run, but it creates two state machines:

- overridden tools commit to the authoritative broker;
- native worker internals continue reading/writing the snapshot.

After an authoritative completion, a local snapshot may still say `running`; `goal_mode` can continue, retry, or block only the snapshot. Mirroring the transition locally is not atomic in either order. Automatic heartbeat and iteration-budget failure writes also miss the broker.

Safe initial posture:

- reject `goal_mode`;
- use broker/supervisor liveness rather than local auto-heartbeats;
- classify worker exit without a terminal broker mutation as a protocol failure;
- do not claim native run-history equivalence;
- avoid local-to-authoritative replay of arbitrary snapshot writes.

A safer no-upstream worker shape is to omit `HERMES_KANBAN_TASK`, expose only broker-namespaced tools, and pass task context in the prompt. This sacrifices native compatibility but avoids hidden Kanban lifecycle writes.

## OS identity and credential rules

- Broker, workers, and humans need distinct principals. If human and worker share a UID, a CLI shim credential is normally callable or readable by the worker.
- Do not spawn Hermes under the DB-writer UID. Drop privilege before Python/plugin code starts.
- Give workers only run-scoped capabilities bound to `(board, task, run, claim_lock, operations, expiry, request_id)`; assume workers and descendants can read them.
- Keep model/provider credentials out of the broker. Keep broker-wide bearer secrets out of workers.
- Unix-socket peer credentials identify a UID, not a task/run; combine peer checks with scoped capabilities.
- Cross-UID workers break native `os.kill(pid, ...)` assumptions unless a trusted launcher/cgroup supervisor owns termination.
- Bind liveness to a pidfd/cgroup or PID plus process start time; integer PID alone is vulnerable to wrapper exit and PID reuse.

## Immutable-code requirement

Never let a service account import Hermes from a user-writable checkout, console script, venv, `.pth`, `sitecustomize`, plugin tree, working directory, or `PYTHONPATH`. Use a root-owned, release-pinned image/venv and verify import origins/hashes at startup. Sanitize `PATH`, Python environment variables, dynamic-loader variables, `HERMES_BIN`, project-plugin toggles, and current directory.

Use a broker-owned `HERMES_HOME` containing only sanitized config/profile roster data. Pointing the broker at real user profile homes can expose credentials and creates privileged SQLite/symlink confused-deputy paths.

## Workspace and Project hazards

Projects are per-profile while boards are shared. Native task creation may resolve `project_id` through the broker's active `$HERMES_HOME/projects.db`, silently drop unresolved links, and later execute `mkdir`/Git worktree operations with broker privilege. A user-controlled `projects.db`, symlink, repo path, or board `default_workdir` must never be opened or acted on as the DB-writer UID.

Initial safe scope:

- broker-owned scratch workspaces only;
- protected parent, per-task leaf handed to the worker UID;
- reject Project links, worktrees, and arbitrary `dir` paths;
- later run workspace/Git preparation under the workspace owner's UID through a separate narrow helper.

## SQLite, WAL, ACL, and path checks

Protect directories and all ancestors, not only `kanban.db`. Directory write permission permits unlink/replace attacks and SQLite needs sibling WAL/SHM/journal/lock files. Include board metadata, current-pointer, backup, attachment, log, and lock paths in the ACL review.

Require:

- local filesystem with working advisory locks and atomic rename;
- restrictive umask and pre-created service-owned hierarchy;
- no group/default-ACL write access for ordinary users;
- fail-closed lock behavior in the external service even where native helpers degrade open;
- canonical DB identity check from `PRAGMA database_list` before dispatch;
- no ambient broker `HERMES_KANBAN_DB`, because it overrides explicit board routing;
- explicit board on every request; never use the global current-board pointer for concurrent clients.

Native `connect()` is not a pure reader: it creates directories, enables journal mode, and runs migrations. Native dashboard GET paths may initialize DB state, and some “read” commands recompute readiness. Use a broker read API or broker-created online snapshot, not direct read credentials.

For backups, use SQLite online backup and fail closed. Never fall back to raw main-file copy on a live WAL database. Restore only after fencing all broker/read/snapshot operations, into a new validated generation; never place an old main DB beside a newer WAL.

## Race checklist

Inject crashes at:

1. after claim;
2. after capability persistence;
3. after snapshot;
4. after spawn;
5. before worker-handle/PID recording;
6. after authoritative commit but before response.

Require startup reconciliation for each state. Also test stale-token use after reclaim, duplicate request IDs, concurrent replay, board archive during dispatch, broker restart with live workers, and two broker instances when locking is unavailable.

Native task idempotency may be advisory/racy; broker request dedup needs a database-enforced key or serialized durable request journal. Do not claim exactly-once execution—target idempotent mutation and at-most-one active run per scoped identity.

## Multi-scope identity rules

Always carry and validate:

- board slug;
- task id (board-local);
- run id and claim lock;
- assignee/profile owner;
- tenant as metadata only, never as an ACL;
- Project owner profile plus canonical project ID if Projects are eventually supported;
- request ID and actor kind.

Reject or ignore caller-supplied board/profile/actor values that disagree with the authenticated capability. Test duplicate task IDs across boards and duplicate Project slugs across profiles.

## Release-pinned no-core seam findings (v0.18.2)

The 2026-07-09 audit pinned stable Hermes to package `0.18.2`, tag `v2026.7.7.2`, peeled commit `9de9c25f620ff7f1ce0fd5457d596052d5159596`, and annotated tag object `b7751df34688835a108e0d630f3495fc11f3df79`. The inspected `main` snapshot was `111544d544d6cf6efed9875e116f2daeb76a1211`. Fifty-eight selected seam-function source segments were identical between that stable tag and `main`; this is evidence for that snapshot, not a future compatibility promise.

Additional exact pitfalls:

- `PluginContext.register_tool(..., override=True)` plus `plugins.entries.<plugin_id>.allow_tool_override: true` is the supported replacement path for the nine `kanban_*` names. Use a distinct plugin toolset. `ToolRegistry.register()` only enters its collision branch when the old and new toolsets differ; reusing literal toolset `kanban` can bypass the intended explicit cross-toolset collision check and should not be treated as a supported authorization shortcut.
- Enabling is per active profile home: install under that profile's `$HERMES_HOME/plugins`, include the plugin in `plugins.enabled`, grant the override entry, and repeat for each worker/orchestrator profile. `HERMES_SAFE_MODE=1` disables this entire path.
- The native dashboard's `_conn()` calls `init_db()` even on GET handlers. Treat native dashboard reads as potentially mutating/migrating. Disable the bundled Kanban dashboard through `plugins.disabled: [kanban]`; the contemporaneous docs' `dashboard.plugins.kanban.enabled: false` advice is not what the source gate reads.
- Tagged source authenticates `/api/plugins/*` through the dashboard session/OAuth gates even though one paragraph of the same official Kanban page says plugin routes are unauthenticated. Preserve this as a docs/source compatibility discrepancy rather than choosing the prose silently.
- `kanban.dispatch_in_gateway=false` disables both the embedded dispatcher and the native notification watcher. There is no independent notifier-only switch, so an external broker must own durable notification delivery rather than assuming native notifications survive dispatcher shutdown.
- `kanban_tools.py` describes a TUI poller in `tui_gateway/server.py`, but no source path that consumes `kanban_notify_subs` or claims unseen events for `platform="tui"` was found in the pinned tree. Keep TUI delivery on compatibility hold until runtime/source evidence closes this gap.
- Project `board_slug` is an advisory field: task creation does not enforce it. Native task creation resolves a Project against the creator's per-profile `projects.db`, stores only the canonical `project_id`, materializes path/branch values, and silently drops an unresolved link. Broker records therefore need `project_owner_profile`, canonical `project_id`, bound board, and path/branch snapshots, with fail-closed validation.
- Omit `HERMES_KANBAN_TASK` for broker-authoritative workers. Besides exposing native tools, it activates auto-heartbeat, turn-budget failure writes, and goal-loop native DB reads/blocks outside plugin tool handlers. Use broker-prefixed task/run/claim variables and inject lifecycle guidance explicitly.

For a compatibility-hold ledger, record at minimum: ledger schema version; release package/tag/commit/tag-object/signature state; audited `main` SHA; observed runtime version/SHA/dirty paths; adapter version/SHA/plugin ID; per-profile enabled and override-grant state; native dispatch/dashboard/task-env gates; each source path + symbol + expected signature + UTF-8 source-segment SHA-256 + contract-test result; and per hold `hold_id`, expected/observed pin and fingerprint, change kind, impact, blocking flag, required action, owner, status, evidence, approval/waiver timestamps, and resolution. Whole-file hashes are useful for low-churn modules; source-segment hashes avoid false holds when unrelated code shifts line numbers in large files.

## Native adapter audit additions (main snapshot `c67aab763dd68a26a07bd3c7aec0443268c76225`)

Re-check these against the selected release; they are source-confirmed implementation behavior, not a public stability promise.

### Operation-map method

For a complete native adapter map, inspect the argparse tree before the DB module. Record every verb and alias, then trace each handler to: exact native signature and return type; direct SQL; secondary transactions; filesystem/process/network behavior; and output/exit-code translation. In this snapshot, the top-level Python entrypoint calls `args.func(args)` without propagating its returned status, so subprocess exit code can remain zero when the Kanban handler returned `1` or `2`. Native callers should consume the function result or structured return, not infer success from `python -m hermes_cli.main` alone.

### Read-only, dry-run, and atomicity traps

- There is no supported read-only Kanban connection helper. `connect()` can create parents/files, enable WAL, run integrity checks, and migrate schema. Every non-board Kanban CLI verb also calls `init_db()` before its handler.
- `kanban list` mutates through `recompute_ready()` before `list_tasks()`.
- `dispatch_once(dry_run=True)` is not globally read-only: stale-claim release, stale/crash detection, max-runtime enforcement, and ready recomputation run before dry-run suppresses assignment/spawn. A broker preview needs a pure planner or disposable snapshot.
- CLI bulk transitions loop one task at a time. Complete, block, schedule, unblock, promote, archive, and purge permit partial success. Block/schedule/unblock reason comments are separate transactions from state transitions.
- `claim_task()` atomically claims and creates a run, but CLI claim resolves/creates a workspace and persists its path later. `complete_task()` atomically closes task/run/event, then separately scans advisory references, clears counters, promotes children, cleans workspace/tmux state, and fires hooks. `reclaim_task()` may terminate a worker before its DB CAS and resets failure state later.
- `create_swarm()` is not one graph transaction and can leave partial topology. `decompose_triage_task()` does create its child graph/root transition atomically, with ready promotion afterward.
- Board metadata/current pointers and board create/remove are filesystem operations around independent SQLite initialization. Project-to-board binding updates per-profile `projects.db` first and synchronizes board metadata best-effort afterward; `Project.board_slug` does not route `create_task()`.

### Concrete safety defects to test

- `boards set-default-workdir <slug>` with no path passes `None`; metadata update interprets that as “leave unchanged,” so the documented clear path is a no-op for an existing value. Native callers currently need `default_workdir=""`.
- CLI GC validates archived scratch paths with `path.relative_to(scratch_root)`, which accepts equality. A malformed archived row whose `workspace_path` equals the root can remove the entire scratch root. Require strict descendancy.
- `archive_task()` clears claim/PID fields and closes the run but does not terminate the external worker.
- Native task idempotency is a pre-transaction lookup backed by a non-unique index. Concurrent same-key creation can duplicate; enforce broker request dedup transactionally.
- `create_task(project_id=...)` resolves through per-profile `$HERMES_HOME/projects.db`, not `HERMES_KANBAN_HOME`, and silently drops unresolved projects. A temp Kanban root alone is not a hermetic Project test.

### Real-temp-root probe pattern

When execution is allowed, create a real temporary `HERMES_KANBAN_HOME`; unset `HERMES_KANBAN_DB`, `HERMES_KANBAN_BOARD`, `HERMES_KANBAN_WORKSPACES_ROOT`, and `HERMES_KANBAN_ATTACHMENTS_ROOT`; set `PYTHONDONTWRITEBYTECODE=1`; and clean the root on exit. Exercise public calls in this order: `create_board` → `set_current_board` → `connect_closing(board=...)` → parent/child `create_task` → completion/promotion → `claim_task` → ownership-aware heartbeat → notification subscribe/claim → `list_runs`/`board_stats` → archive/GC. For Project-linked creation, also set a temporary `HERMES_HOME`.

Use direct native assertions rather than CLI process return code. Keep assignees empty or isolate the profile home when avoiding profile/config reads, and reject worktree/`dir` paths outside the temporary root unless that filesystem behavior is under test.

## Runtime tool-override audit additions (`c67aab763dd68a26a07bd3c7aec0443268c76225`)

Re-check these against the selected release; they are source-confirmed runtime details, not stable API promises.

### Count and gating ledger

The native surface is **nine** tools: `kanban_show`, `kanban_list`, `kanban_complete`, `kanban_block`, `kanban_heartbeat`, `kanban_comment`, `kanban_create`, `kanban_unblock`, and `kanban_link`. A task-scoped worker sees seven: all except `kanban_list` and `kanban_unblock`. `kanban_create` and `kanban_link` are worker-visible despite stale comments in the Codex MCP bridge describing them as orchestrator-only.

The profile plugin `kanban-workflow-control-plane` adds three more prefix-matching tools—`kanban_workflow_status`, `kanban_workflow_route`, and `kanban_workflow_action`—but overrides none of the native nine. A process with both surfaces therefore has 12 names beginning `kanban_`. The three workflow tools use a separate `kanban_workflow_control_plane` toolset; status is read-oriented, model route/action calls are preview-only, and the human confirmation path shells out to `hermes -p <profile> kanban ...`. In an exclusive-broker deployment, disable this plugin or merge/port those three surfaces into the broker plugin; do not co-enable a second override plugin and depend on discovery order.

Exact native availability checks:

- `_check_kanban_mode`: `show`, `complete`, `block`, `heartbeat`, `comment`, `create`, `link`; true for `HERMES_KANBAN_TASK` or a profile with the `kanban` toolset.
- `_check_kanban_orchestrator_mode`: `list`, `unblock`; false whenever `HERMES_KANBAN_TASK` is present, otherwise requires the profile `kanban` toolset.

### Safe registration and authorization nuance

For a supported override, require both `ctx.register_tool(..., override=True)` and `plugins.entries.<plugin-id>.allow_tool_override: true`. Register the replacement under a **distinct plugin toolset**, while preserving the native schema, check function, JSON-string handler contract, and emoji. Tool selection is name-based after resolving the native `kanban` toolset, so the worker still receives the replacement name; the distinct toolset is what forces `ToolRegistry.register()` through its explicit collision/authorization/audit branch.

Do **not** reuse literal toolset `kanban` as a shortcut. The registry only treats an existing name as a collision when the old and new toolsets differ; same-toolset replacement can skip the intended collision branch. Even a well-behaved plugin should not normalize this bypass into a pattern.

Preflight all nine names, complete schemas, broker protocol/policy version, and handler availability before the first registration. Registration is not atomic: `PluginManager` catches plugin load exceptions but does not roll back tools already replaced. A mid-loop failure can leave a partial override set. A startup supervisor must therefore attest all nine handler owners before serving work and terminate/quarantine the process on partial load. Protected authoritative storage remains the real fail-closed boundary.

Also note that `model_tools` catches plugin discovery failures and continues with native tools. A failed plugin load is not itself a process-start failure. Against a protected authority this should yield visible denials or shadow-only writes, never native authority access.

### Real manager test, not a fake context

Use a fresh subprocess and disposable `HERMES_HOME`:

1. Stage the plugin under `<temp-home>/plugins/<id>/` and write temporary config enabling it plus `allow_tool_override: true`.
2. Set `PYTHONDONTWRITEBYTECODE=1`; import native Kanban registrations first.
3. Instantiate `PluginManager()` and call `discover_and_load()` so it creates the real `PluginContext`.
4. Assert plugin `enabled`, no load error, all nine names attributed, full-schema fingerprints preserved, check functions mapped correctly, and registry handlers owned by the broker module.
5. Exercise standard `handle_function_call()` with a disposable broker/snapshot for allow, deny, timeout, malformed response, wrong board/task/run/profile, idempotent terminal retry, and authority-committed/snapshot-mirror-failed cases.
6. Run a second fresh process without override permission and assert every built-in remains intact.
7. Test task-scoped and unscoped tool-definition sets separately, then test the Codex MCP process separately.

A permissive `register(FakeContext())` test cannot prove config gating, real path types, loader attribution, discovery order, or registry replacement.

### Codex MCP and finalizer gaps

The Codex app-server callback hard-codes all nine native names and imports `model_tools`, so successful plugin discovery in the MCP subprocess routes calls to overridden registry handlers. It does not expose the three `kanban_workflow_*` tools.

The MCP builder fetches each authoritative Hermes parameter schema into `params_schema` but does not pass that value to `FastMCP.add_tool()` or the decorator fallback. Because the generated callback is only `def _dispatch(**kwargs)`, exact input-schema parity is not established. Require a real MCP `tools/list` assertion; hold Codex compatibility until the advertised schemas match the native fingerprints.

The main conversation loop returns early for `codex_app_server`, before normal `TurnFinalizer`. Consequently the standard iteration-budget `_record_task_failure` bridge and normal finalizer hooks such as `transform_llm_output`, `post_llm_call`, and per-turn `on_session_end` do not execute on that path. Tool hooks may execute inside the separate MCP subprocess, without equivalent AIAgent lifecycle context.

### Snapshot terminal-state requirements

Core worker behavior bypasses tool handlers and touches `HERMES_KANBAN_DB` directly: first-turn task-body/image lookup, auto-heartbeat, goal-mode task/status reads, goal-budget `block_task`, and normal-runtime iteration-budget `_record_task_failure`. A compatibility snapshot must therefore carry the task row, title/body, goal settings, exact task/run/claim identity, active run, and enough dependency/comment/event context for native worker reads.

After broker-accepted completion, mirror `done`, cleared claim/PID/current-run state, closed run with `outcome=completed`, summary/metadata, and completion event before returning ordinary success. After a broker-accepted block, mirror the actual landed state (`blocked`, dependency `todo`, or recurrence `triage`), closed blocked run, cleared claim/PID, and corresponding event. Goal mode exits explicitly on `done`/`blocked` and stops on other non-running/non-ready states, so stale or approximate status mirroring can create extra turns or split-brain blocks.

Do not replay arbitrary local snapshot mutations into authority. Goal-budget and turn-finalizer fallback transitions need a narrow supervisor reconciliation contract bound to the broker-issued task/run/claim capability and idempotent request journal. Broker liveness must come from a trusted supervisor/process handle, not snapshot auto-heartbeats.

## Completeness-proof and task-order audit additions

### Independent operation inventory

Do not accept a green “ledger coverage” test when both sides are curated by the same implementation. A common false proof is:

1. a checked-in contract lists only selected callables;
2. the operation ledger maps exactly those callables;
3. the test asserts contract equals ledger;
4. live parser verbs, public mutation helpers, auxiliary modules, dashboard routes, and dispatcher-only writers are absent from both.

Build the comparison set independently from the pinned source:

- parse the complete CLI verb/alias tree and global/per-command flags;
- enumerate registered model-tool names and schemas;
- inventory public `kanban_db` functions plus private helpers actually called by CLI/dispatcher paths;
- inspect `specify`, `decompose`, `swarm`, notifier, dashboard, Projects, backup/restore, and GC modules for direct writes;
- classify each as `read`, `mutation`, `dispatcher`, `auxiliary`, `client_preference`, or justified infrastructure/exclusion;
- require an explicit canonical-board rule, authority owner, approval class, retry/idempotency class, adapter function, broker operation, result shape, and enforce-mode behavior for every row.

A missing live surface makes the completeness claim **incorrect**, not merely untested, when the test itself asserts exhaustive coverage.

### Dependency-safe implementation order

Reconstruct the dependency graph before accepting numbered task order. For an external broker, the safe shape is usually:

1. pinned adapter and exhaustive operation map;
2. real Unix socket server/transport (protocol structs alone are not a service);
3. common client with request-ID-safe retry/recovery;
4. scheduler/lease contract foundation;
5. user launcher/workspace foundation;
6. online compatibility snapshots and attachment/path handling;
7. snapshot-backed auxiliary proposal extraction and authoritative CAS application;
8. dispatcher integration of proposal-backed auto-decompose;
9. human UX plugin;
10. exact native-name overrides and fresh-process ownership attestation;
11. staged profile/config/guide migration;
12. live enablement only at the approved install/cutover step.

Split cycles explicitly. For example, dispatcher lease issuance may precede launcher execution, while auto-decompose integration must wait for the proposal runner; implement these as separate scheduler foundation and integration slices. Likewise, do not enable a profile-local plugin before its reviewed copy exists, and do not disable embedded dispatch before the broker, launcher, notifications, rollback, and cutover approval are ready.

### Read-only execution ledger

When runtime tests are allowed inside an otherwise no-edit audit:

- capture commit, `git status --short`, tracked diff names, and untracked count **before and after**;
- distinguish committed baseline, pre-existing dirty working tree, and the exact tree the test actually exercised;
- set `PYTHONDONTWRITEBYTECODE=1`, disable pytest cache (`-p no:cacheprovider`), and force fixtures into an isolated temporary root;
- inspect the suite for generated files, service calls, live DB/config paths, and cleanup behavior before running it;
- never report “the pinned commit passed” when tests actually ran against dirty working-tree code;
- report test counts as evidence for present behavior only—green tests cannot prove absent task surfaces.

## Minimum production gates

- immutable, pinned TCB and verified import origins;
- distinct broker/worker/human principals;
- local-FS ACL proof covering DB, sidecars, locks, metadata, and ancestors;
- run-scoped capabilities with replay resistance;
- trusted cross-UID launcher and cgroup/process-handle supervision;
- one fail-closed broker instance and per-board serialization;
- pure broker read plane; native dashboard mutators unreachable;
- explicit board/path-to-connection verification;
- supervisor-side heartbeat;
- goal/Project/worktree restrictions until dedicated tests pass;
- exhaustive direct-writer negative tests;
- online backup, restore fencing, upgrade clone test, and proven rollback or declared irreversibility;
- durable request/audit reconciliation.

## Safer alternatives

1. **External queue is authoritative (preferred without upstream changes).** Use a small owned schema/API and generic Hermes workers with broker-only tools.
2. **Narrow native-DB pilot.** One board, scratch only, no goal mode/Projects/worktrees/decomposer/review/notifier/attachments/native dashboard; state the reduced guarantee.
3. **Upstream mutation kernel.** For full native behavior, add typed pre-commit mutation/context/approval enforcement at the actual Kanban write boundary; keep external plugins as UX.
