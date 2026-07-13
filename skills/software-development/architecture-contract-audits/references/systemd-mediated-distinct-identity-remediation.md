# Systemd-mediated distinct-identity remediation

Use this reference when a rejected local broker/launcher/worker candidate must move from same-UID direct spawning to distinct broker, launcher, and worker OS identities while preserving lease, capability, replay, and recovery semantics.

## Evidence discipline during an active parent repair

Freeze the staged candidate separately from later unstaged repairs. Recheck both digests at the end. If a parent adds an unstaged RED/GREEN for one blocker, classify it as concurrent partial remediation rather than attributing it to the staged generation. Recompute structural limits on the live repair: a one-line guard added to a file already at 200 lines creates a new blocker even when behavior improves.

## Smallest coherent identity architecture

Use three static service identities:

1. **Broker** owns policy/native authority, databases, keys, public/control sockets, dispatch, and reconciliation. It never spawns launcher or worker processes directly.
2. **Launcher** has public-socket access but no authority-path access. It enrolls from kernel-derived peer credentials, checks out leases, and asks systemd to manage only one sealed worker template.
3. **Worker** runs under a third UID/GID. It receives one launch credential through systemd credentials, becomes PID/start-time/unit bound, then execs the exact worker command while preserving its PID.

Systemd is the cross-identity process mediator. Any polkit allowance must authorize only fixed start/stop/query actions for an exact template whose instance is derived from a strictly validated lease ID. Do not grant generic transient-unit or arbitrary-unit control.

## Enrollment without same-parent assumptions

A separately managed launcher cannot satisfy a broker-child check. Replace direct-child enrollment with a closed `launch.enroll` route that:

- accepts no caller-controlled PID, start time, UID, GID, groups, unit, or database path;
- derives PID/UID/GID/groups from `SO_PEERCRED` plus a held pidfd and coherent process reads;
- verifies the configured launcher service unit/cgroup;
- atomically inserts or stale-rebinds the stable launcher principal;
- rejects replacement while the prior exact binding is live or process state is ambiguous.

A distinct launcher UID makes this route narrower than same-UID bearer enrollment, but UID alone is insufficient: retain PID/start time, primary GID, supplementary groups, unit identity, and liveness.

## Systemd worker activation and capability handoff

Do not pass capability material in argv. A robust sequence is:

1. launcher checks out one lease;
2. launcher generates request ID and token, then durably writes one bounded activation intent before starting a unit;
3. launcher atomically publishes a `0600` credential file under its private runtime root;
4. systemd starts `worker@<validated-lease>.service` under the worker identity with `LoadCredential=`;
5. launcher observes the unit's MainPID and sends replayable `launch.started` with the token;
6. broker holds a pidfd, verifies exact worker UID/GID/groups/unit, performs native start acceptance, then atomically stores worker principal, capability, lease transition, and journal result;
7. worker waits on a capability-authenticated readiness route, not a sleep, then notifies systemd and execs the fixed Hermes command in the same PID;
8. launcher removes the credential/intent only after exact terminal acknowledgement.

Persist the activation request ID/token/unit/PID so launcher restart or response loss reaches the existing journal instead of creating a second authority mutation.

## Recovery and readiness

- Replace process-group ownership assumptions with exact systemd-unit stop/query plus pidfd verification.
- Preserve native-first, sidecar-finalized `launch.started` and `launch.exited` recovery semantics.
- Reconcile every `launching`, `running`, and `terminating` lease before broker readiness.
- Bind worker units to broker/launcher service lifetime or otherwise prove no capability-bearing cgroup survives either service unexpectedly.
- Use `Type=notify` for broker and launcher. Broker readiness means migrations are current, recovery completed, and listeners are authenticated/reachable. Launcher readiness means enrollment plus an authenticated broker probe succeeded.
- Use an aggregate target requiring both notify services when deployment readiness means the complete broker+launcher plane, avoiding a dependency cycle where broker waits for a launcher that is ordered after broker readiness.

## Closed worker grammar

Remove `argparse.REMAINDER` and arbitrary absolute argv tuples. Prefer separate service entrypoints:

- broker: one absolute config path;
- launcher: one absolute launcher-config path;
- worker: one absolute worker-config path plus one strictly shaped lease ID.

Worker config stores one exact Hermes executable; production code appends the canonical profile/hooks/chat/task vector. Reject `/usr/bin/env`, wrappers, interpreter flags, extra suffixes, and caller-selected executables.

## Migration and packaging

A schema migration may add nullable service-unit identity fields, but must not blindly delete open leases or revoke state that still needs native reconciliation. Startup handles legacy open rows fail closed. Bump independently:

- daemon/config schema version;
- authenticated install-bundle manifest version;
- SQLite migration sequence.

An inert bundle normally needs broker, launcher, worker-template, and aggregate-target units plus tmpfiles, sysusers, narrowly scoped polkit, split configs, and bounded logging configuration. Prove account creation and group membership, not only rendered `User=` lines.

## Minimum real RED inventory

- launcher denied before enrollment; wrong UID/GID/groups/unit and live replacement denied;
- worker registration denied for wrong PID/start/UID/GID/groups/unit;
- exact `launch.started` response-loss replay creates one native start and one capability;
- launcher restart resumes the same durable activation intent;
- worker, launcher, and broker death leave no live worker cgroup or unreconciled native claim;
- systemd does not report aggregate readiness before broker recovery and launcher enrollment/probe;
- launcher/worker cannot read broker DB/key and worker cannot read launcher credential storage;
- no production path invokes direct broker→launcher or launcher→worker `Popen`;
- old config and bundle versions fail closed.

Use real service-manager/process/socket behavior in a root-capable isolated job. In ordinary tests, do not replace these acceptance claims with monkeypatched listener, pidfd, process, or publication seams.
