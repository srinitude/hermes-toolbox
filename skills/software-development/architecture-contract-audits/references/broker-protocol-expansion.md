# Broker protocol expansion audit checklist

Use this when adding a broker-only protocol operation that does not map to a native operation.

## Surfaces to trace

1. Public protocol operation allowlist and wire schema.
2. Exact argument contract, including unknown-field and token rejection.
3. Special-operation registry and handler routing order.
4. Runtime dependency/dataclass construction and production wiring.
5. Kernel/server-derived identity checks and scope binding.
6. Success and denial audit events.
7. Client read/retry classification and real socket round trips.
8. Compatibility equations that compare protocol operations with native-ledger IDs.
9. Checked-in ledgers, snapshots, schemas, and generated exhaustive sets.
10. File, construct, line-length, and control-nesting limits.

## Native-ledger distinction

Do not automatically add a broker-only operation to the native operation ledger. If it has no official native callable, classify it explicitly as non-native in exhaustive coverage tests. Keep the native ledger and its expected-operation snapshot unchanged unless the operation genuinely dispatches a pinned native callable.

A typical failure is:

```text
operation_ids == KNOWN_OPERATIONS - NON_NATIVE_OPERATIONS
Extra items: <new broker-only operation>
```

The correct update is usually the broker-only exclusion set, not a fabricated native-ledger entry.

## Compatibility traps

- A read-only special operation may bypass the generic native read path, so explicitly inspect client retry allowlists and audit-event parity.
- Do not call the clock or perform shared validation for every request merely to support one special route; route-match first to avoid shifting expiry boundaries for unrelated operations.
- If `now` is passed into a polling/read path, verify it is actually used to reject expired records.
- “Read-only” may still append audit records. Tests should separately assert no authority mutation, no journal reservation, stable lease state, and the intended audit write.
- Runtime fields with defaults preserve constructor compatibility but may leave production wiring absent. Identify the real assembler or state clearly that the repository has none.
- Generic operation sets can feed worker-capability validation. Check whether adding a privileged broker operation accidentally broadens another allowlist even if a later gate still denies execution.

## Launch lifecycle acknowledgements and worker bootstrap

Treat start/failure acknowledgements as a lifecycle protocol, not two isolated IDs.

- Keep protocol names in command form when the registry uses commands (`launch.start`, `launch.fail`); reserve past tense (`launch.started`, `launch.failed`) for audit events.
- Update every coupled set: wire registry, exact argument spec, special-handler registry, durable-replay bypass, broker-only compatibility exclusion, and client retry classification. Refactor binary special-handler fallthroughs before adding a third operation.
- Process-local duplicate guards must not intercept retries intended for a durable journal. Retry the identical frame/request ID only after ambiguous transport failure; do not relabel lifecycle mutations as reads.
- If fingerprints omit top-level tokens, replay must independently prove that the presented token hashes to the already-bound capability. Never persist plaintext capability tokens merely to replay a result.
- Do not validate capability operation lists against the generic protocol registry: protocol growth can accidentally make privileged broker operations capability-eligible. Use a fixed worker-operation allowlist and test it against native `worker_eligible` metadata.
- Bind a worker to a process instance, not only a numeric PID: kernel-derived UID/PID plus process start time. Derive board, task, run, claim lock, profile, expiry, and operations server-side.
- Bootstrap principal creation, capability-digest insertion, lease CAS, and journal completion in one broker-store transaction; do not compose independently committing storage calls.
- Trace terminal cleanup in both directions. A failed lease with authority still carrying `claim_lock=launch:<lease>` can break recovery; an open running lease after worker completion can block dispatch forever. Require reclaim/reconciliation and a focused next-dispatch test.
- Existing schema columns may already support bootstrap. Prefer a composite API over an unnecessary migration; when a migration is necessary, update exact schema-version assertions.
- Audit success with non-secret lease/task/run/process/capability IDs. Keep tokens and claim locks out of audit records.
- Verify production reachability: a tested handler is not worker bootstrap if no launcher loop, subprocess contract, runtime assembler, or executable entrypoint exists.

## Focused verification

Run only affected tests, with cache disabled where read-only worktree preservation matters. Include:

- the new real client/server operation tests;
- exhaustive protocol-versus-ledger coverage;
- existing client/server framing tests;
- audit tests;
- the pre-existing special-operation path being refactored;
- a static structural-limit probe.

Report confirmed failures separately from untested likely failures. Re-check `git status` after tests, and note any concurrent worktree drift observed during the audit.
