# Capability-Gated Worker Launches

Use this pattern when a privileged local launcher must start and supervise a narrowly authorized worker through a local broker without allowing the child to act before its kernel identity is registered.

## Safe launch sequence

1. Resolve and persist the authoritative native workspace before issuing the launch lease. Bind the same absolute workspace into checkout; never inherit or guess `cwd`.
2. Validate configuration before checkout: absolute executable, bounded NUL-free argv, real Unix socket rather than a regular file/symlink, private profile home/log/workspace roots, bounded identities, and a bounded protected-authority set. Reject equality or containment in either direction between writable roots and policy databases, digest keys, policy directories, or native authority roots.
3. Build a minimal allowlisted environment. Do not inherit `PATH`, `PYTHONPATH`, loader variables, arbitrary secrets, or launcher-only credentials. Pass only profile home, workspace/task/run/claim identifiers, broker socket, and one scoped capability.
4. Open an anonymous pipe. Spawn a tiny bootstrap as the launcher's direct child with a broker-opened disconnected stdin descriptor, private append-only logs, and the read end inherited. The bootstrap blocks on exactly one byte. After kernel confinement, nested workers should inherit fd 0 instead of reopening `/dev/null`, because a read-only `/dev` Landlock rule correctly denies a new read-write open.
5. Register `launch.started` using the child PID. The broker derives process start time from the kernel, verifies UID/direct parent/PID/start time, and holds a pidfd through native and sidecar registration.
6. Retry only the exact same started request ID/fingerprint after an ambiguous broker-unavailable response. Never mint a second capability or child while acknowledgement is ambiguous.
7. On success, write one release byte. The bootstrap closes the gate and calls `execve`; the PID remains unchanged.
8. On failure, close the gate and terminate/reap the blocked bootstrap. Preserve recovery-required state when native commit may have succeeded.

## Apply kernel confinement before launcher enrollment

When launcher and broker share a UID, metadata alone is not privilege separation. Apply an irreversible kernel sandbox in the same launcher PID **before** binding its PID/start identity:

1. Keep worker workspaces under a dedicated private root that is disjoint from native databases and policy state. Configure that root explicitly in both the native adapter and launcher; never derive it as a child of a broad authority runtime.
2. Serialize the broker-authored read/write policy with an exact bounded schema into a `memfd`, seal it against write/grow/shrink/further-seal changes, and pass only that descriptor to the bootstrap. Environment variables are not an integrity boundary for a compromised launcher.
3. Give the bootstrap a separate readiness pipe. It must parse the sealed policy, apply Landlock or the selected irreversible sandbox, and write exactly one readiness byte. The broker must receive readiness before reading process identity or creating the launcher binding.
4. Fail closed on unsupported sandbox ABI, malformed policy, missing roots, readiness EOF/timeout, parent-PID drift, or child exit. Kill and reap the process group and prove no launcher binding exists.
5. Build read rules from fixed runtime/package data, broker socket parent, executable, and at most the designated script/module entrypoint. **Never allow every absolute argv item**: an attacker-controlled later argument can smuggle a policy database parent into the read allowlist.
6. Authenticate the connected broker with the UID directly returned by `SO_PEERCRED`. Do not call a richer peer-identity routine that opens `/proc/<broker-pid>` when only server UID is needed; the sandbox should keep broker `/proc` state inaccessible.
7. Apply a narrower second sandbox in the worker bootstrap. A child cannot widen its inherited Landlock domain, so every legitimate worker path must already be inside the launcher domain.

Use a real worker probe against the live policy database: opening it must raise permission denial, while the same process must still authenticate the broker, complete the task, and close its lease. This combined denial-plus-success test prevents a sandbox that “passes” only because it blocks all useful work.

## Supervise every process exit

A process return code is observation, not task authority.

- `0` is successful only when the native task is already terminal through an authorized task operation. A clean exit while the task remains running is a protocol violation.
- A nonzero or signal-derived return code must be converted to deterministic bounded text and delegated to a source-pinned native failure helper. Do not reproduce native failure counters, breaker thresholds, run outcomes, or claim clearing with direct SQL.
- Runtime timeout should terminate the worker's private process group, wait a bounded grace interval, escalate to `SIGKILL`, reap the direct child, and then submit the observed return code through the same exit operation.
- Successful task completion followed by process exit needs a journal-only observation branch. Verify native terminal state and exact terminal capability/lease scope, but do not mutate native state twice.
- Keep exit/failure cleanup authorized during dispatch quarantine or shadow/hold mode. Policy may block new checkout/start while still allowing existing authority to be revoked and reconciled.

## Replay and cross-store ordering

Use a deterministic exit request ID derived only from immutable lease ID and registered PID. This lets launcher restart or response ambiguity replay the exact operation; a changed PID or exit code must conflict through the request fingerprint.

Durable launcher operations must bypass any process-local duplicate guard and rely on their durable journal. Test both:

1. same-server exact replay; and
2. exact replay after broker restart.

Native and broker stores do not share a transaction. Order exit processing as:

1. reserve or match the durable sidecar journal;
2. verify exact launcher, lease, task, run, claim, profile, board, PID, and capability scope;
3. apply or deterministically observe native authority;
4. atomically terminalize capability/principal/lease plus journal result in the sidecar.

If native succeeds but sidecar finalization fails, leave a recoverable incomplete journal. Never mark the journal complete first.

## Expired worker and orphan recovery

Do not release an expired running task while the old worker may still execute.

1. In one sidecar transaction, revalidate lease/capability/principal scope and expiry, revoke the capability, and move `running -> terminating` while retaining PID.
2. Only after the claim commits, open a pidfd and compare live UID/PID/kernel start time with the stored worker identity.
3. If PID/start time differs, treat the old worker as gone and never signal the replacement process.
4. If identity matches, kill the worker's private process group and wait for pidfd readiness. Missing pidfd support, permission errors, or ambiguous process state must leave the lease recoverably `terminating`.
5. Apply the pinned native worker-failure operation.
6. Atomically move `terminating -> failed` and clear the lease PID.

The intermediate state is essential: it closes the heartbeat-renewal race before signaling and lets recovery resume after broker failure at any later step. Reconciliation must run even while dispatch policy is held; otherwise quarantine can wedge orphans indefinitely.

## Service-loop posture

A persistent launcher loop should retain one kernel-bound launcher PID across checkout attempts. Use bounded worker timeout, bounded idle delay, an injectable stop event, and aggregate nonsecret counters. An idle checkout is not a failure. Do not expose arbitrary environment injection through the CLI.

Launcher enrollment is a separate privileged concern. Do not weaken PID/start-time authorization merely to make a static service file convenient; enrollment should be broker-managed or use a protected pre-exec gate that binds the actual long-lived launcher PID before checkout.

## Test the real boundary

Use real subprocesses and Unix sockets, not fake process objects. Prove:

- direct-child registration precedes broker access;
- exact argv and disconnected stdin;
- no inherited marker, secret, `PYTHONPATH`, or loader variables;
- authoritative workspace as `cwd`;
- private token-free mode-`0600` logs;
- successful terminal capability/lease closure;
- clean-exit protocol violation;
- nonzero and signal failure;
- timeout TERM→KILL escalation;
- same-server and post-restart exit replay without duplicate native events/counters;
- cleanup under a policy hold;
- first-pass and resumed `terminating` orphan recovery;
- PID-reuse mismatch never signals the replacement process;
- service-loop completion followed by an idle poll.

A dependency-free test worker can send the real newline-delimited JSON frame with `socket` and `json`. Give native operations enough response time: native commit may precede a too-short client's response timeout.

If the pinned native helper cannot reproduce a special provider-specific exit branch without direct SQL, preserve conservative fail-closed behavior or an explicit compatibility hold. Never bypass the native-authority boundary to make the test matrix look complete.
