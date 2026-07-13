# Broker Boundary TDD and Identity Hardening

Use this reference when a saved plan introduces a privileged local broker, Unix-domain transport, operator approvals, scoped worker capabilities, or a sidecar policy store.

## Authority derivation

- Treat request actor fields as non-authoritative metadata. Changing JSON from `model` to `human` or back must never change authorization.
- Derive the caller from `SO_PEERCRED` at the accepted Unix socket and resolve it against a persisted principal or authenticated server/session context.
- UID equality alone is not a human/model boundary when operators, gateways, and workers share an account. Human approval minting needs an explicitly enrolled operator peer/session (for example exact UID+PID for a bounded process lifetime) or separate OS identities. Worker capabilities remain bound to exact UID, PID, profile, board, task, run, claim, operation set, and expiry.
- A PID-bound operator record is fail-closed but ephemeral. Deployment/client work must include safe enrollment, rotation on restart, and denial of stale records; never silently fall back to same-UID trust.
- Persisted operator role is the explicit cross-profile widening mechanism. Ordinary human and worker principals remain profile-local.

## Real Unix-socket acceptance tests

Use real `AF_UNIX` sockets and temporary paths, not socket fakes. Prove all of these at the public boundary:

1. The server reads `SO_PEERCRED`; actor JSON changes do not alter authority.
2. An unregistered or wrong-PID same-UID peer cannot mint human approval.
3. One connection carries one bounded NDJSON request and one compact NDJSON response.
4. A process-wide request registry rejects duplicate IDs before a second dispatch.
5. Malformed UTF-8/JSON, missing newline, multiple frames, and frames over 1 MiB return stable errors.
6. `BrokerError` and unexpected internal failures become safe response objects; no traceback crosses the socket.
7. A client RST/BrokenPipe before response does not kill the accept loop; a subsequent real request succeeds.
8. Shutdown removes only the socket created by that server. An existing path fails closed instead of being unlinked.

## Meaningful RED discipline

A first run can fail because the wished-for API/module does not exist; that is a valid bootstrap RED. After adding scaffolding, rerun until the public behavior itself fails for the intended reason. Test-setup errors such as a missing required native argument do not count as the regression RED: correct the setup, rerun, and record the later `DID NOT RAISE`, wrong result, or unauthorized mutation as the meaningful RED.

## Sidecar schema migrations

When adding authority metadata such as peer PID or binding approval fields:

- add an append-only migration;
- update fresh-open version expectations;
- bump synthetic failed-migration tests to the next unapplied version;
- verify rollback leaves every earlier version and no partial artifact;
- update human/operator fixtures to supply the new security field;
- clear prior approval whenever the exact protected binding changes.

For Project bindings, store explicit approval identity/time and compare the approved record read-only with native `projects.db`. Missing DBs, missing rows, archive state, or ID/name/board mismatches are drift; do not auto-reconcile during mutation.

## Checkpoint and reporting rule

After a security regression reaches focused GREEN, run the relevant suite, full suite, parser-based structure checks, compile/lint, `git diff --check`, protected-boundary drift checks, and commit before opening another behavior family. If the tool ceiling lands after the production patch but before GREEN, report the last verified commit separately and label the current files dirty and unverified. Never attach an earlier full-suite count to the later tree.
