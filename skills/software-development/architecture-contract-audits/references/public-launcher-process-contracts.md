# Public launcher process contracts

Use this reference when a broker implements launch checkout/start/failure protocol but the audit must determine whether a real launcher and worker consumer are operable.

## Public-path proof

Do not infer launcher integration from broker handlers or lifecycle unit tests. Trace all of these:

1. an installed CLI/service entry point constructs the launcher;
2. production runtime assembly provisions the launcher principal from the real process PID and start time;
3. the launcher checks out a lease through the public transport;
4. it creates the worker as its direct child without a shell intermediary;
5. it sends `launch.started` or `launch.failed` through the public client;
6. the worker actually consumes the minted capability and routes eligible tools through the broker;
7. the launcher waits/reaps and handles signals/orphans; and
8. unexpected post-start exit terminalizes or reconciles the running lease so later dispatch is possible.

A test process manually sending launch frames for a synthetic child proves broker protocol behavior, not a public launcher. A compatibility equation between worker-visible tools and capability operations proves scope selection, not consumer cutover; inspect the pinned tool handlers to determine whether they still write native state directly.

## Process contract

Record the exact contract rather than accepting an unspecified `Popen` call:

- fixed bounded argv and direct-child relationship;
- allowlisted environment, with ambient credentials excluded;
- bootstrap capability absent from argv, environment, `/proc`, stdout, stderr, and logs;
- explicit stdin ownership and closure semantics;
- explicit stdout/stderr destinations, permissions, and bounds/rotation;
- process-group/session policy;
- wait/reap behavior and exit classification;
- SIGTERM/SIGINT forwarding, escalation, and launcher-death behavior;
- no orphan that can retain authority after the launcher exits.

Holding a pidfd prevents PID reuse but does not prove the child remained alive throughout handoff. Poll before native acceptance and again at the chosen acceptance boundary, then provide deterministic post-start death reconciliation.

## Exactly-once failure acknowledgement

Before reserving or applying native failure, require the sidecar lease to be `launching` and bound to the authenticated launcher PID. A different request ID must not claim an already-failed lease. If lease transition and journal completion share one sidecar transaction, a generic `state='failed'` recovery branch is usually unnecessary and can admit duplicate successful acknowledgements.

Focused public test:

- complete one `launch.failed` request;
- resend the same lease and reason under a new request ID;
- require denial before a new journal reservation;
- assert one native terminal event, one failure-counter increment, and one successful acknowledgement/audit.

## Running-lease reconciliation

Audit open-lease selection carefully. If the dispatcher reconciles only `pending`/`launching` expiry and otherwise returns the first open lease, a dead or expired `running` lease wedges dispatch forever. Worker-initiated complete/block/heartbeat reconciliation is insufficient because a dead worker cannot initiate it.

Required real-process tests include:

- exit during start handoff;
- clean and nonzero post-start exit;
- SIGTERM followed by bounded escalation;
- launcher exit without worker orphaning;
- capability expiry after missed heartbeat;
- next dispatch after every terminal/death case;
- token absence from argv, environment, `/proc`, and log bytes.

## Evidence-boundary pitfall

Concurrent drift can appear after an initially clean status. Recheck status at the end. If a pinned dependency checkout is not at the pinned revision, inspect exact Git objects and explicitly separate current-checkout drift from pinned-source conclusions. Never cite a worktree read after drift as exact-commit evidence unless it is verified unchanged from the commit object.
