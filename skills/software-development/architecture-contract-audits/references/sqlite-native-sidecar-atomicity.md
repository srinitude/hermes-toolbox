# SQLite Native + Sidecar Atomicity

## Composite native helpers

A native helper that calls several public mutations may still be non-atomic when each mutation owns `BEGIN IMMEDIATE` and `COMMIT`. Inspect transaction implementation, not the helper's name or docstring.

An outer `BEGIN IMMEDIATE` cannot wrap such calls unchanged: SQLite raises `cannot start a transaction within a transaction`. A wrapper that yields when `connection.in_transaction` can collapse row writes into the outer transaction, but it is not automatically safe:

- the transaction function may be a process-global module attribute shared by unrelated board calls;
- overlapping install/restore windows can race;
- inner savepoint/rollback semantics disappear;
- functions may fire lifecycle hooks, cleanup workspaces, or notify observers because they believe their local transaction committed;
- outer rollback can then leave phantom external effects.

The preferred correction is a pinned native composite operation that owns one transaction and defers post-commit callbacks until the outer commit succeeds. If that primitive does not exist and authored SQL is prohibited when native functions exist, report a blocker rather than silently reconstructing native tables.

## Idempotency of graphs

Root-only idempotency is insufficient when child nodes commit before the topology record. A crash can leave a root and some children; retry may find the root but create new children. Atomic graph creation should ensure either:

- no graph rows exist, or
- the complete topology record and every node/edge exist.

Recovery must verify a single exact root, topology marker, node count, disjoint IDs, expected attributes, and every edge before deriving a result. Partial or tampered topology is `recovery_required`, not permission to replay blindly.

## Sidecar acceptance

When native authority and workflow bindings live in separate SQLite databases, use a saga and state the limitation explicitly. Commit authority first, then finalize all sidecar rows plus journal completion and approval consumption in one sidecar transaction. If sidecar finalization fails:

- do not report success;
- keep the journal reservation unresolved;
- ensure dispatch ignores native tasks lacking a complete accepted binding set;
- retry sidecar finalization after exact native post-state inspection;
- never duplicate the native graph.

A normalized relation such as `(board, child_task_id, parent_task_id)` is required for multi-parent joins. Storing only one `parent_id`, choosing an arbitrary parent, or encoding unenforced edges in opaque JSON weakens policy and blocks acceptance.

## High-value real failure tests

Use native validation that occurs after earlier graph nodes would be created—for example, a later worker specification that native task creation rejects—to prove transaction rollback without mocks. For sidecar failure, use a real database constraint or trigger that aborts one later binding insert; assert the batch rolls back, the operation remains reserved, and recovery succeeds after removing the fault without invoking native creation again.

Static adapter checks should reject authored `execute`, `executemany`, and `executescript` calls in modules for operations that have pinned native functions. Broker-owned sidecar SQL is allowed when no native function exists.
