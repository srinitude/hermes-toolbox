# Fixed Systemd Worker Activation for Security Brokers

Use this reference when a security-sensitive local broker must delegate work to a separately identified, fixed systemd worker slot without giving the scheduler launcher process-control authority or capability secrets.

## Trust boundary

Use pairwise-distinct non-root identities for:

- broker;
- scheduling launcher;
- each fixed worker slot.

A shared UID preserves integrity risks and same-UID signaling/resource interference. Treat authority integrity and availability isolation as separate acceptance rows.

The launcher may enroll and submit an empty scheduling tick. It must not receive:

- worker capability tokens;
- credential paths;
- lease workspaces or worker argv;
- `CAP_SETUID`/`CAP_SETGID`;
- polkit authority to start or stop units;
- broker database access.

The broker alone controls a literal non-template worker unit. Never accept a caller-selected unit, instance, alias, or verb.

## Closed activation sequence

1. Require the fixed slot to be inactive and cgroup-empty before reservation.
2. Durably reserve the lease and slot before any external start.
3. Generate an activation ID and capability token; persist only the digest.
4. Publish a bounded credential source atomically with `O_EXCL|O_NOFOLLOW`, mode `0600`, file and parent fsync, and recorded device/inode.
5. Subscribe to systemd job signals before calling `StartUnit(unit, "fail")`.
6. Correlate the exact returned job object and accept only `JobRemoved(unit=literal, result="done")`.
7. Worker reads a closed-schema credential from `CREDENTIALS_DIRECTORY`; token never enters argv, launcher responses, logs, or general launcher state.
8. Worker self-binds through a broker-observed pidfd and `GetUnitByPIDFD`, then same-PID `execve`s the fixed executable and fixed argv.
9. Post-exec plugin initialization performs the final broker registration/readiness transition.
10. Only after durable lease/capability binding succeeds does the main process emit `READY=1`; use `Type=notify` and `NotifyAccess=main`.
11. Remove only the recorded credential inode after systemd has consumed it; fsync the parent. Credential cleanup is not capability revocation.

`StartUnit` completion is protocol readiness only when the unit is `Type=notify` and the `READY=1` sender is the exact main process after authenticated post-exec registration.

## Identity checks

For enrollment and every capability-bearing request, hold a pidfd across observation and the committing transaction. Re-observe immediately before commit and require:

- kernel peer PID, UID, effective GID, supplementary groups, and process start time;
- pidfd liveness;
- exact fixed unit returned by `GetUnitByPIDFD`;
- canonical unit object path;
- 16-byte nonzero `InvocationID`;
- `MainPID == peer PID`;
- `ActiveState` appropriate for the transition;
- unified `/proc/<pid>/cgroup` equals `Unit.ControlGroup`;
- persisted slot, activation, lease, task, run, claim, expiry, and capability digest.

Enrollment-only validation is insufficient. Re-resolve the unit, invocation, cgroup, and process identity on every capability mutation and replay path.

## Stop and recovery

`StopUnit` has no compare-and-stop invocation argument. Before stopping:

1. serialize the slot under broker ownership;
2. inspect the current fixed unit;
3. compare its invocation and cgroup with durable state;
4. quarantine on mismatch rather than stopping a replacement;
5. revoke capability before stop;
6. call `StopUnit(unit, "fail")` and correlate exact `JobRemoved`;
7. require inactive state, `MainPID=0`, and cgroup absent or `populated 0`;
8. remove the exact credential inode and scrub worker-writable runtime state;
9. only then mark the slot reusable.

Before broker readiness, reconcile every nonterminal activation state. Cover crashes after reservation, credential publication, start queueing, invocation bind, capability registration, readiness, and stop queueing. Response loss must be replay-safe and must not create a second invocation.

If activation failed after `StartUnit` may have created a generation, compensation must inspect and stop the attributable exact generation before credential cleanup and durable terminalization. Prove the slot was inactive immediately before the broker-owned start; otherwise an unbound observed generation is ambiguous and must be quarantined.

## Inert installer contract

Render, authenticate, and verify artifacts without installing or activating them:

- broker, launcher, and worker0 units;
- aggregate target;
- sysusers and tmpfiles declarations;
- broker-only exact-unit start/stop polkit rule;
- closed broker/launcher/worker configuration;
- manifest with exact names, modes, sizes, hashes, and authenticated canonical payload.

The worker unit should be fixed, non-template, `Restart=no`, `KillMode=control-group`, `Type=notify`, and have no `[Install]` section. Keep local rendering, privileged installation, activation, and production cutover as separate approvals.

## Verification gates

Unprivileged tests may prove real Unix sockets, pidfds, same-PID exec, closed config loading, notification datagrams, authenticated bundle publication, and read-only systemd calls. They do not prove distinct-UID DAC, polkit, `LoadCredential`, service-manager readiness, or cgroup cleanup.

Require a root-capable disposable systemd environment for:

- real users/groups and DAC denial matrix;
- broker-only polkit start/stop and negative verbs/units;
- launcher and worker inability to read broker authority state;
- credential absence from argv, environ, logs, and journal;
- failed-exec/no-ready cases;
- descendant survival and cgroup-empty stop;
- broker restart and invocation-replacement quarantine.

Do not seal a candidate while per-request generation revalidation, complete recovery-state tests, real installed-wheel proof, or privileged acceptance remains unresolved.
