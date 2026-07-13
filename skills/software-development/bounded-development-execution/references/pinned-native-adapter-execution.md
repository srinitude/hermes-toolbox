# Pinned Native Adapter Execution Pattern

Use this reference when a standalone component must call a pinned upstream Python implementation without modifying it.

## Trust order

1. Verify the tracked contract and exact upstream commit before importing or opening native state.
2. Treat contract inspection failure, wrong commit, signature drift, or tool-schema drift as `compatibility_hold`.
3. In production, reject writable source roots/files, symlink escapes, modified relevant tracked files, and imported module origins outside the verified root.
4. Permit writable checkouts only through an explicit immutable development/test mode; never silently downgrade production.

A compatibility hold should create no runtime database, migration, metadata, lock, or workspace files.

## Process-global isolation without destroying authority-level concurrency

Python imports, `sys.modules`, `sys.path`, bytecode settings, and `os.environ` are process-global. A single lock around every native callback is safe but can violate a requirement that unrelated boards/tenants progress independently. Choose the isolation model from the concurrency contract:

- For a short-lived verifier or a library that may load several source roots, keep exact-source import plus environment replacement/restoration under one real re-entrant lock and restore in `finally`.
- For a dedicated broker process pinned to exactly one verified source root, load and origin-check the official module once, reject any later second source root, and retain the verified root on `sys.path` for lazy upstream imports.
- Replace ambient path resolution with context-local authority scope (for example a `ContextVar` carrying runtime root plus canonical board). Patch only the verified module's public path resolvers so database, workspace, and attachment paths derive from that scope rather than inherited environment pins or current-board pointers.
- Serialize mutation callbacks with locks keyed by `(runtime_root, board)`. Use a separate metadata lock for root-wide board metadata. Do not use one process-wide operation lock when unrelated boards must progress concurrently.
- Prove both sides with real callbacks: same-board writers cannot overlap, while two different-board writers can meet at a barrier and complete against separate real databases.

For Kanban-style authority paths:

- Set an explicit broker-owned runtime root and isolated profile/home.
- Ignore inherited direct database, board, workspace, and attachment pins.
- Pass the canonical board explicitly to the public connection helper.
- Resolve the selected database through the public native resolver and verify containment under the runtime root.
- Import the official package name from the verified source, then validate both package and module origins.
- Include lazy-import behavior in the test: removing the source root from `sys.path` immediately after the first import can make later official calls fail when they import sibling top-level modules on demand.

Avoid private APIs, direct authority-table SQL, CLI output parsing, and subprocess exit codes when stable public native functions exist.

### Python-version-stable source contract digests

Do not persist `ast.dump()` hashes for pinned source contracts across Python minor versions. AST node shapes can gain fields (for example `FunctionDef.type_params`), creating a false compatibility hold with unchanged upstream source. Parse with AST to locate the exact declaration, then hash `ast.get_source_segment(source, node)` bytes. Verify the same contract under every supported project Python runtime; source formatting changes may intentionally hold because the pinned bytes changed.

## Complete operation ledgers and wrappers

For a broker that must cover a pinned native surface, make completeness executable rather than relying on a handwritten list:

- Store immutable metadata for every broker operation: operation id, exact official callable(s), registered model-tool surface, read/mutation class, worker/human eligibility, approval class, retry class and behavior, normalized result shape, and stable public error class.
- Require exact-set coverage in an adversarial test: ledger callables plus explicitly justified infrastructure exclusions must equal the pinned contract callables; ledger registered tools must equal the pinned registered-tool set; ledger operation ids must equal the broker protocol's native operation ids.
- Give infrastructure exclusions concrete rationales. Connection helpers, authority-root/path resolvers, and deployment-only board provisioning are exclusions only when another verified layer owns them.
- Represent a missing official mutator as an explicit `compatibility_hold`. Never fill the gap with direct SQL or a private upstream API.
- Wrapper signatures must be fixed and bounded. Validate every scalar, mapping, and collection before the adapter callback; pass only explicit official keyword arguments, never arbitrary `**kwargs`, ambient board/profile authority, actor JSON, approval/capability tokens, or private profile paths.
- Exact-operation approval includes exact argument bytes/values. Validation must not silently trim, case-fold, rewrite, reorder, or otherwise transform a value after its request fingerprint was approved. Either canonicalize before fingerprinting or validate and return the original value unchanged; add a regression test with leading/trailing whitespace or another transformation-sensitive value.
- Preserve upstream concurrency guards. Pass explicit claim owner and TTL values so environment defaults cannot redirect semantics; pass expected run ids where supported.
- Treat compound official operations as one scoped contract. A heartbeat wrapper should bind one task, run, claim lock, and TTL, call both the claim-extension and worker-heartbeat functions, and fail when either refuses the scope. Real tests should cover stale run and wrong claim without test doubles.
- When the upstream exposes a compound mutation only as separate transactions, validate every shared scope guard before the first call and serialize the broker writer. Document that the sequence is not intrinsically atomic, test that known stale-scope failures cause zero mutation, and route crash ambiguity through the operation journal/recovery path rather than claiming rollback that the upstream API cannot provide.
- Prove logical reads are non-mutating after the initial native migration by comparing normalized SQLite state snapshots before and after board/task list and task read operations.
- Exercise idempotency-key retries, native cycle/self-link rejection, unknown objects, stale CAS values, invalid bounds, and unsupported operations against real temporary roots.

When a repository and an installed dependency both expose a top-level `tests` package, invoke focused tests as `python -m pytest ...` from the repository root. The `pytest` console entry point can resolve the installed package first even when a direct Python import resolves the local package.

## Public result boundary

Return deeply immutable normalized values. Convert upstream dataclasses, mappings, sequences, enums, and paths before leaving the isolated import boundary. **Reject every unknown result type** instead of passing it through: a callback must not leak a live database connection, module, file handle, iterator, or other mutable native object after the isolation context closes. Mapping keys should be validated or normalized without silent collisions.

Keep the public adapter class thin when structural limits count a class from its declaration through all methods. Put verification, invocation, connection, and failure helpers at module scope so the class and each helper stay independently bounded.

Map failures to stable public codes such as:

- `compatibility_hold`
- `native_permission_denied`
- `native_conflict`
- `native_not_found`
- `native_unavailable`

Do not serialize raw exception text to callers. Preserve exception type and detail through an internal audit sink or internal logger; keep that channel separate from the public result.

## Real temp-root tests

Use the actual pinned source discovered through a generic environment override or `$HERMES_HOME/<source-checkout>`, never a tracked user-specific absolute path. Exercise real public functions against temporary roots:

- Resolve the explicit board database without creating files.
- Create/list a board and create/read a task through the native connection.
- Seed a conflicting current-board pointer and hostile inherited path pins; prove they cannot redirect authority and are restored afterward.
- Use an actual wrong-commit clone to prove zero-file compatibility hold.
- Use real filesystem permissions and malformed temporary database bytes for permission/unavailable paths.
- Trigger not-found/conflict through public native operations rather than mocks or synthetic exceptions.
- Verify production rejection of writable and symlinked sources.

### Guard against fixture-driven native reconciliation

Some official Kanban calls reconcile other tasks while setting up an otherwise unrelated task. Creating or completing a later fixture can move an earlier blocked or pending subject back to a ready state, making a promote or CAS test fail for the wrong reason.

- Assert every setup mutation result instead of discarding it.
- Build unrelated tasks first, then put the subject into its exact required native state last.
- Re-read the subject immediately before the broker call and assert status, run id, and claim lock.
- Keep policy workflow phase/status evidence explicit and verify it is consistent with the official native precondition. If the policy model and native operation encode incompatible transitions, fail closed or redesign the mapping; do not pass the test with an unexplained contradictory fixture.
- When a failed attempt leaves a durable reservation, use a fresh request id or fresh temp root after correcting the fixture so the retry is not confused with the intended recovery path.

Keep adapter infrastructure, security checks, isolation, normalization, and tests in separate bounded files so structural limits remain visible.
