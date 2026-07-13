# Native launcher lifecycle wrappers

Use this reference when a broker or sidecar launcher acknowledges process start/failure against a pinned native task database.

## Fixed native invocation boundary

Expose fixed, bounded methods through the existing native operations facade; broker lifecycle code should not call arbitrary adapter callbacks directly. Inside one verified adapter session, invoke the pinned native helper with the session-owned API and connection:

```python
session.api._set_worker_pid(session.connection, task_id, worker_pid)
blocked = session.api._record_spawn_failure(
    session.connection, task_id, error, failure_limit=failure_limit,
)
```

Private helpers must be explicitly pinned in a dedicated non-public contract section; do not add private names to a public-callable set or its exhaustive operation-ledger equation. Record a fixed repository-relative origin, exact AST-unparsed signatures, and SHA-256 digests of complete function source segments. The checker must hard-code the trusted origin instead of following a path supplied by contract data, and a missing helper must yield a specific compatibility reason rather than raising into a generic contract-unavailable result. Test origin, signature, digest, and deletion drift independently.

## Derive launched-worker operations from the pinned consumer

Do not copy a plan list or trust comments that label tools “orchestrator-only.” Derive worker-visible tools from pinned registrations and their executable worker visibility gate, then map those tool names through the native operation ledger. Assert equality between that computed operation set and the capability operation set minted at launch. This detects related-work operations such as task creation or linking that are genuinely worker-visible, while excluding list/unblock operations behind an orchestrator-only gate. Exercise both task-scoped lifecycle operations and policy-constrained related-work operations through a real PID-bound capability.

## Start acknowledgement

Before `_set_worker_pid`, verify the exact active scope in the same adapter callback:

- task exists and is `running`;
- task ID, assignee/profile, current run ID, claim lock, and claim expiry equal the launch lease;
- the expected run exists, belongs to the task, is open/running, and has the same lock/expiry;
- task and run PIDs are both null;
- no spawned event exists for that run.

Recognize replay without invoking the helper only when task and run both carry the requested PID and exactly one run-scoped `spawned` event has payload `{"pid": pid}`. Partial PID state, a different PID, or ambiguous event history requires recovery/conflict handling. After first invocation, verify this same post-state.

Order cross-store acceptance as: reserve journal intent → validate process and native scope → apply/reconcile native PID state → atomically activate sidecar capability/lease → complete journal. Never expose a worker capability before native PID/event acceptance.

If generic request fingerprints intentionally omit secrets, bind a keyed digest of the bootstrap token into the journal intent. Never persist the raw token. Return a completed replay before requiring the child process to still be alive, provided launcher authentication and exact journal intent still match.

## Kernel process binding

Do not accept process start time from the launcher. Reserve an intent containing only the lease ID, claimed PID, and bootstrap-token digest; on a non-completed request derive process identity server-side. Open a Linux pidfd before reading `/proc/<pid>`, then verify UID, direct parent PID, and derived start time while holding the pidfd through native acceptance and sidecar finalization. Reject a readable pidfd before acceptance because the process has already exited.

Some Python builds run on pidfd-capable kernels but omit `os.pidfd_open`. A fail-closed positive fallback is libc's exported `pidfd_open(pid, 0)` via `ctypes.CDLL(None, use_errno=True)`. Configure argument/result types, translate a negative descriptor through `ctypes.get_errno()`, and never hard-code an architecture-specific syscall number. If neither binding is available, deny the launch rather than reverting to an unpinned `/proc` check.

Completed journal replay is deliberately process-independent: authenticate the launcher, reconstruct the exact secret-bound intent, return the completed result, and do not require the former child PID to remain present.

## Failure acknowledgement

Do not substitute operator reclaim for spawn failure. Reclaim commonly emits `reclaimed`, closes the run with the wrong outcome, and may clear failure counters. Use the native spawn-failure helper so retry counters, circuit breaker, run outcome, and events remain native.

Before `_record_spawn_failure`, verify the same exact active lease/run scope, null task/run PID, an open running run, and no terminal spawn-failure event. Capture the pre-failure counter. Pass only validated broker configuration as `failure_limit`; never accept it from the launcher request. Passing `None` preserves the pinned native default and per-task override precedence.

Verify one of two exact post-states:

1. Retry: task `ready`; claim/PID/current-run fields cleared; counter incremented once; truncated last error; expected run closed as `spawn_failed`; exactly one matching run-scoped event.
2. Breaker: task `blocked`; fields cleared; counter incremented once; expected run closed as `gave_up`; metadata/event identify `spawn_failed` as the trigger and carry the effective limit/source.

For crash replay, infer success only from the expected closed run, task counters/error, and exact terminal event—not merely from `status == ready`. This also handles first-failure blocking from a per-task retry limit.

Order acceptance as: reserve exact intent → apply/reconcile native failure → transition sidecar lease to failed → complete journal. A new request ID must not claim recovery of an already-failed lease; only the matching reserved request may finish recovery.

## Expiry and post-start reconciliation

An open sidecar lease must never block dispatch solely because its deadline passed. Before selecting an active lease, reconcile expired `pending` or `launching` leases through the same exact native spawn-failure wrapper, then atomically mark the sidecar lease failed. Order this native-first and make it replay-safe: a crash after native failure but before the sidecar transition must be recovered from the exact run/event/counter post-state. If authoritative reconciliation is ambiguous, fail closed and keep dispatch blocked rather than issuing a second claim.

Launch acceptance is not the end of lifecycle synchronization:

- After a successful worker heartbeat, read the authoritative task and atomically copy its exact `claim_expires` to both the launch-bound capability and running launch lease while completing the operation journal.
- After worker complete or block, require the exact native terminal shape, atomically mark the launch lease completed, clear its PID, preserve terminal capability state, and complete the journal.
- Native block semantics may use a non-running task status plus an exact `block_kind`; do not assume the native status literal equals the policy-layer word `Blocked`.
- Derive the launch lease deterministically from the capability ID and validate principal, profile, board, task, run, claim lock, PID, native assignee, and journal fingerprint/intent in one sidecar transaction.
- For non-launch capability IDs, fall through to the established generic mutation-completion path rather than imposing launch-only invariants.

Terminal capability reservation happens before native mutation. Exact same-request recovery must therefore authorize both `reserved` and `completed` terminal journal states, then inspect authoritative native post-state before finalizing. For complete, require a closed run and native `done`; for block, require a closed run and the request's exact block kind. This prevents a crash after native commit from stranding a terminal capability and a permanently running launch lease.

Test all of these with real temporary databases: heartbeat deadline equality, complete and block terminalization, next-dispatch freedom, reserved-terminal crash recovery, expired pre-start reconciliation, first failure retry, and circuit-breaker `gave_up` with exactly one event.

## Exclusive-writer assumption

Pre-check/helper/post-check is race-safe only when the broker is the sole authoritative native writer. An in-process lock does not exclude gateways, CLIs, dashboards, plugins, or another service process. Audit the deployment/cutover controls that disable or deny every non-broker mutation path. State this assumption explicitly in the verdict.

## Read-only exact-commit audits

Freeze commit objects and pinned dependency revisions before inspection. If the worktree changes during the audit, re-check status, cite committed-object lines, exclude concurrent drift from findings, and report the drift. Do not run tests when the requested boundary forbids them.
