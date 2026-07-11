# Hermes Kanban Control-Plane Audit Notes

Use this reference when auditing a proposed Hermes plugin that wraps Profiles, Projects, Kanban, hooks, or slash commands. Re-check live docs/source because these contracts evolve.

## High-value probes

- Pin the latest stable release, then record the installed `hermes --version`; treat an installed carried commit separately from both stable and `main`.
- Use `hermes <surface> --help` and nested verb help for behavior without reading runtime databases or configuration state.
- Introspect public Python signatures (`PluginContext.register_*`) and the manifest dataclass/parser; declarations in `plugin.yaml` may be accepted but ignored.
- Check the central slash registry for both exact conflicts and plugin-command dispatch behavior.
- Inspect hook timing, return semantics, process location, and whether the hook is pre-commit, post-commit, observer-only, or veto-capable.
- Make test doubles reproduce real argument types and validation. A permissive fake context can make an invalid registration probe pass.

## Durable contract distinctions

- Profiles scope Hermes state through `HERMES_HOME`; normal `hermes -p NAME` startup does not necessarily set `HERMES_PROFILE`. Plugin code should prefer `ctx.profile_name` over guessing from environment variables.
- Projects are per-profile; Kanban boards are rooted at the shared Hermes root. Do not describe both as having identical profile scope.
- Project CLI selectors may accept only ID/slug even though GUI project tools resolve display names. Board CLI `--board` is slug-oriented. A human-name UX therefore needs explicit name-to-slug resolution and ambiguity handling.
- Kanban workers and configured orchestrators receive different `kanban_*` schemas. Human CLI/slash/dashboard operations are separate front doors.
- Forward-compatible columns such as workflow or step keys do not prove a shipped workflow-routing engine. Look for dispatcher reads, transition APIs, and tests before claiming enforcement.
- A profile-local `pre_tool_call` hook cannot enforce policy over native CLI, dashboard, cron, scripts, or processes where the plugin is not loaded. Post-commit lifecycle observers also cannot serve as pre-write vetoes.

## Common implementation-plan failures

1. A bundled skill registration must pass the actual `SKILL.md` `Path`, not a directory or string accepted only by a fake verifier.
2. Manifest fields outside the parsed `PluginManifest` contract are descriptive/inert; runtime `register_*` calls remain authoritative.
3. “Every task everywhere” is a kernel-level guarantee unless all bypass surfaces are operationally disabled. Otherwise scope the claim to work created through the plugin.
4. One task with one assignee is not automatically a multi-stage workflow. Model phases as dependent tasks or require a real workflow-template engine.
5. Verify that route operations actually call native `link`/assign/transition primitives rather than merely writing comments.
6. Confirm block/status enums from live CLI. Human review labels invented by a plan are not native states unless source proves them.
7. “All boards” must not silently cap enumeration or inspect tasks only on the active board. Test more than the implementation cap and duplicate titles across boards.
8. Self-asserted booleans plus prose are not proof of “100% certainty”; classify that as policy/advisory unless backed by an approval authority.

## Universal enforcement design pattern

When the user wants policy to govern every official Kanban front door, do not extend a profile plugin and call it universal. Trace all production writers first: CLI/slash, model tools, dashboard REST and drag/drop, dispatcher, decomposer/specifier/swarm helpers, gateway recovery paths, and cron/scripts using supported APIs. Inspect for direct SQL writes outside the nominal kernel; a shared database does not prove a shared policy boundary.

Use these design rules:

1. **Define the guarantee.** “Universal across supported Hermes surfaces” is achievable in core. Preventing the same OS user from opening SQLite directly requires a broker that exclusively owns the writable DB—and meaningful tamper resistance requires a separate OS account. State the threat model explicitly.
2. **Enforce before commit.** Add a typed mutation service at the authoritative Kanban write boundary. Evaluate policy after `BEGIN IMMEDIATE`, against the canonical current row state, and before any SQL mutation. Existing post-commit/best-effort lifecycle hooks remain observers and cannot veto.
3. **Carry trusted actor context.** Mutation context should include board, actor kind/id, profile, surface, task/run/session, request id, and approval receipt. Each first-party front door constructs this context; never trust caller-supplied claims that it is a dispatcher, orchestrator, or approved human.
4. **Use finite decisions.** Policy returns `ALLOW`, `DENY(code, reason)`, or `REQUIRE_APPROVAL(challenge)`. Avoid arbitrary plugin rewrites inside the transaction and forbid model/network/external-process calls while the SQLite lock is held.
5. **Make policy board-owned.** Boards are the hard shared boundary; profile-local config is not authoritative. Store a versioned policy/template reference and digest in board metadata or board tables, with explicit `off | audit | enforce` and fail-open/fail-closed semantics.
6. **Make approvals atomic.** Bind challenges/receipts to board, task, workflow step, normalized operation/arguments, policy version, principal, and expiry. Verify and consume the receipt in the same transaction; concurrent reuse must yield exactly one commit. Tool approval bypasses such as YOLO must not silently bypass board governance.
7. **Refactor every writer.** Dashboard direct status/title/priority SQL, CLI handlers, model tools, dispatcher transitions, and helper modules must call the same mutation service. Add a repository check that rejects production `INSERT/UPDATE/DELETE` of lifecycle tables outside the kernel/migrations.
8. **Use native workflow state.** If the stable schema reserves workflow/template/step fields but the dispatcher ignores them, label them forward-compatible—not shipped routing. A v2 engine should atomically close the current step run, validate handoff evidence, advance the step, assign the next profile, and mark the task done only at a terminal step. Keep task dependency graphs for parallel fan-out/fan-in.
9. **Keep the plugin as UX.** A control-plane plugin can preview, resolve human selectors, install declarative templates, and explain denials, but core remains the authority. Third-party executable policy code inside write transactions is a deadlock and consistency risk.
10. **Stage upstream work.** Prefer an RFC, then audit-only mutation/context plumbing, single-service refactor, approval receipts, workflow-template routing, and only then an optional local broker.

Minimum adversarial validation:

- the same forbidden mutation is denied through every official surface;
- denial produces zero board mutation except a policy-decision audit row;
- malformed/expired/replayed/wrong-scope approvals produce zero mutation;
- two concurrent uses of one receipt produce exactly one success;
- unknown policy in enforce mode fails closed;
- audit mode preserves behavior while recording the counterfactual decision;
- legacy boards with policy off remain compatible;
- multi-board tests prove isolation;
- no production lifecycle-table writer bypasses the mutation service;
- policy evaluation performs no unbounded or external work under the write lock.

## Exhaustive native-operation and ledger audits

When a broker or compatibility layer claims complete parity with Hermes Kanban, use an independently derived inventory rather than starting from the broker's contract:

1. **Recover the parser tree structurally.** Preserve nested route paths, aliases, positionals, and flags per route. A flat set of parser names collapses repeated names such as top-level and nested `list`/`show`, drops aliases, and cannot prove command coverage.
2. **Classify executable behavior, not command labels.** Trace every leaf handler in call order. Connection setup may initialize or migrate a database, a list can recompute state, and a dispatcher dry-run can reclaim, terminate, timeout, or promote before suppressing spawn.
3. **Inventory the whole native callable surface.** Parse all public functions, classify read/pure, authoritative mutation, filesystem/process mutation, context-only side effect, and infrastructure. Fingerprint private dispatcher seams whose signatures or call order are compatibility-critical.
4. **Find auxiliary writers independently.** Scan production callers of native mutators plus direct SQL/filesystem/process effects. Include model tools, dashboard handlers, gateway watchers/slash auto-subscriptions, specifier/decomposer/swarm helpers, worker heartbeats/finalizers, Project metadata sync, GC, and backup/restore.
5. **Compare five layers separately.** For each discovered surface record: source route/caller, native callable or direct seam, contract entry, ledger row or justified exclusion, wrapper/dispatcher support, and independent test. Do not count a contract-derived test as proof the contract is exhaustive.
6. **Split semantic operations from aliases and composites.** Aliases share an operation; composites such as list+recompute, claim+workspace persistence, block+comment, create+auto-subscribe, and dispatch ticks must explicitly reference every sub-operation.
7. **Rebuild implementation batches from runtime dependencies.** Contract/schema inventory precedes wrappers; transport/server precedes clients and consumers; lease/snapshot/launcher foundations precede dispatcher integration; proposal isolation and snapshots precede specify/decompose/swarm application; restore and ACL cutover come last.
8. **Detect source drift during the audit.** Record commit and worktree state at both start and finish. If files change concurrently, re-read changed consequential artifacts, distinguish immutable HEAD from working-tree observations, and state which findings remain valid. Never attribute concurrent edits to the audit.

For literal read-only audits, prefer AST/text introspection with bytecode disabled, avoid tests that create caches unless permitted, and finish with repository status checks. Report documentary/source verification separately from runtime tests.

## Exact current-HEAD acceptance matrices

When the user asks for **current HEAD** rather than the mutable checkout, treat the Git object as the evidence boundary:

1. Record `git rev-parse HEAD` and worktree status before reading.
2. If the worktree changes concurrently, do not silently mix those edits into the audit. Read consequential committed artifacts from `HEAD:<path>` (for example, via `git show`) and enumerate tracked HEAD paths with the Git tree, not the filesystem. Reconfirm that HEAD itself did not move.
3. State that line citations and findings refer to the immutable commit, identify concurrent worktree drift separately, and never attribute those edits to the auditor.
4. Avoid importing the mutable checkout to prove HEAD content. If structural extraction is needed, parse `git show` output directly; otherwise an import can observe uncommitted modules while the report claims committed behavior.

For each remaining surface, build the matrix from executable behavior rather than identifiers. Record:

- exact parser route, aliases, positionals, flags, and result shape;
- exact callable signatures and whether each is merely in the exhaustive public-signature inventory or promoted into the selected operation contract/ledger;
- direct SQL, filesystem, process, config, and multi-transaction effects;
- protocol registration, argument validation, scope resolution, wrapper/dispatch support, policy/journal handling, and independent behavior tests;
- the concrete gap, without inferring semantics from names.

Keep these distinctions explicit:

- An exhaustive `public_callables` signature pin proves source-surface awareness, not that a callable is broker-exposed. A narrower selected `callables` set, ledger row, protocol operation, dispatcher entry, and behavior test are separate acceptance gates.
- A parser digest pins syntax, not helper implementation semantics or aggregate atomicity.
- A store-level foundation is not an exposed operation. Compare identity keys, idempotency, deletion/deactivation, ordering, cursor, and return-shape semantics before claiming parity.
- A composite helper is atomic only if one transaction encloses all authoritative writes. Sequential calls to individually atomic helpers can commit a partial graph. Check retry behavior before the final topology/idempotency marker is written.
- Filesystem plus SQLite cleanup is normally multi-phase. Report containment guards, board scoping, partial completion, and crash/retry behavior rather than calling the whole command transactional.

For a strict-TDD recommendation, choose the smallest real public behavior slice, not the smallest file change. Prefer a read-only slice that extends an existing dispatcher path when it can be verified against real temporary native state. For composite atomicity, design a RED test with a deterministic late validation failure through real public functions (for example, an invalid later child specification) so partial commits are exposed without mocks or fault-injection stubs.

## Reporting pattern

Return an outcome-first ledger with: baseline release and installed drift; confirmed contracts; contradicted assumptions; hard blockers; UX evidence; and a read-only audit record. Separate a defensible UX synthesis from claims directly mandated by sources.