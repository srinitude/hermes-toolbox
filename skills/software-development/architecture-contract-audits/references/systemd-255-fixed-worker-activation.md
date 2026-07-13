# systemd 255 fixed-worker activation audit notes

Use this note when mapping a fixed service such as `worker0.service` from direct `Popen` supervision to systemd-mediated activation.

## Cheap blocker-first preflight before expensive suites

For a read-only fixed-worker security preflight, inspect production paths before running any suite. Stop and report candidate-invalidating blockers when any of these equations fails:

1. **Fresh-slot operability:** pre-start inspection uses `LoadUnit()` for a possibly unloaded static unit; the `inactive + MainPID=0` branch is handled before requiring a nonempty `ControlGroup`; activation actually calls this path.
2. **Launcher liveness:** the launcher request holds a pidfd from kernel-derived authorization through durable reservation, credential publication, and the accepted start boundary. A resolver that opens and closes a pidfd before returning is not request-wide protection; token-only guards commonly omit launcher requests.
3. **Worker commit revalidation:** every capability request, readiness transition, and replay repeats `GetUnitByPIDFD()` plus `Id`, `InvocationID`, `ControlGroup`, `MainPID`, `ActiveState`, and `SubState` immediately before each committing transaction. Polling a held pidfd against cached systemd properties is insufficient, and a final check after handler return cannot roll back an earlier commit.
4. **Native-state recovery discrimination:** do not infer that native start committed merely because sidecar invocation binding persisted a worker PID. Read exact authoritative task/run state and choose worker-exit versus launch-failure accordingly.
5. **Unknown-unit startup reconciliation:** inspect the fixed unit even when no open activation row exists. An active or ambiguous invocation must be stopped by exact generation, quarantined, or block broker readiness.
6. **Replacement-safe stop:** require stored worker PID/start, current `MainPID`, invocation ID, and cgroup to match before stop. A precheck followed by name-based `StopUnit()` remains a replacement race unless starts/stops are serialized in one trusted owner and mismatch handling quarantines rather than killing.
7. **Slot-reuse filesystem closure:** prove the prior cgroup is empty and that no worker-writable profile, plugin, config, workspace, hook, or executable input can persist code or secrets into the next lease. A dedicated UID per slot does not make persistent worker-owned plugin code safe.
8. **Durable credential cleanup:** unlink the captured source inode through a held directory descriptor, fsync the parent, and only then commit scrubbed state. Reconciliation of `cgroup_empty`/`scrubbed` rows must still prove source absence; otherwise fixed-path `O_EXCL` publication can wedge forever after power-loss reorder.

Use exact file/line evidence for each failure and distinguish static findings from real-systemd acceptance. If the user prohibited tests, do not run even a focused probe; seal the inspected source hashes/status twice instead and state that privileged systemd/polkit/cgroup behavior remains unobserved.

## Exact systemd 255 D-Bus surface

Use the system bus destination `org.freedesktop.systemd1`, manager object `/org/freedesktop/systemd1`, and interface `org.freedesktop.systemd1.Manager`.

- `Subscribe()` (`- -> -`) before enqueueing jobs.
- `GetUnit(name)` (`s -> o`) only for an already loaded canonical unit object; it fails when the unit is not loaded.
- `LoadUnit(name)` (`s -> o`) for fixed-name pre-start inspection when a static worker may be unloaded after boot.
- `StartUnit(literal_unit, "fail")` (`ss -> o`).
- `StopUnit(literal_unit, "fail")` (`ss -> o`).
- `GetUnitByPIDFD(pidfd)` (`h -> osay`): unit object, unit ID, invocation ID bytes. Pass a real Unix FD through D-Bus FD passing, never the PID integer.
- Correlate `JobRemoved(u id, o job, s unit, s result)` with the exact returned job object. Accept only the literal unit and result `done`.

Read through `org.freedesktop.DBus.Properties.Get`:

- `org.freedesktop.systemd1.Unit`: `Id`, `ActiveState`, `SubState`, `InvocationID`.
- `org.freedesktop.systemd1.Service`: `ControlGroup`, `MainPID`.

Pin property ownership to the target systemd release instead of assuming it from generic D-Bus summaries. On systemd 255, read `ControlGroup` from the `Service` interface; a focused read-only probe is `busctl get-property --system org.freedesktop.systemd1 <unit-object> org.freedesktop.systemd1.Service ControlGroup`. Keep this probe distinct from privileged activation acceptance: it verifies interface shape only.

Disable interactive authorization on D-Bus messages. Direct calls avoid `systemctl`, shell parsing, and password-agent behavior.

## Identity invariant

For each bootstrap and capability-bearing Unix-socket connection:

1. Read `SO_PEERCRED` at accept time.
2. Immediately open and retain `pidfd_open(peer.pid, 0)`.
3. Read PID/start/UID/effective-GID/supplementary-groups and unified `/proc/PID/cgroup` twice.
4. Call `GetUnitByPIDFD` and require the exact fixed unit, canonical object, and a nonzero 16-byte invocation ID.
5. Require returned invocation ID to equal `Unit.InvocationID`, and `/proc/PID/cgroup` to equal `Service.ControlGroup`.
6. Require the configured dedicated worker UID/GID/groups and acceptable `ActiveState`.
7. If the worker entrypoint stays the service main process, require `Service.MainPID == peer.pid`.
8. Repeat pidfd liveness, process identity, cgroup, and `GetUnitByPIDFD` immediately before commit.
9. Persist slot, literal unit, invocation ID, PID/start/UID/GID/groups, activation generation, lease scope, and capability digest.

A cgroup path and `MainPID` are corroboration, not generation identity. Cgroup paths are reused; `InvocationID` distinguishes activations.

## Credential and readiness sequence

The broker—not the launcher—generates and publishes the activation token. Store only its digest durably. Publish a bounded `0600` source under a broker-owned directory using no-follow/exclusive creation, capture device/inode, fsync, and atomic rename. The launcher receives no token, PID, credential path, unit name, or systemd authority.

The fixed worker unit should use at least:

```ini
Type=notify
NotifyAccess=main
Restart=no
KillMode=control-group
SendSIGKILL=yes
LoadCredential=activation:/run/example/activations/worker0
RuntimeDirectory=example-worker0
RuntimeDirectoryMode=0700
RuntimeDirectoryPreserve=no
```

Keep `ExecStart` and config paths literal. Do not add an `[Install]` target to the worker unit: it must not start at boot with stale or absent credential state.

The worker reads `$CREDENTIALS_DIRECTORY/activation`; never copy the token into argv, a general environment variable, logs, journal fields, or launcher responses. A robust two-phase startup is:

1. pre-exec bind authenticates token plus exact systemd identity and returns non-secret lease metadata;
2. the fixed process applies sandboxing and initializes/execs the real worker while preserving PID;
3. a post-exec plugin in the same main process calls a broker readiness route;
4. broker rechecks pidfd/unit/invocation, commits native start and capability activation;
5. only then the main process sends `sd_notify(0, "READY=1...")`.

If same-PID post-exec notification is impossible, a persistent main supervisor may notify only after an authenticated child handshake; then authorization must deliberately distinguish service `MainPID` from the child pidfd while still requiring the same exact unit and invocation. Never notify before exec/real initialization merely because credential loading succeeded.

## Durable state and compensation

Recommended activation states:

`reserved -> credential_published -> start_queued -> invocation_bound -> registered -> ready/running -> stop_queued -> cgroup_empty -> scrubbed/terminal`

Do not hold a database transaction while waiting for a `Type=notify` start job: worker registration must remain serviceable or startup deadlocks.

### Fresh-unit and empty-slot inspection

A fixed worker with no `[Install]` target is commonly not loaded after boot. On systemd 255, `GetUnit(name)` fails for an unloaded unit; use the fixed-name `LoadUnit(name)` (`s -> o`) for pre-start inspection, then verify the returned canonical object and exact `Id`. Keep `GetUnit()` for already-resolved identity checks where failure is meaningful.

Handle inactivity before active-only property invariants. `inactive + MainPID=0` is an empty slot when the prior cgroup is absent or proven `populated 0`; do not require a nonempty slash-prefixed `ControlGroup` before the inactive branch. Add a real systemd RED that inspects a never-before-loaded static unit.

Startup reconciliation must inspect the fixed unit even when there is no open activation row. A record-only early return can let an unknown active invocation survive broker readiness. With no matching durable activation, stop the observed exact invocation and prove inactive/cgroup-empty/source-absent, or fail readiness and quarantine the slot.

### Native-state discrimination during recovery

Persisting a bound worker PID does not prove that the authoritative native `worker started` transition committed. A process may die after `invocation_bound` but before post-exec readiness; conversely, native start may commit while sidecar finalization remains at `invocation_bound`.

Recovery must read exact authoritative task/run post-state:

- exact expected worker PID present with matching run/claim: record worker exit;
- worker PID absent with matching active run/claim: record launch failure;
- any other PID, run, claim, or terminal mismatch: quarantine/fail closed.

Never choose `record_worker_exited` merely because the activation sidecar has an integer `worker_pid`. Test death after bind but before readiness, and native-start-committed/sidecar-not-finalized separately.

### Commit-time systemd revalidation

A held pidfd plus cached unit properties is not the complete final guard. Immediately before each capability or readiness commit, re-run `GetUnitByPIDFD` through the held pidfd and re-read `Id`, `InvocationID`, `ControlGroup`, `MainPID`, `ActiveState`, and `SubState`; require the complete identity to equal the initially captured generation. A final process/cgroup-only check, or a recheck after the committing transaction returns, is insufficient.

### Durable credential-source removal

Exact-inode cleanup must be durable relative to the sidecar `scrubbed` commit. Unlink through a held broker-owned directory descriptor, verify the captured device/inode, fsync the parent directory, then commit scrubbed state. Otherwise a persistent runtime root can retain a stale fixed source after power loss; the next `O_EXCL` publication fails before the new activation records an inode, creating a repeatable slot wedge. Startup and slot-reuse reconciliation must also prove source absence or reconcile it to a provenance-matched historical activation.

Compensate each boundary:

- publish-before-start crash: resume only if captured inode, lease, and empty slot still match; otherwise exact-inode cleanup and terminalization;
- start error/job failure/timeout: revoke, stop any bound invocation, wait for empty cgroup, scrub, and record launch failure;
- native start committed but pre-READY death: recover as worker exit and revoke;
- lost READY/job response: reconcile durable ready state plus exact invocation and unit properties, never start a duplicate;
- stop response loss: reissue only if the expected invocation still owns the fixed unit; mismatch means quarantine, not name-based killing;
- broker restart: reconcile the fixed unit before readiness and before issuing new leases;
- source deletion is cleanup, not revocation—the runtime credential copy survives until unit teardown.

Before slot reuse require `ActiveState=inactive`, `MainPID=0`, source absence, runtime-directory scrub, and cgroup-v2 `cgroup.events` reporting `populated 0` (or exact cgroup disappearance). `populated 0` is recursive and proves no live process in the cgroup subtree.

## Polkit boundary

Grant only the broker service account, only when `subject.system_unit` is the broker system unit and `subject.no_new_privileges` is true, only action `org.freedesktop.systemd1.manage-units`, only the alias-resolved fixed unit, and only verbs `start`/`stop`. The launcher gets no rule.

Negative real tests must cover restart, kill, reset-failed, set-property, transient units, aliases, templates, other units, unit-file management, mask/enable, and daemon reload.

## Evidence and drift discipline

A concurrent dirty tree can change bytes while `git status` path/state classes remain unchanged. Record the requested digest producer, literal HEAD, status digest, tracked-diff digest, staged digest, and untracked manifest. Recheck at the end. If the content digest moves, label source findings unsealed and separate the stable architecture recommendation from claims about the moving implementation.

When a partial repair adds distinct UID fields but production assembly still invokes direct spawn, classify it as inoperable partial remediation—not systemd activation. Also cross-check installer-emitted config version against daemon-required schema version.

## Real-test boundary

Systemd acceptance requires a root-capable disposable VM or CI image booted with the target systemd release. In-process D-Bus doubles, same-UID subprocesses, rendered-unit assertions, and synthetic principal insertion do not prove polkit, credentials, invocation identity, readiness, cgroup teardown, or scrub behavior.
