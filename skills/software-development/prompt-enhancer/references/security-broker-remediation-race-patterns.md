# Security Broker Remediation: Deterministic Race and Publication Patterns

Use these patterns when executing a long RED→GREEN remediation plan for a local authority broker, launcher, or inert installer. They complement `security-sensitive-candidate-sealing.md` and `kernel-bound-operator-cli.md`.

## Coherent kernel identity

- Read `SO_PEERCRED`, acquire a pidfd immediately, then read process identity while that pidfd remains open.
- Re-read identity and poll the pidfd before accepting it. Fail closed if pidfd support/acquisition is unavailable; never fall back to unpinned split `/proc/<pid>/stat` and `status` reads.
- A pre-transaction liveness check is insufficient. Poll the same pidfd after the authoritative registration transaction commits and before returning success. If the process died, run an idempotent compensating terminalization and return a denial.

## Deterministic real-process race tests

Prefer real processes and real database transactions. Use a narrow seam only to position the race:

1. Perform the real persistence method.
2. Kill and reap the real child immediately after the method commits but before its caller exits the held-pidfd scope.
3. Require a broker denial plus terminal sidecar/native state.

For transaction races, a genuine SQLite `BEGIN IMMEDIATE` lock can hold a write after socket admission. Synchronize on an externally visible milestone (for example native status becoming `running`) before killing the process; a fixed sleep can accidentally test an earlier already-safe branch.

## Leaderless process groups

- `PR_SET_PDEATHSIG` protects only the direct child. Descendants can survive in the worker's process group.
- Reconciliation must signal the stored PGID even when the leader is gone.
- On Linux, `pidfd_open(leader_pid)` can return `EINVAL`, not only `ESRCH`, when the task is gone but its leaderless process group still exists. Treat `EINVAL` as leader loss only when `/proc/<pid>` is absent, then issue `killpg(PGID, SIGKILL)`.
- A PGID remains reserved while group members survive, preventing that numeric ID from being reused as a process PID during this cleanup condition.

## Bounded quiescence

- Listener disappearance is not clean shutdown. Close admitted sockets, wait against a finite deadline, remove the namespace safely, and raise an explicit drain failure if handlers remain.
- Avoid `ThreadPoolExecutor.shutdown(wait=True)` after a deadline; cancel pending futures and surface active-worker failure.
- Test both directions: a handler that ignores socket close must cause bounded explicit failure, while listener startup exceptions must reach the foreground immediately rather than becoming a generic readiness timeout.

## Authenticated readiness

Do not announce launcher readiness after local parsing alone. Add a non-mutating launcher-only broker probe that authenticates the enrolled PID/start identity. Execute it before writing the readiness byte. Never discard a mutating checkout as a readiness probe.

## Crash-atomic inert bundle publication

1. Create a randomized mode-0700 staging directory under a trusted descriptor-opened parent.
2. Write and `fsync` every file; `fsync` the staging directory.
3. Verify exact file set, modes, digests, manifest authentication, and staging namespace identity.
4. Publish with Linux `renameat2(..., RENAME_NOREPLACE)`; do not emulate no-replace with check-then-rename.
5. `fsync` the parent after rename and verify the final namespace identity.
6. Before publication, cleanup must guarantee staging absence or raise; after publication, never delete a pathname whose identity is no longer proven.

Prove abrupt-death behavior with a fork that exits after the first real file write: the final name must remain absent and an immediate retry must succeed. Separately race a rival final directory at publication and prove it is preserved.

## Validation and evidence discipline

- Run changed-slice lint/type checks using the project's active baseline. A broad default-linter invocation can surface unrelated legacy violations and is not evidence that the current slice regressed.
- Still run parser-based file/construct/nesting gates over the complete tree after every new test; late test files often cross hard physical limits.
- Test expectations for migration/config versions must use independent literal contract values. Do not derive an oracle from the production migration collection being tested.
- If a watched external checkout drifts without an authorized write, inspect and preserve it, label it external/unattributed, and do not claim global “no drift.”
