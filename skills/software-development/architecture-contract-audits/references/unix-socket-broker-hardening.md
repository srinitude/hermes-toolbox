# Unix-socket broker hardening audits

Use this reference for read-only audits and test-first designs covering local newline-framed broker servers before adding new consumers such as operator CLIs.

## Evidence trace

Inspect the complete accepted-connection lifecycle:

1. listener parent validation and socket-path preparation;
2. `listen()` backlog and application admission bound;
3. accept-loop behavior;
4. frame acquisition deadline;
5. peer-credential derivation;
6. request validation/dispatch;
7. response write deadline;
8. active-connection tracking;
9. stop/drain behavior;
10. exact socket-path cleanup.

A bounded client does not make a serial server available. Verify the server can accept and serve an independent health connection while another client holds an incomplete frame.

## Frame deadline

Require a total, monotonic deadline for acquiring one frame. A fixed per-`recv()` inactivity timeout is vulnerable to slow trickle traffic because each byte can restart the timeout. Before every read, calculate the remaining budget from one `time.monotonic()` deadline and fail when it is exhausted. Keep the existing byte bound and one-frame-per-connection rule.

Test both a silent partial frame and bytes trickled faster than the inactivity interval. The latter distinguishes an absolute deadline from a resettable socket timeout.

## Bounded independent connections

Use a small fixed application admission bound, not only a kernel backlog. A thread pool with an unbounded submission queue does not satisfy bounded concurrency and can make shutdown wait indefinitely. A minimal synchronous-code design is:

- one daemon worker thread per admitted connection;
- a `BoundedSemaphore` as the actual admission limit;
- lock-protected sets of active sockets and worker threads;
- immediate close of an accepted connection when no slot is available;
- explicit `listen(limit)` as a backlog hint, not the proof of boundedness.

Share only thread-safe process state. Before recommending concurrency, inspect duplicate-request registries, database connection ownership, native adapters, and handler-side global mutation.

Public tests should prove: one partial client does not block health; all slots can be occupied without admitting another worker; excess connections close promptly; a released slot becomes usable again. Also test continuous slot reacquisition by one UID: a one-second timeout does not prevent a client from sustaining denial of service by reconnecting.

## Pre-authentication state and response identity

Trace which state is allocated before peer authorization. A process-local duplicate-request set that records every decoded unique ID before authorization is an unbounded memory-exhaustion primitive even when concurrent connections are capped; sequential unauthorized requests can grow it forever. Prefer durable operation/journal deduplication, or a strictly bounded TTL/LRU, and do not permanently retain an ID merely because framing and schema decoding succeeded.

Clients must authenticate the server as well as servers authenticating clients. Pathname access alone does not establish response integrity when a writable parent permits rename/unlink/rebind. For security-sensitive clients, verify connected-server `SO_PEERCRED` against the configured service identity and provision the socket in a non-group/world-writable runtime directory. Include tests for fabricated reads, replacement sockets, and exact-inode cleanup.

## Safe parent and stale-socket recovery

The server should not act as a deployment installer. Prefer a pre-provisioned socket parent and validate it before binding:

- `lstat()` identifies a real directory, not a symlink;
- the path does not resolve through unexpected symlink redirection;
- owner is the service effective UID;
- group/other write bits are absent unless a stronger directory policy is explicitly proven.

For an existing socket pathname:

1. inspect with `lstat()` so symlinks are not followed;
2. reject and preserve non-sockets;
3. reject and preserve sockets not owned by the service effective UID;
4. probe an owned socket—successful connection means active/in use, while the platform-specific stale result (normally `ECONNREFUSED`) permits recovery;
5. immediately re-`lstat()` and require the same type, UID, device, and inode before unlinking.

After binding, capture the created socket's identity. Cleanup must unlink only if the current pathname still has that exact identity. This prevents an old server from deleting a successor socket after the live pathname was removed and rebound.

Do not weaken ownership checks merely because a portable unprivileged test cannot create a foreign-owned socket. Put that real-process case in a root-capable installer/system test job; do not mock `stat`, skip the case silently, or add a caller-controlled production UID override solely as a test seam.

## Bounded stop and daemon composition

On stop:

1. stop accepting;
2. close the listener;
3. close or shut down every active connection to interrupt partial reads/writes;
4. join workers against one absolute drain deadline, not one full timeout per worker;
5. remove only the exact socket created by this listener;
6. surface a drain failure to the foreground daemon.

A caller-side `thread.join(10)` followed by an exception is not sufficient if the server thread remains alive or the socket remains. Also inspect whether server-thread startup and runtime exceptions are propagated; new parent/socket checks should fail promptly rather than being hidden behind a readiness timeout.

Thread cancellation cannot safely interrupt arbitrary Python handler code. State the accepted contract precisely: transport drain can be bounded by closing connections, while arbitrary in-flight handler cancellation requires cooperative handler deadlines or process-level termination. Do not claim stronger cleanup than the architecture provides.

## Exact focused tests

Recommended real-behavior tests:

- `test_partial_frame_has_absolute_deadline`
- `test_partial_client_does_not_block_independent_health_connection`
- `test_connection_limit_closes_excess_connection_promptly`
- `test_stop_closes_partial_connections_and_returns_within_drain_bound`
- `test_owned_stale_socket_is_reclaimed_and_serves_health`
- `test_active_socket_is_preserved_and_reported_in_use`
- `test_non_socket_and_symlink_paths_are_rejected_without_removal`
- `test_unsafe_socket_parent_is_rejected_before_bind`
- `test_shutdown_does_not_unlink_replacement_socket`
- `test_foreign_owned_stale_socket_is_never_removed` (root-capable real-process job)
- `test_foreground_daemon_stops_with_partial_client_within_bound`
- `test_foreground_daemon_reports_listener_startup_failure_promptly`

For repositories with strict physical-line limits, add a focused hardening test module instead of overfilling an existing integration file.

## Read-only reporting

For no-test audits, say explicitly that source/test evidence was inspected but no test result was observed. Freeze the commit to a literal SHA, use exact-object reads, and recheck status at the end. If concurrent RED work appears during the audit, report it as excluded drift and do not let it alter the committed-HEAD verdict.
