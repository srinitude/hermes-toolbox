# Adversarial concurrency, liveness, and bounded-resource audits

Use this reference for exact-tree daemon/broker candidates where correctness depends on retries, approvals, process identity, connection draining, and worker supervision.

## Volatile dedup versus durable recovery

Trace duplicate handling before the durable journal. A bounded process-local request-ID registry is still incorrect if it rejects an identical retry before journal replay or reservation recovery. Test response loss after authority mutation or journal completion, then resend the identical frame through the real public socket. The retry must return/recover the original result without reapplying authority.

Safe patterns:

- use volatile state only for bounded in-flight coordination;
- never evict an active request: reject admission at a fixed in-flight cap;
- retain a separately bounded completed-fingerprint cache so an identical completed frame may pass through while changed content under the same recent ID is rejected;
- release in-flight state in `finally`, including handler errors and client disconnects;
- route completed mutations through durable replay and allow safely retryable reads to re-execute;
- never require unrelated traffic, eviction, or daemon restart to make recovery reachable.

A useful public RED sends one frame through the real socket, discards or ignores the first response, then resends the byte-identical frame. Require the original durable result without a second authority mutation. Send a changed frame with the same ID separately and require conflict. Also fill the in-flight set to its exact cap and prove the next distinct request is rejected without evicting any active entry.

For interactive operator CLIs, server-side replay is not operable unless the client preserves and retries the exact approved request after an ambiguous disconnect. A fresh invocation that generates a new request ID/challenge cannot reach the old journal and can duplicate idempotency-keyed creation. Keep the approved request and token in the same process, classify ambiguity from the immutable retry contract, and exercise response loss after commit through the real CLI. Audit generic client retry classification plus the operator wrapper: a client that retries reads only, paired with a one-shot mutation call, makes the durable journal unreachable precisely after ambiguous mutation response loss. A test named as transport safety that asserts “mutations are never retried” is a contract regression when exact-once public recovery is required.

## Approval liveness at the commit boundary

A PID/start-time check before a database transaction has a death race. For direct and delegated approvals, inspect the interval between process validation and the approval+journal CAS. A deterministic RED can pause the real function at that boundary with a trace/barrier, kill and reap the real operator process, then resume.

Prefer a held pidfd, exact identity validation, and a final pidfd poll immediately before committing the same transaction. Dead or ambiguous state must roll back both challenge reservation and journal insertion. Keep PID/start-time/UID/primary-GID/supplementary-group validation as a separate identity invariant; a pidfd pins lifetime and PID reuse, not authorization attributes.

If the configured Python lacks `os.pidfd_open` on a Linux kernel that supports pidfds, a small audited `ctypes` wrapper around `pidfd_open(2)` is an acceptable portability path; do not silently fall back to a second `/proc` check. Fail closed on `ENOSYS`, `EPERM`, or ambiguous polling state.

A deterministic test need not add a production pause hook. Open a pidfd while a real enrolled subprocess is alive, kill and reap it, then invoke the actual transactional reservation CAS with that held descriptor. Require a false/denied result, unchanged pending challenge, and zero journal rows. Pair this transaction-boundary proof with top-level direct and delegated denial tests.

## Pre-authority reservation rollback

Differentiate failures before authority dispatch from ambiguous failures after authority may have committed. If audit emission, request preparation, or another definitive pre-native step fails after reservation, atomically restore every reserved resource:

- human/delegated challenge returns from `reserved` to `pending` and clears its request binding;
- terminal capability returns to non-terminal when no native call began;
- plain operation-journal reservation is deleted;
- every transition is request-ID and fingerprint bound.

If rollback itself conflicts, fail closed as recovery-required rather than hiding it behind the original availability error. Never release a reservation after entering an authority call whose commit status is uncertain; preserve it for reconciliation. A real RED should fail the audit sink on the reserved event, prove zero native mutations and retryable state, then retry through the healthy runtime and observe exactly one mutation.

## Durable state growth

Validate migration history before applying any statement: the persisted version rows must equal an exact contiguous prefix of the compiled migration plan. `MAX(version)` is insufficient—a ledger such as `(1, 3)` can skip migration 2, apply later migrations, and commit an irreparable hole. Preserve helper APIs that accept an appended migration delta by validating against `compiled-prefix-before-first-supplied-version + supplied-delta`, not by treating the delta as the whole history. Keep migration an explicit administrative action; putting `migrate` in a service unit's `ExecStartPre` silently turns every ordinary restart into a state mutation and defeats fail-closed stale-schema startup. Tests should use independent literal version expectations, including previous and unknown-future versions, rather than deriving expected values from the production migration tuple.

Inventory every row created by polling and retry paths. An in-memory LRU does not bound a durable journal. In particular, an infinite launcher loop with fresh request IDs can persist one completed row per idle checkout. Compute and report the normal-operation time to outage (`remaining row capacity × idle interval`), including pre-existing rows; a 4,096-row cap with one-second idle polling is a permanent restart-surviving outage after roughly 68 minutes. Require an explicit retention equation and tests that run beyond the real cap under no-work conditions, then introduce work and prove discovery still functions.

A fixed row cap without a retention, archival, acknowledgement, or bounded replay-horizon contract is not a durable bound: it is a delayed permanent outage. Trace every delete site. A test that fills the journal and merely asserts fail-closed denial proves integrity preservation but also confirms the availability blocker; it is not an exhaustion acceptance test. If deletes exist only for aborting pre-authority reservations, prove that reaching the cap does not reject every future unique mutation forever. If admission deletes completed rows, treat loss of request-ID conflict/replay evidence as an exactly-once defect unless an independently specified replay horizon has expired. Reject tests that celebrate eviction merely because row count stays flat; the oracle must resend an evicted mutation ID and prove it cannot reapply authority. Test cap-minus-one, exact cap, existing replay at cap, changed-content conflict at cap, and a public recovery action that restores admission without weakening request-ID conflict detection.

For compacted authenticated audit chains, distinguish a signed prefix anchor from an authenticated current tip. A validator that accepts `rows=[]` after a valid compact anchor launders deletion of the entire retained suffix. Require authenticated state to bind the expected tip/sequence (or an equivalent external seal), reject every deleted suffix including the empty tail, and prove the next append cannot silently poison an AUTOINCREMENT sequence after truncation.

Do not journal no-op polling results unless replay semantics truly require it. Terminal records need a safe bounded retention/acknowledgement design.

## Connection drain

Closing active sockets interrupts framing and response I/O, but not arbitrary handler code already inside a database, filesystem, native adapter, lock, or subprocess. `ThreadPoolExecutor.shutdown(wait=True)` is unbounded, and its non-daemon workers can prevent interpreter exit.

Require one absolute drain deadline and make timeout observable: remove the socket namespace and other owned resources, then surface an explicit shutdown failure if active handlers remain. Do not report clean shutdown merely because the listener thread returned. Conversely, `shutdown(wait=False, cancel_futures=True)` only cancels queued work; it does not stop running non-daemon workers and therefore is not by itself proof of bounded process exit. If handlers cannot cooperatively honor the deadline, isolate them behind a killable process boundary or ensure the service manager's cgroup/timeout escalation is part of the tested acceptance contract.

Use real blocking seams rather than sleeps alone: hold a genuine SQLite `BEGIN IMMEDIATE` transaction, admit a valid request, request shutdown, and capture the server thread's error. Require bounded namespace cleanup plus one explicit undrained error; release the lock afterward so the test process itself cannot hang. For readiness, race the ready event against a captured thread-completion/error event—otherwise listener setup failures become generic ten-second timeouts and unhandled-thread warnings.

## Launcher and worker supervision

Audit process groups, sessions, parent-death signals, signal handlers, pidfds, and authoritative lease reconciliation together.

A common orphan trace is:

1. worker starts a new session/process group;
2. launcher SIGTERM handler only sets a stop event;
3. launcher is blocked waiting for the worker;
4. daemon escalates against the launcher's process group;
5. worker survives in its separate group with a valid capability.

Require immediate signal forwarding, bounded TERM-to-KILL escalation, parent-death behavior for the worker and descendants, wait/reap, and lease reconciliation before launcher shutdown returns.

For a broker-accepted worker start, holding a pidfd is not enough: poll before native acceptance and again immediately before the sidecar lease/capability commit. A worker that exits between the initial poll and registration must not be recorded as running. Pair the transactional test with the real launcher gate so a dead child cannot produce a successful start acknowledgement.

## Restart reconciliation

Expiry-only reconciliation is insufficient. After cgroup cleanup or a crash, an unexpired `running` lease may point to a dead worker. If startup treats it as active and checkout selects only `pending` leases, dispatch wedges until TTL expiry.

Audit `launching` leases separately. A daemon crash after checkout can leave an unexpired lease bound to the old launcher PID; a replacement launcher cannot reclaim it when candidate selection accepts only `pending`, while the dispatcher may suppress work merely because any open lease exists. Startup must either prove and adopt the exact live launcher/child or atomically reconcile the old launch attempt before publishing readiness.

On startup and during supervision, inspect exact PID/start-time liveness for every running lease. Atomically claim dead or ambiguous workers, reconcile authoritative native state, terminalize the lease, and prove the next dispatch succeeds. If a worker remains alive after launcher loss, either safely adopt it under explicit supervision or terminate and reconcile it; never leave it orphaned.

## Readiness

Separate these readiness points:

1. socket bound;
2. sandbox installed;
3. principal enrolled;
4. post-exec launcher runtime initialized;
5. authenticated checkout/health path working.

Do not publish daemon readiness after only pre-exec sandbox acknowledgement. Preserve a post-exec readiness descriptor and require the production launcher CLI to signal after configuration and a real broker probe.

## Output and log bounds

Directing worker stdout/stderr to an append-only file is not a bound. Require a byte quota, rotation, or OS-level file-size limit, and reconcile limit exhaustion as a worker failure. Test with a real worker that emits beyond the configured maximum.

For broker-call deadlines, distinguish a per-attempt timeout from one public absolute deadline. A retry helper that invokes a 15-second client twice permits two independent deadline windows; a separate lifecycle acknowledgement configured for 30 seconds also violates a claimed 15-second worker-broker bound even if checkout uses 15. Carry one monotonic deadline through connect/send/read and all permitted retries, and test delayed first-attempt response loss plus a second attempt against the total bound.

## Focused RED inventory

- identical public-socket retry after response loss reaches durable replay;
- operator death between liveness check and approval CAS leaves zero state change;
- repeated idle checkout keeps durable rows under a fixed cap and later discovers work;
- stop during a blocked handler exits within one absolute drain bound;
- daemon/launcher stop leaves no worker process or authority orphan;
- restart before lease expiry reconciles a dead running worker and permits next dispatch;
- post-gate launcher failure never publishes readiness;
- oversized worker output remains within a configured storage bound.
