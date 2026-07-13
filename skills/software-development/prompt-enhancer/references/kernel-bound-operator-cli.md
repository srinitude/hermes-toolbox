# Kernel-Bound Operator Enrollment and Broker-Only CLI

Use this reference when a local policy broker must authorize a human CLI without trusting same-UID callers, caller-supplied actor JSON, inherited ambient credentials, or reusable worker-readable secrets.

## Separate static identity from ephemeral authority

Provision a static operator principal containing only durable policy identity such as principal ID, expected UID, kind, and profile. Daemon startup may validate this static record without requiring a human process to exist.

Grant request authority only through an ephemeral session bound to:

- kernel peer UID;
- exact PID;
- Linux process start time;
- monotonically increasing binding generation;
- absolute expiry.

Include all five values in authenticated context proofs and approval-challenge identity. A challenge, delegated approval, or cached context must fail after expiry, PID reuse, or generation replacement.

## Direct-child gated enrollment

Use a separate private Unix control socket for enrollment. Derive the registrar peer from `SO_PEERCRED`; the request should carry only a child PID, not actor identity, UID, profile, start time, generation, or proof material.

Before binding:

1. Re-read and verify the registrar's kernel UID, PID, and process start time.
2. Open a pidfd for the proposed child before reading mutable `/proc` identity.
3. Require exact direct parentage to the registrar and the configured operator UID.
4. Confirm the pidfd is not signaled.
5. Atomically bind the static principal with PID/start/expiry and increment generation.
6. Recheck the still-open pidfd **after** the atomic bind and before returning enrollment success; a pre-bind check alone can authorize a child that died during storage.
7. Release the child gate only after that post-bind liveness check succeeds.

Prefer `os.pidfd_open` when available. On Linux runtimes lacking that Python wrapper, a narrowly typed glibc `pidfd_open` call with `use_errno=True`, explicit argument/result types, and guaranteed descriptor cleanup preserves the kernel guarantee without falling back to PID-only identity.

A live binding is never replaceable. For early process death before expiry, allow replacement only after proving the exact old PID/start tuple is no longer live, then perform a compare-and-swap over old PID, old start time, and old generation. PID reuse proves the old tuple dead but does not authenticate the reused process.

## Gated shim

The registrar and operator are distinct production OS identities. Treat UID-only separation as incomplete: validate exact registrar UID/GID from `SO_PEERCRED`, and validate the child’s effective UID/GID plus supplementary-group posture from `/proc/<pid>/status`. The private control socket may be group-reachable (`0660`) only inside a broker-owned, setgid registrar transport directory; socket-group reachability is transport permission, never authority.

The registrar launches the operator child behind a pipe gate and enrolls it before execution:

- require an absolute existing executable;
- never invoke a shell;
- pass only the gate descriptor;
- use a minimal allowlisted environment and do not inherit `PYTHONPATH`, loader variables, tokens, or arbitrary profile secrets;
- perform an explicit pre-exec UID and primary-GID drop;
- when crossing identity boundaries, clear supplementary groups before exec and have enrollment verify they are empty;
- set a parent-death signal and verify the same parent immediately before `exec`;
- preserve stdin/stdout/stderr and a genuine controlling foreground TTY so confirmation can occur in the enrolled process;
- do not detach the enrolled child with `start_new_session=True` unless the registrar also performs a correct `tcsetpgrp` handoff and restoration; `isatty()` alone is insufficient;
- on failed enrollment, kill the exact gated child before it can exec. Use a separate child process group only when foreground-terminal ownership is safely transferred; never kill a shared registrar/shell process group;
- release exactly one byte only after successful binding.

A same-UID unprivileged integration fixture proves protocol mechanics only; it does not prove the production identity transition. Pair it with a spawn-contract test that checks the exact `user`, `group`, and empty `extra_groups` options, strict config tests requiring distinct registrar/operator UID and GID, and a privileged disposable integration test before cutover. If production config requires distinct identities but the shim still spawns with inherited credentials, treat that as a blocking contradiction rather than accepting isolated GREEN tests.

Test that a failed enrollment never executes the command, that spawn failure closes both gate descriptors, and that the same enrolled PID reaches the public broker after release.

## Private and public socket hardening

A per-connection timeout alone bounds a partial-frame client but still creates serial head-of-line blocking. Use a small bounded worker pool plus nonblocking admission on both public and private sockets:

- fixed maximum concurrent connections;
- bounded newline-delimited frame size;
- one monotonic **whole-frame** read deadline, recomputing the remaining timeout before every `recv`; a per-`recv` timeout can be extended forever by slow trickle input;
- one request per connection;
- worker-owned close and semaphore release in `finally`;
- immediate close when saturated;
- bounded executor shutdown;
- safe socket-parent directory, ownership, type, symlink, and collision checks;
- fixed denial envelope on the private socket.

Prove with real sockets that continuous trickle input still expires at the absolute deadline, that saturating every worker cannot indefinitely exclude a valid request, and that partial clients cannot prevent bounded shutdown.

## Broker-only operator CLI

Build the CLI from an immutable operation ledger. Do not import or call the native adapter as a fallback.

For reads, validate human eligibility and bounded arguments, then make exactly one broker call.

For mutations:

1. Construct the proposed request with explicit principal, profile, board, project, operation, and arguments.
2. Call the broker's approval-preview operation.
3. Validate the returned protocol version, request ID, operation, profile, actor, board, project, arguments, approval token presence, expiry type, and fingerprint.
4. Remove approval and capability tokens before displaying the preview.
5. Require a genuine controlling foreground TTY (`isatty()` plus terminal foreground process-group equality) and an exact confirmation phrase such as `EXECUTE`; a programmatically attached slave PTY alone is not human confirmation.
6. Execute the exact returned request in the same enrolled child process.
7. On cancellation, send no mutation request.

Use a real-process integration test spanning shim → private control socket → exact session binding → public broker → read operation. Add a real TTY mutation test before declaring the CLI complete.

## Dashboard posture

When dashboard mutation integration is not yet approved, ship an inert validated posture artifact rather than a partially enabled UI:

- read transport is broker-only;
- mutation transport is disabled;
- native fallback is false;
- install state is inert;
- allowed reads and blocked mutations exactly match the immutable operation ledger.

Package the artifact in the wheel and validate it from an installed wheel, not only from a source checkout.

## Required adversarial tests

- registrar cannot enroll itself as its child;
- wrong registrar UID or GID is denied with no binding;
- wrong child effective UID/GID or retained supplementary registrar groups are denied;
- production registrar/operator UID and GID values must be distinct;
- same-UID sibling cannot replace a live binding;
- concurrent siblings produce exactly one atomic winner;
- stale generation, expiry boundary, PID mismatch, and start-time mismatch fail closed;
- verified-dead exact binding can be replaced, but a live exact binding cannot;
- actor JSON never grants authority;
- partial frames do not block independent public or private requests;
- child death during the atomic bind is detected by a post-bind pidfd check and never returns enrollment success;
- continuous slow-trickle frames cannot extend public or private read occupancy beyond the absolute deadline;
- failed enrollment executes no command;
- non-TTY, non-controlling PTY, and non-foreground process-group mutation attempts execute nothing;
- preview tokens never appear in displayed or logged output;
- broker unavailability never invokes native fallback.

## Checkpoint discipline

After each vertical slice, run focused behavior tests and the parser-based structure gate. Before commit, run compilation, diff checks, the relevant broad suite, source/staged secret and unsafe-pattern scans, installed-wheel checks when package data changed, and protected-boundary drift capture. Commit only a clean GREEN slice, then run a small foreground post-commit packet before starting the next RED.
