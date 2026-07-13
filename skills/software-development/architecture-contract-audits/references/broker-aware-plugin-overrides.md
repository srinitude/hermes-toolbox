# Broker-Aware Hermes Plugin Override Audits

Use this reference when auditing a Hermes plugin that should mediate native tools through an external policy broker.

## Evidence boundaries

Freeze and report separately:

1. broker repository HEAD and worktree drift;
2. pinned Hermes source HEAD;
3. plugin source tracked in the broker repository;
4. currently installed plugin copies and selected non-secret trust config;
5. tests present versus tests actually executed.

An installed monolithic plugin is not repository implementation. A compatibility contract that pins `PluginContext.register_tool` is not an override plugin.

## Four required equations

Audit all of these independently:

1. native tool names = override registrations;
2. pinned native input schemas = override schemas;
3. native tool visibility predicates = override `check_fn` behavior;
4. native behavior = broker operation, explicit normalization, or visible `compatibility_hold`.

Exact schemas alone do not prove output or semantic parity. Compare native handler defaults and side effects with broker argument contracts and result shapes.

## Registration contract

For every native override require:

- exact native name;
- original native toolset, usually needed for existing profile filtering;
- `override=True` even when a same-toolset registry implementation might overwrite without it;
- explicit `plugins.entries.<plugin-id>.allow_tool_override: true` in approved consumers;
- preflight of every schema, handler, environment requirement, and compatibility pin before the first registration;
- post-registration ownership checks for every handler.

Hermes override registration is per-tool rather than transactional. A later failure can leave a partial override set, so startup must fail before the first override when preflight is incomplete, and a supervisor or real-manager test must verify complete ownership before work is served.

## Broker request construction

Derive trusted context instead of accepting model-controlled identity:

- profile from `ctx.profile_name`;
- worker task, board, run, claim lock, socket, and capability from trusted launcher environment;
- fresh bounded request id locally;
- actor JSON as metadata only;
- canonical selectors and policy identity at the broker.

Reject caller board/task claims that disagree with worker scope. Do not silently fall back to native CLI, direct SQLite, or another socket when the broker is unavailable.

## Human and model separation

Model-callable tools must not call an endpoint that also mints human approval tokens. If the broker only offers an evaluate-and-mint operation, add a non-minting preview operation or keep model previews purely descriptive and defer authoritative resolution to the human path.

A human slash command may call the broker approval-preview endpoint and then execute the exact returned request. It must not replace broker approval with an in-memory token bound only to rendered CLI commands.

Same-process model tools and slash commands share PID/UID. Code-path separation is useful but does not establish a strong security principal; production strong enforcement still needs a distinct operator principal or out-of-band grant that model code cannot invoke.

## Semantic parity checklist

For each native tool compare:

- default task/board resolution;
- required versus optional arguments;
- environment-derived run and claim fields;
- idempotency derivation;
- redaction and metadata normalization;
- pre-read promotion or other hidden writes;
- enriched output such as comments, runs, graph edges, and worker context;
- notification/auto-subscription behavior;
- worker versus orchestrator visibility;
- cross-task and cross-board scope;
- unsupported Projects, worktrees, goal mode, skills, or arbitrary directories.

Unsupported behavior may be an acceptable explicit compatibility restriction, but it must return a structured visible hold rather than disappear or silently weaken policy.

## Control-plane audit traps

- Native `list` may promote dependencies; a broker `task.list` that only reads is not behavior parity.
- Conversely, adding native-list parity by hiding `recompute_ready` behind a flag on a ledger-classified read is a policy bypass: trace argument-dependent callables, writes, approval class, journaling/recovery, retry behavior, and result shape. If a mode flag changes any of those, use a separately classified operation/variant or extend the ledger contract explicitly; do not leave one operation ID claiming both semantics. Check whether the generic public argument validator accepts the flag—even if only the plugin is intended to set it—because that makes the alternate behavior caller-selectable.
- Native `show` may aggregate comments, events, runs, graph edges, and worker context; a task row is not equivalent. An enriched-envelope flag must also be reflected in the operation ledger's complete callable and result-shape contract. Exhaustive coverage tests must compare the callables actually reached by each registered tool route, not merely prove that every ledger callable appears somewhere.
- Compare the complete model-visible handler JSON, not only the nested payload. A broker wrapper such as `{"ok": true, "result": ...}` is not an exact override when the pinned native handler returns the aggregate object directly; success and error envelopes both require parity or an explicit compatibility restriction.
- Audit pagination before the handler as well as inside it. A generic scope resolver that preloads a fixed maximum and rejects `len >= max` can make an otherwise exact `limit + 1` native pagination envelope fail on large boards before dispatch. Include archived rows when deriving the triggering cardinality if the resolver does. Test below-boundary, exact-boundary, and over-boundary behavior through the public route for both list and point-read tools; a point read must not become unavailable merely because the board is large.
- A single canonical-board broker runtime cannot provide multi-board mutation UX without explicit board-to-broker routing.
- Project/profile catalogs are separate from Kanban authority; if the human control plane promises name-based Project routing, identify the broker-backed selector/catalog contract.
- A plugin hook that scans terminal text is defense-in-depth only and cannot establish mediation outside processes loading the plugin.
- A library `serve()` used by fixtures is not an operable broker service.

## Real strict-TDD slices

Prefer dependency-ordered vertical slices:

1. fresh-process real `PluginManager` discovery, trust denial, exact schema, visibility, and handler ownership;
2. one real broker-backed read override with outage/no-fallback proof;
3. worker lifecycle tools with real capability, PID, run, claim, and terminal replay;
4. related-work tools with explicit narrower-scope and compatibility-hold tests;
5. orchestrator-only read/human-approval surfaces;
6. broker-aware custom control-plane tools and slash confirmation;
7. adversarial startup proving no partial override set.

Use a real Unix socket, temporary native/policy databases, kernel peer credentials, and a real PluginManager. Do not substitute a fake registration context or mocked broker transport.

## Retry review

Compare client retry behavior with the real server duplicate-request policy. A custom socket fixture proving that identical frames are retried does not prove the real server will accept the repeated request id. Test the actual server after a lost response or classify the route as non-retryable until replay semantics are explicit.
