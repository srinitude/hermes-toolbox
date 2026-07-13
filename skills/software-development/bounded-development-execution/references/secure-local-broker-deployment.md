# Secure Local Broker Deployment

Use this checklist when turning a tested local Unix-socket broker into an installed service. Unit/integration coverage of handlers is not deployment completeness: the service must construct production dependencies, enroll process identities, dispatch work, supervise children, and support recoverable operations from installed artifacts.

## Process identity and enrollment

Treat kernel UID/PID/start time as runtime state, never static service-file configuration.

### Launcher enrollment

For a production topology with distinct broker and launcher identities, the broker must **not** spawn, gate, or parent-enroll the launcher. Configuration metadata is not identity separation.

1. Provision the broker and launcher as separate service-manager units with pairwise-distinct primary UID/GID and bounded supplementary groups.
2. The launcher opens the broker Unix socket and sends an argument-free enrollment request. It must not supply PID, UID, group, unit, cgroup, or invocation identity.
3. The broker derives `SO_PEERCRED`, opens and holds a pidfd for the peer, reads PID/start time/UID/GID/groups from the kernel, and resolves that pidfd through the service manager (for systemd 255, `GetUnitByPIDFD`).
4. Require the literal configured launcher unit, canonical unit object path, 16-byte invocation ID, expected main PID, and matching unified cgroup. Double-read process and cgroup facts around the service-manager query and fail closed on drift or inspection ambiguity.
5. Persist PID/start time/UID/GID/groups, service unit, and invocation ID in one CAS. Every later launcher request re-resolves and compares the same service generation; enrollment alone is not continuing authority.
6. Initial binding is allowed only when absent. Replacement requires positive death or PID-reuse evidence for the exact prior binding. A live or ambiguously inspectable prior generation denies replacement without mutation.
7. The launcher is scheduling-only: it receives no capability token, worker PID, credential path, unit-control handle, polkit grant, database access, or identity-changing capability.

Development-only direct-process fixtures may remain temporarily for compatibility, but production runtime assembly must make them unreachable. Real acceptance requires separate service identities; same-UID or parent-child emulation is not rollout proof.

### Human/operator enrollment

An exact human principal bound to PID/start time cannot be safely represented as a fixed systemd value. Do not weaken this to same-UID trust merely to simplify installation.

Use a separate broker-private registrar socket. Do not expose a public `operator.enroll` operation or reusable bearer material.

1. A privileged registrar authenticates the operator, enters with its dedicated configured UID/GID, spawns the installed CLI as its direct child behind a one-byte gate, drops the child to the configured non-root operator UID/GID, clears supplementary groups, and sends only the child PID over the private channel. The registrar needs only the narrowly approved `CAP_SETUID`/`CAP_SETGID` path (or an explicit root invocation); ordinary operator processes must not possess the registrar identity.
2. The broker authenticates the registrar's exact UID/GID with `SO_PEERCRED`, opens/holds a pidfd for the child, derives UID/GID/supplementary groups/parent PID/start time from the kernel, requires the registrar as parent, requires the configured operator UID/GID, and fails closed on missing `Gid:` or `Groups:`, ambiguous `/proc`, or liveness state. A cross-identity child with any supplementary group is denied.
3. Persist one fixed operator principal with static ID/kind/profile/non-root UID and ephemeral PID/start time, monotonic binding generation, and session expiry. Production config must reject registrar/operator UID equality, registrar/operator GID equality, and operator UID/GID zero. Daemon startup may accept a statically valid unbound principal, but every human read/mutation must remain denied until enrollment.
4. Bind with one SQLite CAS. Generic human sessions may use expiry-based renewal when that is their declared contract, but an operator session may use the initial-bind path only from a completely unbound row. Expiry alone never proves an operator process is dead and must not permit overwrite. Operator replacement increments generation only after positive death/reuse evidence and an exact previously observed PID/start/generation CAS.
5. Acknowledge enrollment only after durable binding, then release the child gate. Failure leaves the CLI blocked and requires process-group kill/reap plus closure of both gate descriptors.

Every human authorization decision must require the current static principal metadata, `SO_PEERCRED` UID/PID/GID, kernel-derived start time and supplementary groups, binding generation, and unexpired session. Persist the bound primary GID and a canonical bounded supplementary-group tuple alongside PID/start/generation/expiry; re-read `/proc/<pid>/status` at context construction and again before challenge mint/reservation. A process that keeps the same PID/start time across `exec` can still acquire a new effective GID or supplementary groups through setgid/file capabilities, so enrollment-only GID/group checks are insufficient. Include the complete identity tuple in the keyed trusted-context proof; caller actor JSON remains non-authoritative.

Treat prior-process liveness as three states, not a boolean. Replacement is allowed only on positive death evidence: `pidfd_open` returning `ESRCH`, a readable pidfd, or a live reused PID whose kernel start time differs from the persisted start time. `EINVAL`, `EMFILE`, permission failures, malformed/missing `/proc`, and other inspection uncertainty are **unknown**, not dead, and must deny replacement without changing the durable binding. Exercise this with real kernel cases (for example, a persisted invalid PID causing `pidfd_open` `EINVAL`) rather than monkeypatching the liveness helper.

Bind approval challenges to the same operator session by persisting principal ID, UID/profile, PID/start time, primary GID, canonical supplementary groups, generation, and session expiry. The atomic reservation predicate must verify every field against the current principal row (for example with an `EXISTS` subquery), so a delegated worker cannot reserve after operator expiry, rebinding, or post-mint GID/group drift. Schema upgrades that add posture fields must invalidate legacy operator bindings lacking that posture while preserving unrelated generic-human bindings; pre-migration challenges with null session/posture fields fail closed. Keep plaintext approval tokens only in the CLI process memory: preview → render exact request → `/dev/tty` confirmation → execute in the same process; never place tokens in argv, environment, disk, logs, audit, recovery records, or child processes. Preview verification must compare every proposed field, require the single-use approval token, reject any hidden capability token, and redact both token fields before display. Parse argument/project JSON with explicit type branches—never call mapping methods after a non-short-circuit boolean check—and convert malformed shapes to one fixed denial without traceback.

The operator CLI must have no native fallback. Each pinned native parser path maps to a broker read, broker preview/approved mutation, or explicit fail-closed exclusion. Privileged acceptance still requires distinct broker/registrar/launcher/worker identities and real filesystem, socket, ptrace, and process-isolation tests; local same-UID emulation is not proof of rollout security.

For compromised-broker or hidden-authority defenses, replace in-process recording/fake clients with an actual local Unix service and the production client codec. The adversarial service may deliberately return a well-formed malicious frame (for example, a preview carrying a hidden capability), but normal read/mutation/cancellation success evidence must come from the real broker. Capture expected server-thread failures in the harness and assert them explicitly; warning-only background exceptions are not clean GREEN evidence.

## Daemon completeness gate

Before calling the broker deployable, prove that installed code can:

- load a strict bounded config with unknown fields rejected;
- read secret keys from owner-only files rather than YAML or argv;
- resolve the exact checked-in policy identity and preprovisioned board binding;
- validate a statically configured human principal and deny human operations while it is unbound;
- verify live enrolled human sessions and launcher identities before authorizing their operations;
- construct the pinned production native adapter;
- open and remove the Unix socket safely;
- run request serving and dispatch reconciliation;
- authenticate a separately managed launcher generation and accept scheduling ticks;
- reserve a fixed worker slot durably before publishing credentials or requesting activation;
- start/stop only the literal worker unit through the service manager, with no launcher unit-control authority;
- reconcile persisted activation/lease states before protocol readiness;
- handle signals and shut down without abandoning an authorized worker;
- emit bounded nonsecret diagnostics.

A server helper exercised only from tests is not a daemon entry point. A daemon that serves requests but never dispatches or starts its launcher is also incomplete.

### Dual-group Unix-socket topology

When registrar and operator identities are intentionally distinct, one service-group-owned `0660` socket cannot authorize both audiences safely. Use two protected runtime directories and two socket nodes:

- public broker socket chgrp'd to the configured operator GID;
- private enrollment/control socket chgrp'd to the configured registrar GID;
- configure the service manager to grant the daemon both the registrar and operator supplementary groups explicitly, while the gated operator child clears supplementary groups;
- require separate absolute, preprovisioned runtime parents owned by the daemon UID, assigned to the exact audience GID, and mode `0710`; reject missing, symlinked, shared-parent, wrong-owner/GID, or wrong-mode paths instead of creating or repairing them at runtime;
- when shipping an inert install bundle, authenticate a tmpfiles fragment (or equivalent declarative provisioning artifact) that defines both directories, and render empty capability bounding/ambient sets unless a separately approved privileged registrar unit needs narrowly scoped capabilities;
- capture the bound filesystem socket's `(st_dev, st_ino)` immediately after `bind`, verify configured GID/mode, revalidate that the published namespace still names that inode during the accept loop, and terminate on deletion/replacement; unlink on cleanup only if the current path is still the same socket inode. Never use a bare `lstat`→`unlink` sequence in a directory an untrusted identity can modify.

Exercise each chgrp with GIDs genuinely available to the test process; do not simulate ownership success. If distinct identities/groups require privileges unavailable locally, keep that acceptance explicitly deferred rather than weakening production checks.

### Supervision and cleanup

Readiness is not lifetime supervision. The foreground broker must continuously monitor its public/control servers, socket namespaces, persisted lease/activation state, and the exact fixed worker unit generation. The separately managed launcher is supervised by the service manager, not parented or reaped by the broker. Unexpected server-thread exit, socket replacement, unit-generation drift, or ambiguous activation recovery is a service failure rather than silent partial operation.

Worker shutdown is unit/cgroup based: compare the persisted invocation ID before `StopUnit`, wait for the exact correlated job result, require the prior cgroup to become unpopulated, scrub credential/runtime state by captured inode, and only then mark the slot reusable. Do not kill a bare PID or PID-derived process group. Capture background failures explicitly in tests, use shared monotonic deadlines, attempt every cleanup obligation, and preserve the first meaningful failure.

## Descriptor-bound inert bundle publication

Treat install-bundle staging as a directory race boundary, even when the destination is local and inert:

1. Open the trusted parent once with `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC`, validate owner/type/write bits from `fstat`, and retain that descriptor through creation, hashing, manifest signing, verification, cleanup, and parent `fsync`.
2. Create the destination with `mkdirat`/`dir_fd` and no overwrite. Track whether this invocation actually created it; an `EEXIST` path must never enter cleanup or delete a pre-existing bundle.
3. Open the new bundle directory relative to the retained parent. Create every file with `O_CREAT|O_EXCL|O_NOFOLLOW`, loop over short writes, `fsync` each file, then `fsync` the bundle directory and parent.
4. Hash and parse files through descriptor-relative `openat` plus `fstat`. Verify regular-file type, exact owner/mode/size/digest, manifest HMAC, and `os.listdir(directory_fd)` membership without re-resolving `bundle/name` pathnames.
5. On failure, unlink only the fixed filenames relative to the directory fd and remove only the directory name relative to the retained parent. Never use pathname-recursive deletion at this trust boundary.
6. Public verification should open the parent once, open the named bundle relative to it, and perform the same fd-relative checks. Returning `Path` handles for callers is fine; using them as verification authority is not.
7. Preprovision socket parents and all launcher profile/log/workspace roots declaratively. Runtime code may validate or open them, but should not repair privileged topology.

Keep these primitives in a bounded companion module when the renderer is near structural limits. Test no-overwrite preservation, symlink/tamper rejection, writable-parent denial, manifest exactness, and successful config loading from the staged artifact. Review the exceptional path specifically: cleanup after failed creation is a common bug that deletes an existing destination.

## Installed-artifact portability

Never bake a developer home, editable source path, or ambient `PYTHONPATH` into production source.

- Make interpreter and pinned source/runtime roots explicit validated configuration.
- Validate a venv Python symlink by resolving its target, but execute the original venv path. Executing the resolved base interpreter can silently drop the venv's packages.
- Keep caller-supplied `PYTHONPATH`, loader variables, and arbitrary environment values forbidden. If a pinned source root is required, inject exactly that validated first-party root.
- Build a wheel, install it into a disposable venv, change to a directory outside the repository, and verify import origins plus every console-script/help surface.
- Record the wheel checksum as evidence, but rebuild after later source changes; an old checksum is not final-artifact evidence.

## Offline backup and staging restore

For separate native and sidecar SQLite stores, use an explicit offline fence rather than claiming cross-database point-in-time atomicity while the broker is live.

1. Refuse backup while the broker socket exists, including stale/symlink paths that require operator resolution.
2. Hold a nonblocking process lock to prevent concurrent backups.
3. Use SQLite's backup API for WAL-consistent copies and run `PRAGMA quick_check` on every copy.
4. Write databases and manifest under private directories with `0600` files.
5. Authenticate a canonical bounded manifest with HMAC-SHA256 and record per-file SHA-256 plus byte size.
6. On verify, reject symlinks, malformed identifiers, hash/size mismatch, SQLite corruption, duplicate entries, and any unmanifested extra file.
7. Restore only into a new staging directory; never overwrite live databases. Verify each restored copy before atomically publishing the staging directory.
8. Clean temporary files/directories on every failure path.

The socket fence is sound only when the broker is the sole authorized writer after cutover. Before that gate, report the weaker pre-cutover limitation explicitly.

## Verification matrix

- Real gated launcher completes one task and then polls idle under the same launcher PID.
- Reaped launcher is replaced by exact stale-binding CAS.
- Live launcher replacement is denied before child/log creation.
- Clean exit, crash, timeout escalation, same-server replay, restart replay, first-pass orphan cleanup, and resumed `terminating` cleanup remain green.
- Wheel import and console scripts run outside the source tree.
- Backup create/verify/restore succeeds for native and sidecar databases.
- Live socket, tampered database, altered manifest, extra file, symlink, and existing restore target fail closed.
- Pinned upstream commit and cleanliness are checked separately from the project tree.
