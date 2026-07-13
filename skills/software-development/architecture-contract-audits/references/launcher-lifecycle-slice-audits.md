# Launcher lifecycle slice audits

Use this reference when reviewing a launcher checkout → worker-start acknowledgement → worker-failure acknowledgement slice against an exact committed revision.

## Smallest started request

Prefer the existing launch-operation namespace and avoid inventing another operation when `launch.checkout`, `launch.started`, and `launch.failed` already form a coherent family.

The smallest started request normally contains:

- `lease_id`;
- `worker_pid`;
- the bootstrap secret in the protocol's existing secret-bearing top-level field when one exists.

Do not accept `worker_start_time` from the launcher. Open a pidfd for the submitted PID, derive UID, parent PID, and process start time from the kernel, verify the worker is the launcher's child, and hold the pidfd through new-request validation, native acceptance, and sidecar finalization. Persist PID plus the broker-derived start time. A pidfd is an in-process liveness guard, not durable identity that can be stored in SQLite.

Completed journal replay must occur before requiring the worker to remain alive. A completed request should still replay after the worker exits. Reserved recovery uses the broker-derived start time already stored in the intent and exact native post-state.

## Secret-bound replay

Generic request fingerprints commonly omit protected fields. For a started acknowledgement whose supplied capability material will become a new worker authority, bind the durable intent to a keyed digest. Requirements:

- never store plaintext;
- compare the digest on every replay;
- return `request_conflict` for the same request ID with a different secret;
- test both crash-before-mint and completed-replay cases.

Without the digest, a changed secret can be accepted after a reservation crash or receive a misleading successful replay.

## Native acceptance and sidecar finalization

Native authority and the policy store are separate databases. Use a recoverable acceptance protocol, not a distributed-atomicity claim:

1. reserve a journal intent containing lease ID, worker PID, broker-derived start time, and secret digest;
2. if exact native started post-state is absent, call the pinned native started helper once;
3. verify the authoritative task and current run carry the exact worker PID and the expected started/spawned event;
4. in one policy-store transaction, transition the lease, insert/verify the worker principal, insert/verify the capability, and complete the journal result;
5. return success only after that transaction commits.

Native started helpers may emit events and are often not idempotent. Recovery must observe exact post-state before deciding whether to call them; never blindly repeat one.

For launch failure, use the pinned native spawn-failure semantics rather than generic reclaim semantics. Verify the expected run outcome/event, failure counter, last error, and resulting ready-or-breaker-blocked state before atomically terminalizing the sidecar lease and journal. Pin private native helpers by signature and source digest before relying on them.

## Lease wedges

Audit at least two distinct wedge classes:

### Direct acknowledgement blockers

An expired `launching` lease must not remain the first open lease forever. Failure/recovery may validate the exact run and claim identity even after the launch deadline, perform or recognize native failure finalization, and terminalize the lease deterministically. Started acknowledgement still requires an unexpired lease.

### Following lifecycle slice

A `running` launch lease must eventually close when the authoritative task completes, blocks, is cancelled, loses its claim, or its worker dies. If dispatcher selection simply returns the first nonterminal lease, omission of this reconciliation blocks every later dispatch. This can be a separate bounded slice, but it is a production-rollout gate.

## Capability expiry

A worker capability copied from the initial launch deadline becomes stale when native heartbeat extends the authoritative claim. After a successful heartbeat, renew sidecar capability expiry to the exact verified native `claim_expires`, or provide equivalent reconciliation. Do not grant an arbitrary longer lifetime.

This may be the immediately following bounded slice rather than part of start/failure acknowledgement, but it is also a production-rollout gate.

## Ranking guidance

Block the acknowledgement slice on:

1. caller-supplied start time or missing pidfd liveness protection;
2. missing secret digest in intent;
3. split journal/lease/principal/capability finalization;
4. missing or incorrect native started/spawn-failure semantics;
5. expired launching leases that cannot terminalize.

Allow a separate immediately following slice for running-lease terminal reconciliation and heartbeat-driven capability-expiry renewal only when the checkpoint is not being rolled out or represented as complete end-to-end lifecycle support.

## Focused tests

Use real processes, native temporary databases, and policy-store temporary databases. Cover:

- broker-derived start time and rejection of non-child/dead workers;
- worker exit during handoff leaves no partial accepted state;
- completed replay after worker exit;
- changed bootstrap secret conflicts and plaintext never appears on disk;
- exactly one native started event and exact task/run worker PID;
- injected sidecar-finalization failure followed by observation-based recovery;
- native spawn-failure outcome, event, counter, and breaker semantics;
- failure after launch expiry terminalizes rather than wedging dispatch;
- complete/block/worker-exit reconciliation reopens dispatch;
- heartbeat extends capability expiry only to verified native claim expiry.

For read-only audits, do not run these tests when the user prohibits tests. State that conclusions are source-derived and record concurrent worktree drift separately from exact-commit evidence.
