# Adversarial local-service security audits

Use for read-only reviews of Linux Unix-socket daemons that enroll local processes, launch sandboxed workers, or emit descriptor-bound install bundles.

## Evidence and reporting

- Freeze `HEAD`, staged tree (`git write-tree`), staged blob map, and worktree state before analysis; recheck them at the end.
- In a read-only audit, do not auto-fix. Avoid repository-mutating tests and caches; prefer staged-blob reads and pure `python -B` validation probes.
- If the user requests blockers-only output, return only concrete blockers or explicit `PASS`. Every blocker needs severity, `file:line`, concrete trace, violated invariant, minimum public RED, and minimum remediation. Do not pad the response with passing surfaces.

## Kernel peer identity and liveness

- Separate credentials fixed at Unix-socket connect time (`SO_PEERCRED`) from the process that later writes through an inherited connected socket.
- Treat separate `/proc/<pid>/stat`, `status`, and inode reads as a race unless identity is pinned with pidfd or coherently revalidated. Check UID, primary GID, supplementary groups, PID, start time, parent PID, and liveness according to the authorization contract.
- Acquire the pidfd immediately after `SO_PEERCRED`, retain it across every `/proc` subread, compare repeated complete process snapshots, require exact UID/primary-GID agreement with `SO_PEERCRED`, and poll once more after the final read. Fail closed when pidfd support/acquisition is unavailable; never silently downgrade to split `/proc` reads. A deterministic portability RED can force the pidfd seam to report unavailable while using a real Unix socket pair, then require `untrusted_peer`.
- Trace identity at enrollment and every later use. A PID/start tuple stored correctly but not revalidated at authorization is incomplete.
- Check denial atomicity: if final liveness fails after a database bind commits, denied enrollment may leave durable state. Require rollback/CAS-clear or an explicit tested recovery contract.
- For post-commit enrollment liveness failure, clear only the exact `(principal, pid, start_time, binding_generation)` created by that attempt and increment generation while removing PID/GID/group/expiry fields. If compare-and-clear loses a race, do not erase the replacement binding. A real SQLite `BEGIN IMMEDIATE` barrier plus a short-lived child deterministically exposes this window without production pause hooks.

## UID/GID/group boundaries

- Trace real/effective UID/GID and supplementary groups through systemd `User`, `Group`, `SupplementaryGroups`, `Popen(user=, group=, extra_groups=)`, gates, and exec.
- Resolve service account names to numeric IDs and prove the service UID differs from every operator/ordinary-consumer UID. A config that distinguishes registrar and operator identities but never compares the operator UID with the runtime service EUID can give the operator direct DAC access to service-owned `0600` databases and keys, bypassing the socket reference monitor.
- Inventory identity provisioning artifacts, not only rendered uses: sysusers/account creation, group creation, stable numeric/name mapping, and the real registrar launch path that establishes the primary GID required by server authorization. A unit plus tmpfiles fragment cannot establish this topology on a clean host.
- Socket mode and directory traversal are admission controls only. Server authorization must independently enforce the intended UID/GID/process relationship.
- Inspect whether launcher or worker descendants inherit groups that admit them to private control sockets or authority files.

## Unix socket namespace and deadlines

- Prefer a pinned parent dirfd, `*at(..., dir_fd=...)`, no-follow opens, and exact inode identity checks.
- Verify namespace continuity: a valid socket under an old dirfd does not prove the public pathname still names that socket.
- Stale-socket reclamation must recompare identity immediately before unlink.
- Enforce one absolute monotonic deadline across connect/send/read; per-chunk timeout resets permit trickle stalls.
- Authenticate the server before sending tokens, approvals, or other authority-bearing material. Decide explicitly whether UID-only server authentication is sufficient when other sandboxed processes share the service UID.

## Landlock and protected paths

- Audit launcher confinement and nested worker confinement together; rules are inherited and overlapping path grants can turn a nominal read path into a writable subtree.
- Build protected paths from every authority-bearing surface, not just DBs and keys: future worker executables, service executable/package, config, pinned source root, policy files, public/private socket parents, and paths used to construct later trusted principals.
- Reject overlap in both directions between every writable root and every protected path at installer, daemon-load, and runtime construction boundaries.
- Audit broad ancestor **read** grants as well as write overlap. A recursive `/etc`, `/var`, package-prefix, or runtime-root read rule exposes every service-readable `0600` key/config beneath it; naming the child as "protected" does not subtract it because Landlock grants are additive. Require placement constraints or a minimal runtime-file allowlist.
- Derive future executable protection from the command's validated grammar, not a fixed `argv[:2]` heuristic. Interpreter flags, `/usr/bin/env`, wrappers, subcommands, relative scripts, and environment-assignment tokens can move executable resolution outside the paths that look absolute in argv. In particular, `('/usr/bin/env', 'PATH=/shared/profile/bin', 'worker')` protects only `/usr/bin/env` if the scanner merely collects absolute argv tokens. Either seal one exact direct-executable grammar or parse and resolve every executable-bearing path and search-path assignment before accepting writable-root separation.
- Audit shared writable homes/profile roots as future code sources, not only the configured command path. If a wrapper, interpreter, plugin loader, module search path, or environment search path can execute content from a cross-task writable profile, task A can persist code that task B executes with task B's fresh capability even though the service executable itself is protected.
- Critical persistence trace: task A modifies a future worker executable or executable-discovery input under an allowed writable root; task B launches that replacement, registers its PID, and gives it task B's fresh capability. Include a schema-valid `/usr/bin/env PATH=...` case and a shared-profile case in the real RED inventory.
- Persist and authorize effective GID plus canonical supplementary groups for every process-bound principal, not only human approvals. Trace descendant `Popen` calls for inherited service groups; if launcher/worker children keep registrar/control groups or the broker UID, filesystem modes are not an independent boundary.
- Also inspect inherited/pass-through descriptors and ABI-forward rights such as device ioctls when `/dev` is readable.

## Descriptor-bound installers

- Immediate-parent ownership/mode is insufficient if an attacker-writable ancestor can rename that parent. Verification via the old dirfd can succeed while returned pathnames resolve through an attacker replacement.
- A returned bundle pathname must name the exact verified parent and child inodes. If that cannot be guaranteed, consume verified descriptors directly or require a fully trusted, non-renameable ancestor chain.
- For a pathname API, walk from `/` to the destination parent component-by-component with `openat(O_DIRECTORY|O_NOFOLLOW)` and retain the current dirfd. Reject group/other-writable ancestors unless sticky-directory semantics protect the direct child and that child is owned by the trusted effective UID. Validate the immediate parent as trusted, perform all child work relative to its dirfd, capture verified `(st_dev, st_ino)`, then compare both public parent pathname and child entry identities immediately before returning.
- Keep the created child dirfd through writing, verification, and rollback. Cleanup should not need a fresh fd after failure.
- Strengthening parent traversal can invalidate an older EMFILE harness because the ancestry walk itself temporarily needs parent and child descriptors. For deterministic post-create rollback coverage, pre-open the trusted parent, fork, set the child's descriptor limit so exactly the next `openat` fails, invoke the descriptor-bound create primitive, and verify the new directory is absent before exercising the public renderer normally. Do not let an uncaught failure return the forked child into the pytest runner.
- Do not swallow cleanup errors; verify absence before claiming rollback.
- For atomic publication, build and verify under a private temporary name, fsync files/directories, then no-replace rename within a trusted pinned parent. Directly populating the final no-overwrite name is not crash-safe: process death leaves a visible partial destination that blocks retry. Test abrupt termination after directory creation, after each file, and before parent fsync; every retry must either recover the incomplete attempt safely or publish a fresh complete bundle without manual deletion.

## Minimum real RED inventory

- Process exits or is PID-reused between identity subreads.
- Wrong primary GID with an allowed supplementary group, and inherited group leakage into descendants.
- Parent socket directory is renamed and replaced while the server is live.
- Trickle-frame deadline and bounded connection-admission/drain tests.
- Each worker-writable root overlapping each protected authority path, especially `worker_command[0]`.
- Worker A replaces a future executable; task B must never execute it or receive a capability through it.
- Installer parent beneath a real non-sticky writable ancestor; render/verify must reject or fail closed on namespace pivot.
- RLIMIT/EMFILE before child-open and after child creation; no partial bundle may remain.
