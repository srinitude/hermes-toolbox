# Launcher principal enrollment and service assembly

Use this reference when a launcher library or CLI exists, but a separately executed launcher must become a PID/start-time-bound principal without opening the broker sidecar database.

## Detect the enrollment gap

Trace the first public launcher request back to its authorization prerequisite. A design is not deployable when all of these hold:

- checkout requires a pre-existing principal row matching UID, PID, start time, and profile;
- the launcher has no authenticated enrollment path;
- the store only exposes an insert helper used by fixtures or deployment prose;
- tests seed the principal with the test process identity and invoke the launcher CLI function in-process.

An in-process CLI test preserves the fixture process PID/start time and therefore does not prove a separately executed launcher. Require a real subprocess test.

Also distinguish a callable socket server from service assembly. A production path must construct the runtime, bind the socket, establish trusted principals, supervise shutdown, and expose an executable entry point.

## Preferred secure contract

Prefer broker-supervised, gated enrollment over a public generic principal-creation operation:

1. load fixed broker-owned launcher configuration: stable principal ID, exact profile, expected OS identity, and bounded absolute argv;
2. start the launcher as a separate direct child behind a one-byte or equivalent startup gate;
3. open and hold a pidfd, derive UID, parent PID, and start time from the kernel, verify the expected direct-child relationship, and reject an exited child;
4. atomically bind or safely rebind the stable launcher principal using only broker-derived identity;
5. start or verify socket readiness;
6. release the launcher gate;
7. retain supervision through signal forwarding, bounded escalation, wait/reap, and running-lease reconciliation.

Do not accept PID, process start time, UID, principal class, or internal database paths from launcher arguments. A stable principal ID may come from trusted service configuration, not from untrusted enrollment content.

## Restart-safe binding

An insert-only principal helper is insufficient. The broker-owned binding transaction must:

- require the existing row, if any, to have the exact configured kind/profile/static identity;
- deny replacement while the previous PID/start tuple is still alive;
- allow replacement only after exact stale-process verification;
- serialize concurrent attempts;
- persist the new PID/start tuple atomically;
- fail closed on ambiguous process state.

Use PID plus start time as durable identity and pidfd as the live handoff guard. Never store a pidfd in SQLite.

## Filesystem and OS isolation

Mode `0700` on the sidecar directory and `0600` on the database does not prevent writes by a launcher running under the broker's UID. A secure deployment needs one of:

- distinct broker and launcher OS identities, with the sidecar/native databases accessible only to the broker; or
- an equivalent mandatory sandbox/mount namespace that denies launcher and worker access to those paths.

The launcher should receive the Unix socket and task/worker configuration only—never the sidecar path, digest key, native authority path, or unrelated ambient credentials. Configure the socket directory/group independently from database ownership.

If independent service units are unavoidable, use a dedicated authenticated bootstrap/control channel or one-time inherited credential and still derive PID/start time from `SO_PEERCRED`. UID alone can be insufficient when launcher-spawned workers inherit that UID and could attempt re-enrollment after launcher death.

## Required real tests

Use real processes, Unix sockets, and temporary native/policy databases:

- a separately executed launcher is denied before broker enrollment;
- enrollment stores the exact kernel-derived launcher PID/start time;
- caller-supplied PID/start/UID fields are rejected or absent from the protocol;
- non-child, wrong-identity, exited, and concurrent replacement attempts fail;
- a live prior binding blocks replacement and a verified dead binding can be renewed;
- checkout cannot occur before gate release and succeeds afterward;
- launcher argv/environment omit database paths, digest keys, and unrelated credentials;
- deployment isolation prevents launcher/worker database access;
- launcher death cannot orphan an authoritative worker;
- the complete service → launcher subprocess → worker subprocess → broker path is exercised through installed/public entry points.

Static checks that launcher modules do not import SQLite or the broker store are useful, but they do not replace OS-level isolation and real-process behavior.
