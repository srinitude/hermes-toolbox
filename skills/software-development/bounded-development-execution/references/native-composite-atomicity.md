# Atomicity audits for composed native helpers

Use this checklist when a pinned first-party helper composes several native mutations but acceptance requires one atomic operation.

## Audit before wrapping

1. Read the exact pinned helper and every called mutation.
2. Identify transaction boundaries: a helper that calls functions which each open and commit their own transaction is not atomic.
3. Inspect pre/post-commit side effects, especially lifecycle hooks, workspace cleanup, notifications, filesystem writes, and process signals.
4. Check module identity and concurrency. Temporarily monkeypatching a shared imported module can alter unrelated board/runtime calls even when normal writes use per-board locks.
5. Test late failure after at least one successful child mutation and verify tasks, links, comments, events, and runs all roll back.
6. Inspect retries: a root-only idempotency key is insufficient when a failure can occur before durable topology metadata is written.

## Unsafe pseudo-fixes

Do not claim atomicity from:

- An outer transaction around helpers whose inner functions execute `BEGIN`/`COMMIT`.
- A process-global `write_txn` monkeypatch or no-op nested context.
- SAVEPOINT SQL authored in the adapter when the contract requires calling native mutation functions unchanged.
- Backup-and-restore compensation; readers may observe intermediate commits and external side effects cannot be retracted.
- Best-effort deletion of partially created graph nodes.

An outer rollback is actively incorrect when a nested native operation fires hooks or filesystem cleanup before the outer commit: consumers can observe a completion that later disappears.

## Correct resolution

Fail closed and record an explicit compatibility hold when the native helper cannot satisfy atomic acceptance unchanged. Require an upstream/pinned implementation that owns one transaction and defers external side effects until commit. If authority and policy bindings use separate databases, use a reserved recovery state: apply native atomically, verify exact topology, finalize all sidecar bindings/edges in one sidecar transaction, and recover sidecar finalization without replaying native graph creation.

Keep protected upstream checkouts unchanged. If a patch is needed, prepare it in an isolated review artifact or wait for an official pinned release; do not silently vendor behavior while claiming official parity.
