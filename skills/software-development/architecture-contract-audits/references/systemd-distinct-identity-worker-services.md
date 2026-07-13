# Systemd distinct-identity worker service audits

Use for read-only reviews of architectures where a broker and launcher run as separate service accounts, systemd starts fixed worker units, and lease capabilities are delivered through systemd credentials.

## Outcome rule

Separate broker/launcher/worker UIDs are necessary but not sufficient. Keep these guarantees independent:

1. **Broker integrity:** launcher and workers cannot read/write broker databases, keys, code, sockets, or credential sources.
2. **Cross-task confidentiality:** one worker cannot read another lease's token, profile data, workspace, `/proc` state, or executable inputs.
3. **Capability unforgeability:** a copied token cannot be used from the wrong process, unit, invocation, or lease.
4. **Availability:** a compromised launcher cannot indefinitely race, restart, or occupy worker units.

A design may preserve broker integrity while still failing cross-task confidentiality or availability. State the selected guarantee explicitly.

## Shared worker UID trap

systemd exposes a unit credential in a read-only per-unit directory accessible to the unit UID and root. Distinct credential directories therefore do not, by themselves, hide tokens from another service using the same UID.

Require one of:

- a dedicated UID per bounded worker slot, with at most one active lease per UID;
- `DynamicUser=` or equivalent per-invocation identity plus private state placement; or
- a mandatory mount/LSM boundary proven to deny sibling credential, `/proc`, FD, workspace, profile, and executable-input access.

Before reusing a slot UID, prove the old unit cgroup has `cgroup.events: populated 0`, all descendants are gone, runtime credentials and source material are gone, and no shared writable execution root can persist code into the next task. Binding a stolen token to an exact pidfd/unit invocation may make it unusable but does not satisfy a token-confidentiality claim.

## Kernel-bound request identity

For every worker connection:

1. read `SO_PEERCRED` (credentials fixed at Unix-socket connection time);
2. immediately open a pidfd and fail closed if unavailable;
3. read UID, effective GID, supplementary groups, PID, start time, and parentage coherently;
4. query systemd `GetUnitByPIDFD()` when available to obtain the exact unit and `InvocationID`;
5. verify fixed unit, expected control group, slot, lease, and capability generation;
6. retain and poll the pidfd through authorization and the committing transaction;
7. re-read required process identity immediately before commit.

Do not authorize from caller-supplied identity, `/proc/<pid>/cgroup` text alone, `MainPID` alone, or a cgroup pathname. Unit cgroup paths are reused across runtime cycles; bind the randomized systemd `InvocationID` as the generation. Pin the minimum systemd version and prove the method on the real target host; current upstream documentation says `GetUnitByPIDFD()` was added in systemd 253.

## Fixed unit and polkit boundary

Use a bounded internal slot enum mapped to literal root-owned unit names. Never interpolate task, board, profile, user, or lease strings into unit names, argv, properties, credential paths, or shell text.

Prefer direct D-Bus calls and race-free job tracking: subscribe to `JobRemoved` before `StartUnit`, then correlate the returned job. If a CLI is unavoidable, use an absolute executable, argv arrays, sanitized environment, `--no-ask-password`, and exact literal units.

A polkit rule must constrain all of:

- exact launcher UID and trusted `subject.system_unit`;
- `subject.no_new_privileges`;
- action `org.freedesktop.systemd1.manage-units`;
- exact `action.lookup("unit")` and exact `action.lookup("verb")`;
- no unit-file management, transient properties, daemon reload, arbitrary kill, or unrelated unit access.

Test `StartTransientUnit`, `SetProperty`, restart, reset-failed, enable/mask, aliases, and template instances separately. A rule that allows `verb=start` for a fixed name may still need a negative proof that a transient unit cannot redefine that name. A compromised launcher with start permission can usually still cause denial of service. If availability against launcher compromise is required, move systemd control to a root-owned narrow supervisor or directly to the broker under a narrower proven authorization path.

## Credential handoff and cleanup

Require a random token per lease generation, with only its digest stored durably. Bind authorization to board, task, run, claim lock, operations, expiry, slot, exact unit, invocation ID, and pidfd-derived process identity.

Credential rules:

- never place the token in environment, argv, logs, journal fields, reusable profile files, or general broker responses;
- do not use literal `SetCredential=` for secrets; upstream documents literal values as visible through IPC;
- keep `LoadCredential=` sources under a broker/root-owned non-renamable hierarchy inaccessible to launcher and workers;
- publish atomically with no-follow checks, exact inode capture, restrictive mode, and fsync;
- remove only the captured inode after systemd copied it, and reconcile every pre-copy/post-copy failure;
- treat deletion of the source as cleanup, not revocation: the runtime copy remains available until unit teardown, so enforce expiry/terminal revocation in broker state.

A fixed per-slot source path creates a publication/start race. Serialize source publication and unit start in one trusted owner, bind the first accepted invocation with CAS, and test launcher-driven restart during every handoff window.

## Readiness and state machine

`Type=notify` proves only the configured sender emitted `READY=1`. Require `NotifyAccess=main` and an immutable bootstrap or actual worker that notifies only after credential loading, sandboxing, broker registration, and real worker initialization. Exec-not-found and immediate post-exec failure must never produce readiness.

Use durable states such as:

`reserved -> credential_published -> start_queued -> invocation_bound -> ready/running -> terminating -> terminal`

Keep `starting` distinct from `running`. Define reconciliation for systemd-active/broker-uncommitted and broker-committed/not-ready gaps. Response loss after commit must replay by request ID without a duplicate run, principal, capability, or worker. Disable automatic worker restart unless a separately proven generation protocol prevents old credentials from binding a new invocation.

## Recovery and exact termination

On broker startup, reconcile:

`lease <-> slot <-> unit <-> InvocationID <-> pidfd/PID/start <-> UID/GID/groups <-> capability digest`.

A valid invocation may reattach within a bounded grace period. Unknown, expired, duplicate, or mismatched invocations must be stopped and terminalized. Never signal a bare PID. Use `KillMode=control-group` and prove `populated 0` before slot reuse.

Stopping by unit name can race a replacement invocation. Serialize all start/stop operations in one trusted owner and compare the expected `InvocationID` immediately before termination. If exact-invocation termination cannot be guaranteed, fail closed and quarantine the slot instead of risking termination of replacement work.

Broker unavailability must be explicit: no worker becomes ready before registration, no authoritative mutation succeeds while the broker is absent, retries are bounded, and restart reconciliation completes before new leases are issued.

## Root-owned narrow supervisor alternative

A small root-owned supervisor is safer than broad launcher polkit authority when it accepts only fixed requests such as:

- `start(slot, generation)`
- `stop(slot, expected_invocation)`
- `inspect(slot)`

It must reject arbitrary units, argv, properties, UID/GID, credential paths, and shell content; authenticate the broker UID over a private socket; own credential publication and systemd D-Bus job tracking; and return exact unit/invocation/process evidence. This adds a root TCB but removes launcher command injection, most polkit ambiguity, and many publication/start races.

## Minimum real-process proof matrix

Run in a root-capable isolated VM/CI target:

- real broker, launcher, and per-slot worker UIDs/GIDs with disjoint supplementary groups;
- sibling credential, `/proc`, FD, environment, workspace, profile, and executable-input denial;
- stolen-token use from a wrong pidfd/unit/invocation;
- PID exit/reuse between each identity subread and commit; inherited connected socket after peer death;
- lookalike, nested, user-manager, migrated, and reused unit/cgroup identities;
- compromised launcher negative matrix for other units, transient units, properties, unit files, restart, aliases, templates, and hostile names;
- crash after credential publish, start enqueue, copy, reservation, invocation bind, readiness, commit, and response write;
- exec failure, immediate exit, missing broker, bad token, and wrong invocation never reach ready/running;
- dropped worker and launcher responses replay to one durable result;
- descendant survives leader exit, then systemd stop kills the full cgroup and `populated 0` is observed;
- broker death/restart, launcher death/restart, manual start/restart races, old credential reuse, and bounded broker outage;
- exact source-inode cleanup and no stale runtime credential before slot reuse.

## First-party proof sources to pin

- Linux `unix(7)`: `SO_PEERCRED` is connection-time identity.
- Linux cgroup v2 documentation: PID listings can race/recycle; `cgroup.events populated` is the recursive liveness signal.
- systemd `systemd.exec(5)`: credential accessibility, runtime credential directory, `InvocationID`, and secret warning for literal credentials.
- systemd `org.freedesktop.systemd1(5)`: `GetUnitByPIDFD`, job monitoring, unit/runtime properties, and polkit action class.
- systemd `systemd.service(5)` / `systemd-notify(1)`: `Type=notify`, `NotifyAccess`, and READY attribution.
- systemd `systemd.kill(5)`: `KillMode=control-group` and stop behavior.
- polkit reference: `subject.system_unit`, `subject.no_new_privileges`, and action detail lookup.

Pin these claims to the target distro's systemd/polkit release or source package; latest upstream prose is not proof of a backported target implementation.
