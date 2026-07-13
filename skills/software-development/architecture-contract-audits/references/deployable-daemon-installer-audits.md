# Deployable daemon and installer audits

Use this when a phase claims a service, launcher, installer, dashboard, backup, or notification surface is implemented.

## Public-operability trace

Do not equate a library with a deployed service. Trace, in order:

1. package script or executable entrypoint;
2. strict production configuration and secret-file loader;
3. runtime constructor selecting exact policy, authority database, sidecar, identities, and clocks;
4. foreground process lifecycle, readiness, health, signals, and clean shutdown;
5. socket ownership, parent-directory safety, stale-socket recovery, and client admission;
6. launcher subprocess enrollment, supervision, signal forwarding, wait/reap, and reconciliation;
7. installer/service artifacts establishing users, groups, paths, modes, hardening, ordering, rollback, and upgrades;
8. at least one installed/public consumer that reaches the service without direct database fallback.

A fixture-built runtime plus `serve(path, runtime, stop)` is partial even if socket integration tests pass. A worker CLI is not an enrolled launcher when only an in-process test or library caller establishes its principal.

## Daemon availability checks

Inspect the accepted-connection path, not only listener setup. A serial server that calls blocking `recv()` without a per-connection deadline can be wedged by one local client sending a partial frame. Require:

- bounded frame size and read deadline;
- bounded concurrency or another design that prevents head-of-line blocking;
- slow-client, truncated-frame, reset, and oversized-frame tests;
- SIGTERM/SIGINT behavior and bounded shutdown;
- crash/restart behavior when the socket path remains;
- safe ownership/type checks before removing a stale socket.

Socket mode alone is insufficient. Verify the installer establishes the parent runtime directory, owner, group, umask/ACL posture, and client group independently from authority-database ownership.

## Installer and privilege-separation checks

A packaging script entry is not an installer. Inventory exact tracked artifacts for service units, socket/timer units, sysusers/tmpfiles or equivalent, config templates, migration/upgrade logic, verification, and rollback. Also trace the public install/render entrypoint and wheel/sdist inclusion: an importable renderer with no CLI/callsite, no account provisioning, and no packaged service/tmpfiles/config payload remains an inert library artifact, not a clean-host deployment path.

Require distinct OS access boundaries when launchers or workers must not open authority or sidecar databases. Mode `0600` does not isolate processes sharing the broker UID. Installer tests should operate on temporary roots first; live installation, privileged path creation, service restart, profile rollout, and cutover remain separate approval gates. If the service unit grants registrar/operator supplementary groups, inspect every descendant `Popen`: absent `extra_groups=()` or an explicit identity drop, launchers and workers inherit those groups and DAC separation is not independent. Require a numeric service-UID invariant against operator identities or deterministic sysusers provisioning that establishes it.

Cross-check rendered `Group=`, `SupplementaryGroups=`, sysusers memberships, and kernel-derived `/proc/<pid>/status` groups against every exact runtime authorization tuple. A service can deny its own rendered identity when the unit adds a client/control group but runtime assembly expects only the primary GID; fixture runtimes copied from the test process do not prove the rendered account. Reject sysusers plans that create a new named group at an existing operator primary GID unless the existing group name is proven identical or an explicit membership migration is supplied.

Trace readiness through its installed consumer closure. If `Type=notify` depends on a plugin callback after an `exec`, the exact authenticated bundle and wheel/profile plan must include that plugin, enablement and override grants, and make its imports available in the worker interpreter. Tests that manually `copytree` the plugin and inject source roots through `PYTHONPATH` are development proofs, not package/install proofs. Also search the executed worker environment for native mode markers that activate hidden direct-database lifecycle paths outside overridden tools; either omit them or provision and reconcile the exact compatibility snapshot they require.

Audit sandbox grants against rendered production paths, not only synthetic temporary secrets. Broad runtime allowances such as all of `/etc` can override an otherwise correct protected-path list and expose a `0600` broker key when workers inherit the broker UID. Run a harmless real-sandbox probe against a representative file in each broadly granted root, then cross-check whether config, keys, sockets, package data, or authority state can live below that root.

Exercise every create-then-open boundary under real resource exhaustion. If `mkdirat` succeeds and the following `openat` fails, outer cleanup flags set only after the helper returns cannot remove the new directory. Use a forked `RLIMIT_NOFILE` probe (or equivalent real descriptor exhaustion), assert both the expected failure and destination absence, and keep cleanup descriptor-bound.

## Migration ledger integrity

Before applying any migration, require the persisted version ledger to equal an exact contiguous prefix of the compiled migration sequence. Computing only `MAX(version)` can skip a missing earlier migration, commit later migrations, and then fail a post-commit current-schema check, leaving a mutated database that cannot self-repair. Validate the prefix inside the same transaction before the first DDL/DML statement; reject holes, duplicates, unknown/future versions, reordered entries, and schema/version disagreement without mutation. Test a real malformed ledger such as `(1, 3)` and prove byte/row/schema stability after rejection.

Trace the deployed startup command, not only the daemon constructor. A daemon that rejects stale schema can still lose fail-closed startup semantics when its systemd unit runs an unconditional `ExecStartPre=... migrate` before the check. Classify explicit operator migration separately from service startup; require malformed-ledger rejection before any migration DDL/DML and keep migration expectations hard-coded rather than derived from the production migration collection.

## Consumer and cutover checks

Treat these separately:

- parser compatibility snapshots versus a broker-backed CLI shim;
- protocol read operations versus a dashboard application/adapter;
- notification subscription/cursor storage versus a delivery consumer;
- snapshot manager primitives versus production snapshot creation and cleanup;
- backup/restore libraries versus an operator command and fail-closed service workflow.

For CLI cutover, require an exhaustive parser-path equation and subprocess tests proving no native fallback. For dashboards and notifiers, search production callsites for the broker client and separately search for direct database access.

## Backup offline-fence checks

Socket-path absence alone does not prove the daemon is stopped: a live socket can be unlinked while the process continues, and child processes may still hold authority. Require a service-level quiescence contract such as an exclusive daemon/backup lock plus verified child shutdown and service ordering. Test the adversarial case where the live socket pathname is removed before backup starts.

## Evidence boundary under concurrent RED work

Recheck HEAD and full untracked status repeatedly. If a test appears first and its source appears later, classify both as concurrent in-flight work and keep conclusions pinned to the original commit object. Use `git show`, `git grep <commit>`, and `git ls-tree <commit>` for absence/callsite claims. Report the untracked slice separately; do not let it silently weaken an exact-HEAD finding.

## Focused proof inventory

Recommended public tests:

- daemon executable starts from a real config and serves health;
- malformed config, permissive secret mode, unknown fields, or unprovisioned identity fail before socket readiness;
- slow client cannot block an independent health request;
- SIGTERM cleans up the socket and launcher without orphaning workers;
- crash restart handles a stale socket safely;
- installer dry-run and idempotent reinstall produce exact owners/modes/unit content;
- launcher is denied before broker enrollment and succeeds only after gated enrollment;
- every native CLI parser path maps to broker behavior or an explicit exclusion;
- dashboard/notifier public processes use the broker and cannot open authority databases;
- backup refuses a still-live daemon even if the socket pathname was unlinked.
