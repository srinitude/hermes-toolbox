# Sealing Security-Sensitive Long-Running Candidates

Use this pattern for a large security-sensitive code candidate whose full suite is expensive and whose final audit can invalidate otherwise-green work.

## Candidate generations

1. Treat the staged binary diff digest—not only `HEAD`—as the candidate identity.
2. Tie wheel/install evidence, durable suite logs, exit artifacts, and delegated audit briefs to that exact digest.
3. If self-review, a test-oracle correction, or an audit finding changes any tracked file, immediately invalidate the running suite and all digest-pinned audits. Stop the old process, restage, compute a new digest, and regenerate evidence. Never “carry forward” a full-suite pass from a prior generation.
4. Delayed completion notices from stopped/SIGTERM processes are stale. Exit `130`, `143`, signals, missing exit artifacts, or partial dots are failures, not evidence.

## Long-suite execution

- Use `python -m pytest`, not a potentially stale console-script shebang.
- Write `/tmp/hermes-verify-<gate>-<digest>.log` and a numeric `.exit` file with `pipefail` preserving pytest’s status.
- Set the background-process timeout above the worst observed duration plus explicit margin. Do not choose a generic 600-second timeout for a suite previously observed near or above that duration.
- Run no overlapping pytest against a shared HOME/profile/database/socket/runtime.
- If a bounded watcher expires while the tracked process continues making progress, preserve the run. Do not restart merely because a polling window elapsed.

## Audit ordering

- Run focused RED→GREEN and cheap static gates before staging.
- Apply lint baseline-awareness before issuing a digest: legacy failures may be compared against `HEAD`, but every newly added source or test file must be clean under the active rules. Run added-file and changed-source scans explicitly; a selective latest-slice scan can miss candidate-invalidating findings and waste an expensive full-suite run.
- Run file, construct, and nesting checks after the complete candidate test set exists; a late regression file can cross a hard structural limit even when the prior tree was clean.
- Stage and digest the candidate only after those gates are clean, then build/install/probe from outside the source tree.
- Run the uninterrupted full suite.
- Launch fresh read-only audits pinned to the accepted digest. Require each report to state the digest it independently verified. If an earlier audit batch notices drift, it is stale even when its source findings remain informative.
- A dispatched background audit is not checkpoint evidence. Count it only after its report is delivered, provenance-linked to the requested repository/task/delegation, and reconciled against the still-current digest. Do not end a sealing checkpoint by treating “audit running” as equivalent to review completion.
- For expensive final review, prefer an externally recognizable tracked reviewer process or another delivery path with durable stdout and numeric exit when ordinary background delegation has already failed to return. Preflight one reviewer CLI for binary resolution and authentication before launching a parallel batch; an authentication/setup failure is not a review result and must not be generalized into a durable claim that the tool is unusable.
- If a delayed process notice arrives, classify it by exact session ID, command shape, candidate digest, and durable log/exit artifacts. A generic or superseded pytest process—even if it prints progress—cannot supersede the digest-bound authoritative run.
- Commit only after every material finding is either remediated with public-boundary evidence or explicitly rejected against a stronger active contract.

## Architecture lessons for local brokers

When a service launches less-trusted same-UID descendants, Unix permissions and empty capabilities do not isolate service-owned databases.

- Prefer a kernel-enforced irreversible child domain (for example Landlock) before enrollment/release. Require a readiness acknowledgement before binding the child’s PID/start identity; fail closed on unsupported ABI or setup failure. Landlock grants are additive: a narrow denial cannot override a broad recursive read grant such as `/usr`, an interpreter root, or a command grandparent. Centralize the exact runtime-read-root calculation and reject digest keys, policy databases, service configuration, and other confidential authority beneath every broad readable root in both installer and live-config validation.
- Keep writable worker/profile/workspace roots disjoint from policy databases, digest keys, native authority roots, configuration, and backups. Validate dynamic lease workspaces against an explicit root.
- Do not grant registrar/operator socket groups to a service through supplementary groups when less-trusted descendants inherit that identity. Prefer service-owned setgid socket directories with exact owner/group/mode validation so newly bound sockets inherit the listener-specific group. Verify inherited socket ownership before chmod; do not rely on a child dropping groups it lacks privilege to drop, and do not `chown` a correctly inherited socket as a substitute for topology.
- Persist and revalidate the complete process-bound principal identity: UID, PID, process start time, primary GID, canonical supplementary groups, and scope. Carry immutable kernel identity records through enrollment, checkout, started/exited journaling, and capability authorization instead of repeatedly plumbing partial scalar identities. For a worker child, hold a pidfd while verifying parentage and require its GID/groups to match the launcher’s intentionally non-sensitive service identity.
- Disable dumpability and close all authority descriptors before child exec; a filesystem sandbox alone does not address same-UID process attachment.
- Separate **authority integrity** from **service availability** in the acceptance matrix. Removing registrar/operator supplementary groups, using setgid socket directories, Landlock-confined filesystem access, and complete UID/PID/start/GID/group binding can protect authority bytes while a same-UID worker can still signal or resource-starve the broker. Do not describe the former as full process isolation. A production availability proof requires a genuinely distinct worker service identity or an equivalent privileged/cgroup/seccomp boundary, plus a real process test through that exact launch path; otherwise retain an explicit residual-risk/compatibility hold.
- Do not fake a distinct-primary-GID direct-child proof under an unprivileged runner. Membership in a supplementary group does not let an ordinary child call `setgid()` to promote that group. Helpers such as `sg`/`newgrp` commonly introduce an intermediary process, which breaks exact direct-child PID binding and therefore does not prove the operator/worker process that will call the broker. Use a root/capability-enabled disposable environment, rootless subordinate-ID container when genuinely available, or user-executed privileged systemd setup; if none exists, report the concrete proof blocker instead of weakening parentage checks or marking a skipped test as evidence.
- Hold validated parent directory descriptors for Unix sockets. Bind/connect through `/proc/self/fd/<dirfd>/<name>`, use descriptor-relative metadata and cleanup, reclaim only exact owned stale sockets that refuse connection, and preserve successors.
- Require clients to authenticate an explicit expected server UID with `SO_PEERCRED` before sending bytes. Use one monotonic deadline across connect/auth/send/receive.
- Bound request-ID retention and active connections. On shutdown, close the listener, shutdown tracked client sockets, then drain workers against the daemon-wide deadline. Do not call an executor's unbounded `shutdown(wait=True)` after the deadline; use process-exit-safe daemon handlers or another design whose stragglers cannot keep the service alive.

## Bounded durable state and process output

Choose bounds according to the security contract rather than applying one pruning policy everywhere.

- For an exactly-once operation journal, never evict a completed request merely to admit a new one: once its request ID and fingerprint disappear, the same ID can execute again. Choose one explicit contract: (a) fail-closed capacity backpressure that preserves every replay record, paired with a separately designed administrative recovery path; or (b) an authenticated, operator-acknowledged replay horizon whose public contract explicitly ends exactly-once guarantees before a declared boundary. Horizon advancement must be a distinct authorized operation, not an admission side effect. Preserve every reserved row, make capacity admission transactional before approval/capability/native changes, and prove zero mutation on capacity denial plus replay for every retained ID. Do not call bounded active-table storage “bounded retention” if an unbounded hidden archive carries the same records.
- For a chained audit log, permanent backpressure can disable the whole broker. Compact to a retained suffix only through an authenticated checkpoint containing the pruned boundary sequence and event hash, and separately authenticate the current retained tip so deleting the suffix cannot be accepted. Create the signed genesis tip during one explicit migration/bootstrap ceremony with access to the signing key; normal runtime construction must require and verify it, never recreate a missing tip as though the database were fresh. Before signing a new checkpoint, verify the complete current chain from the prior checkpoint; read checkpoint, tip, and suffix from one database snapshot, reject sequence discontinuity before append, and test deletion of chain, checkpoint, and tip together.
- Bound subprocess logs while the process is running, not only after exit. Pipe stdout/stderr through a bounded drainer, rotate to a finite number of bounded segments, prune stale log files before creating new ones, reject symlinked roots before metadata-changing calls, and join the drainer before reporting authoritative process completion. The drainer must retain and propagate sink exceptions; thread termination alone is not proof of successful EOF or durable output.
- A finite retention rule needs a public behavior test at the actual boundary: new journal admission denied with zero state change, existing replay still accepted, audit suffix verifies after compaction, checkpoint tampering is detected, and noisy real subprocesses stay within byte/file-count caps.

## Process-tree readiness and lifecycle

- Treat sandbox/bootstrap readiness and post-`exec` service readiness as separate gates. Keep a second inherited pipe open across `exec`; acknowledge it only after the final CLI has parsed runtime configuration, installed termination handlers, and completed a non-mutating authenticated broker probe bound to the enrolled launcher identity. Never discard a mutating checkout as a readiness probe.
- For less-trusted worker descendants, bind an expected parent PID before `exec`, install `PR_SET_PDEATHSIG`, then recheck the parent to close the setup race. A graceful normal stop still needs explicit process-group forwarding with bounded TERM→KILL and reap; a parent-death signal is a crash-safety backstop, not the normal shutdown protocol.
- Make worker waits stop-aware. Poll process completion and the launcher stop event against one monotonic deadline; on stop or timeout, terminate the worker process group, escalate after a fixed grace period, drain logs, and only then record the authoritative exit.
- Size client whole-operation deadlines above the server's longest legitimate internal wait plus response overhead. A client deadline equal to a database busy timeout creates a race where accepted requests fail just before the server can respond; retain a finite margin and prove it with a delayed real-server test.
- Derive shutdown test deadlines from the full protocol: TERM grace, possible KILL escalation, reaping, log drain, and authoritative broker reconciliation. To detect missing forwarding without an unjustified tight oracle, set the worker's normal timeout well above the asserted shutdown bound.
- Stress timing-sensitive real-process tests serially several times before the expensive suite. If the suite still exposes a timing failure, classify it as a production deadline defect or an unjustified oracle, preserve a public RED for the corrected contract, and invalidate the candidate after either correction.
- Before runtime construction or reconciliation, acquire a nonblocking lifetime ownership lock under a private descriptor-validated runtime root and hold it for the daemon’s entire life. Socket binding alone is too late: a second invocation can otherwise mutate live leases before discovering the active listener.
- Before opening public sockets or setting daemon readiness, reconcile every persisted `launching`, `running`, or `terminating` lease, including unexpired leases. A crash-interrupted `launching` lease has no registered worker capability: idempotently record native launch failure first, then terminalize the sidecar lease so a crash between steps remains recoverable. For registered workers, use exact PID/start-time/UID/GID/groups identity, a held pidfd, and process-group termination; poll the pidfd again after the registration transaction commits and compensate if the worker died. If any lease cannot be reconciled and terminalized, fail startup closed instead of exposing a mixed old/new process generation.
- Race every listener’s readiness against its thread/process completion and retained exception. Apply this to private control listeners as well as the public listener; a thread that dies before readiness must make startup fail, and a post-readiness listener exception must remain observable through shutdown and process exit.

## Installer evidence

For authenticated inert bundles, pathname-by-pathname verification is not reusable trust evidence.

- Render in memory, write every descriptor completely, `fsync` files/directories, and publish with atomic no-replace semantics.
- Open parents and entries descriptor-relatively with no-follow validation.
- Verify exact bytes from opened descriptors and return immutable verified bytes, not paths described as permanently verified.
- Keep staging/verification distinct from privileged installation or activation approval.
