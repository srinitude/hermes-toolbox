# Operator CLI and Dashboard Parity Audits

Use this when a broker-backed human CLI and a read-only dashboard posture claim parity with an immutable native operation ledger plus pinned CLI/tool contracts.

## Separate four equations

Prove these independently:

1. human-eligible ledger operations = operator operation choices;
2. human read/mutation operations = read dispatch/mutation dispatch;
3. native parser verb/path/alias/flag semantics = mapped broker behavior + explicit exclusions;
4. native dashboard route inventory = broker-backed replacement reads + explicitly blocked mutation routes.

A generic `--operation` plus JSON arguments can satisfy (1) and (2) while failing (3). Parser drift detection is not parser-semantic coverage.

## Argument semantic comparison

Compare the broker argument schema and dispatch call against both the pinned native callable signature and every relevant parser/tool argument. Record whether each native field is:

- preserved exactly;
- derived server-side with equivalent semantics;
- deliberately narrowed with an explicit compatibility exclusion;
- silently dropped, default-changed, unit-changed, or made newly required.

Check defaults and composite behavior, not just field names. Common gaps include archived-board defaults, optional versus required assignees, batch task IDs, fleet diagnostics, derived run IDs, dry-run/force flags, list filters, workspace/branch settings, skills, goal mode, initial status, and retention days versus seconds.

Security-driven derivation of actor identity or idempotency keys may be correct, but it is still not native CLI parity unless the contract explicitly classifies the difference.

## Project-reference semantic trace

Trace project references through all stages:

1. CLI parsing and parent-to-child argv preservation;
2. protocol validation and exact preview fingerprinting;
3. project binding lookup and drift verification;
4. board selection;
5. resolved project identity retained in request scope;
6. native mutation dispatch;
7. persisted native task `project_id`, workspace kind/path, and deterministic branch behavior.

A project selector that merely resolves the board is not equivalent to native `--project`. Watch for a resolver returning `project_id` followed by an intermediate helper that returns only the board string and silently discards project identity.

## Read no-fallback proof

Inspect the production client and operator callsite. Require socket-only failure behavior and prohibit imports/calls to native DB helpers in the consumer. Keep this distinct from the broker's authorized native read adapter. Also report honestly when native connection helpers can initialize or migrate a database during a logical read.

## Exact mutation confirmation

For every human mutation, prove one generic path enforces:

- broker-generated preview;
- exact equality of operation, request ID, profile, actor, board, project reference, and validated arguments;
- approval token and fingerprint binding;
- display with secrets removed;
- explicit interactive confirmation;
- execution of the exact previewed request only;
- cancellation/non-TTY behavior performs no authority mutation.

One end-to-end mutation test supports the generic mechanism, but add a static exhaustive equation showing every human mutation reaches it.

## Dashboard enforcement versus declaration

Inventory the pinned dashboard backend by HTTP method and WebSocket transport. Compare all routes, including mutations outside the native operation ledger: attachments, bulk updates, run termination, dispatch, project/board switching, profile edits, orchestration settings, and auxiliary specify/decompose routes.

A JSON posture saying `mutation_transport=disabled` is only declarative when no production component loads it to unmount or gate routes. Acceptance needs:

- bundled native plugin disabled or mutation routes request-gated;
- WebSocket handling included in the disable mechanism;
- replacement read request factory and authenticated broker client;
- broker-backed fidelity for every retained GET/stream;
- non-GET rejection tests and unchanged authoritative state;
- a real-process dashboard principal/socket proof.

Report two separate results: whether the manifest exactly lists ledger operations, and whether deployed/runtime code actually enforces the posture.

## Read-only verification recipe

Use immutable SHAs for both repositories. Prefer no-bytecode static Python probes to:

- compare ledger/operator/schema/dispatch sets;
- inspect the pinned compatibility contract;
- AST-inventory dashboard decorators by method/path;
- parse candidate modules;
- recheck both worktrees for drift.

Do not describe these probes as test execution. If the audit boundary forbids tests, report source tests present versus tests actually run.
