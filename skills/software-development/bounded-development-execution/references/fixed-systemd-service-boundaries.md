# Fixed systemd Service Boundaries

Use this reference when a local broker, scheduler/launcher, and worker must be separated by OS identities and systemd-managed lifecycle. It is a design and execution checklist, not permission to install units, create accounts, or activate services.

## Trust topology

- Use pairwise-distinct broker, launcher, and fixed worker-slot primary UID/GID values in production. Treat supplementary groups as identity too.
- Broker owns authority state, activation state, capability digests, credential sources, and literal worker-unit start/stop.
- Launcher only enrolls and sends argument-free scheduling ticks. It gets no worker capability, PID, credential path, database access, unit handle, polkit grant, or `CAP_SETUID`/`CAP_SETGID`.
- Worker self-registers over the broker socket. The launcher never reports a worker PID on its behalf.
- Keep privileged installer artifacts inert until a separately approved acceptance/cutover step.

## Kernel and systemd identity proof

For each launcher enrollment and each worker bind:

1. Read `SO_PEERCRED` from the accepted Unix socket.
2. Open and hold a pidfd for the peer. Missing pidfd support or inspection uncertainty fails closed.
3. Read PID/start time/UID/GID/canonical supplementary groups and unified cgroup from `/proc`.
4. Call systemd Manager `GetUnitByPIDFD(h)` using Unix-FD D-Bus negotiation.
5. Require the literal allowed unit and canonical object path. Read `Id`, `InvocationID`, `ActiveState`, and `SubState` from `org.freedesktop.systemd1.Unit`; read `ControlGroup` and `MainPID` from the service-specific interface.
6. Require a nonzero 16-byte invocation ID, expected main PID, expected cgroup, and configured UID/GID/groups.
7. Re-read process/cgroup facts while the pidfd is held. Any drift or ambiguous result denies without mutation.
8. Persist the service unit and invocation ID with PID/start time/UID/GID/groups. Re-resolve the generation on every later authorized launcher or worker request.

A maintained pure-Python D-Bus transport with explicit FD negotiation is acceptable when native systemd bindings cannot be built without privileged development packages. Do not fall back to `systemctl`, bare PID lookup, or caller-supplied unit identity.

## Fixed worker activation state machine

Persist activation intent before external side effects. A useful monotonic sequence is:

```text
reserved
credential_published
start_queued
invocation_bound
registered
ready
stop_queued
cgroup_empty
scrubbed
```

Keep `failed` terminal. Enforce one nonterminal owner of slot 0 with a partial unique index so terminal history does not block reuse.

Persist at least activation ID, lease ID, slot, literal unit, state, token digest, credential device/inode, invocation ID, worker PID/start time, cgroup, and timestamps. Migrations add nullable service fields without rewriting legacy open leases. Startup must reject legacy nonterminal leases lacking required slot/unit/invocation/activation identity; it must not silently reinterpret or mutate them.

## Credential and readiness flow

1. Broker selects one authoritative pending lease and atomically reserves slot 0.
2. Broker generates an activation ID and random capability token; persist only the keyed digest.
3. Publish a bounded canonical credential source with `O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC`, mode `0600`, short-write loop, file `fsync`, directory `fsync`, and captured `(st_dev, st_ino)`.
4. Configure the fixed worker unit with `LoadCredential=`, `Type=notify`, `NotifyAccess=main`, `Restart=no`, and `KillMode=control-group`.
5. Call `Subscribe` before `StartUnit`; correlate the exact `JobRemoved` path/unit/result. Job creation is not readiness.
6. Worker reads only the named file in `CREDENTIALS_DIRECTORY`, then sends argument-free self-bind and ready requests with the credential token.
7. Broker derives worker PID/unit/invocation/cgroup itself, issues capability atomically with the running lease transition, and records durable `ready`.
8. For same-PID bootstrap→`execve` flows, send `READY=1` only after the real executable loads the broker plugin and all required override tools register. Pre-exec notification is premature.
9. Broker treats `StartUnit` success as valid only when the corresponding durable activation reached `ready`.
10. Remove the credential source only by its captured inode after the service manager has consumed it and protocol readiness is durable. Replacement or cleanup ambiguity is recovery-required.

The launcher response should be coarse (`idle`, `busy`, `started`) and secret-free. A worker-ready response may contain a bounded lease DTO, never raw rows containing BLOBs or internal authority fields.

## Stop and recovery

- Before `StopUnit`, compare the current unit invocation with the persisted one.
- Subscribe before stop and correlate the exact job result.
- Require the persisted cgroup to report `populated 0`; do not kill a bare PID or PID-derived process group.
- Scrub credential/runtime files by captured inode and then mark the slot reusable.
- Reconcile every nonterminal activation/lease state before broker readiness. Unknown external state blocks readiness rather than guessing.
- Compensation must attempt durable failure marking and native rollback even if credential cleanup fails; report cleanup ambiguity after recovery attempts.

## Installer boundary

Render an authenticated inert bundle containing separate broker, launcher, worker0, and target units plus explicit sysusers, tmpfiles, config, manifest, and narrowly scoped broker-only polkit policy if needed. Publication remains descriptor-relative, no-follow, no-overwrite, durable, and crash-atomic. Do not execute sysusers/tmpfiles, copy into privileged destinations, reload systemd, create accounts, or start services without a separate approval gate.

## Verification order

1. Migration RED→GREEN, including legacy nonterminal preservation plus startup refusal.
2. Read-only live systemd proof of `GetUnitByPIDFD` and property decoding.
3. Real Unix-socket launcher enrollment with invocation persistence and live-generation replacement denial.
4. Credential no-replace/inode cleanup tests.
5. Durable activation success/failure/recovery tests.
6. Worker-self bind/ready tests proving caller-supplied PID/lease identity is rejected in production.
7. Inert bundle parsing and exact artifact inventory tests.
8. Separately approved root-capable process/unit/cgroup acceptance with distinct accounts.
9. Full regression, exact wheel/install proof, final digest, fresh pinned audits, and only then commit/cutover.

Never claim root boundary proof from a callback/fake starter, same-UID process, unit renderer, or read-only systemd probe. Those are useful focused evidence, not rollout acceptance.
