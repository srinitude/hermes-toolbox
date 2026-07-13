# Inert Rollout, Rollback, and Drift Contracts

Use this when a pre-deployment phase must produce repository-local rollout artifacts without authorizing installation, service changes, profile edits, live backup/restore, or cutover.

## Smallest complete shape

Prefer one canonical machine-readable envelope over three independently drifting plan files:

- `data/deployment-posture-v1.json`
- one strict loader/validator module;
- one focused test module;
- one packaging entry for the JSON.

The envelope should have exact top-level sections: `version`, `install_state`, `approval_boundaries`, `rollout`, `rollback`, and `drift`. Keep it inert: it describes and validates actions but exposes no execution surface or deployment CLI.

## Required cross-surface distinctions

Record current capability honestly:

- an authenticated unit/config renderer is an inert install bundle, not an installer;
- socket-path absence is not service quiescence;
- database restoration to a fresh directory is not live exact-target restore;
- exact plugin override source is not profile installation or override authorization;
- a dashboard operation-intent ledger is not native HTTP/WebSocket route disablement or replacement-consumer parity;
- a pinned upstream contract is not proof that the currently selected checkout is at that commit;
- a dirty in-flight phase must not be frozen as release provenance.

## Schema invariants

### Approval boundaries

Represent at least:

- repository-local validation phase;
- separately approved live/privileged rollout phase;
- separately approved publication phase;
- an exhaustive set of actions forbidden in the inert phase.

No mutating rollout step may be assigned to the repository-local phase.

### Rollout

Use fixed ordered step IDs. Classify verification separately from mutation. Every mutating step must name its approval gate and rollback inverse. Record blockers rather than converting missing implementation into optimistic prose.

Typical blockers include absent service-level quiescence, incomplete non-database backup inventory, missing dashboard route-disable proof, missing replacement consumer/process identity, absent sole-writer OS fencing, and an unpinned final release commit.

### Rollback

Require:

- consumer freeze before service/database changes;
- broker and child-process shutdown;
- profile/plugin/dashboard configuration restoration;
- verified fresh-staging database restore before exact-target promotion;
- service file, owner/group/mode/ACL restoration;
- baseline restart and drift verification;
- a bijection from rollout mutations to rollback inverses.

List secret references, never secret bytes. Describe current restore support exactly; if only fresh-staging restore exists, set live restore to unsupported and gate it.

### Drift

Pin external source commit/version and deterministic source hashes where stable. For the repository being changed, require a clean exact commit at live approval time rather than creating a self-referential tracked manifest. Validate packaged contract hashes and exact plugin tool sets.

For dashboards, inventory the pinned native backend by HTTP method and WebSocket route. Keep route counts/hashes separate from broker operation counts: operation coverage is not route coverage.

## Validator design

The inert validator should:

- reject unknown top-level and nested fields;
- bound file size, strings, and collections;
- reject symlinks;
- enforce exact step ordering, enums, uniqueness, and approval classes;
- prove mutation-step/rollback-inverse equations;
- cross-check installer, backup, daemon-config, plugin, dashboard-posture, and pinned-contract metadata through existing pure loaders;
- reject any claim of live install, live restore, installed plugin, dashboard replacement, or sole-writer cutover when proof is absent;
- contain no subprocess, network, service-control, copy/install, chmod/chown, profile mutation, or runtime mutation surface.

## Authenticated bundle snapshot safety

Do not treat a signed manifest plus pathname re-hashing as a stable authenticated installation input. Audit the producer and verifier together:

- writes must loop until all bytes are written and surface short writes; otherwise the renderer can sign a truncated unit/config as valid;
- verification should open a trusted directory once, reject unsafe ownership/mode, and inspect entries through descriptor-relative no-follow operations;
- authenticate one coherent file set, not each pathname at unrelated instants while a bundle owner can swap entries;
- return descriptor-bound or immutably copied artifacts for later privileged consumption, not mutable paths whose contents can change immediately after verification;
- if the current slice is intentionally inert and has no privileged consumer, report that honestly, but still block claims that the returned paths are safe authenticated install inputs.

Required adversarial proofs include a forced short write, manifest/file replacement during verification, replacement after verification but before consumption, symlink substitution, and a privileged verifier examining an unprivileged-owner bundle.

## Focused test inventory

Use exact public tests covering:

1. inert state and live-phase gating;
2. complete cross-surface inventory;
3. rollout-mutation/rollback-inverse equality;
4. no overclaim of quiescence or live restore;
5. exact native plugin override set;
6. dashboard posture explicitly not treated as route parity;
7. exact upstream pins and packaged hashes;
8. unknown fields, duplicates, and reordered-step rejection;
9. static absence of execution surfaces;
10. packaged-wheel loading.

During a no-write review, do not run test tools that may create caches. Report source tests as present/unexecuted and use immutable Git-object inspection for committed claims.

## Approval packet for the later live phase

Require the later approval to name exact values for:

- clean release commit and upstream source commit;
- install-bundle manifest/authenticator;
- service identity, paths, sockets, databases, and ownership/modes;
- quiescence mechanism and authenticated backup ID;
- target profiles and override-trust changes;
- native dashboard disablement, including WebSockets;
- replacement dashboard identity and socket access;
- shadow/enforce and sole-writer transitions;
- restart commands, acceptance checks, rollback trigger, and exact restore targets.

Publication remains independent even when live rollout is approved.

## Exact minimal-envelope design discipline

When the deliverable is a design rather than an implementation, still make it directly implementable:

- name the exact four-file change set: one packaged JSON envelope, one read-only loader/validator, one focused test module, and one packaging entry;
- give exact key sets for every object, fixed ordered step IDs, enums, bounds, and the mutation-to-inverse rollback equation rather than saying only “use a strict schema”;
- put desired UID/GID values in the later environment-specific live manifest; reusable tracked data should name identity and group roles, ownership relationships, modes, and directories without private numeric IDs or profile names;
- distinguish current capability fields from desired rollout posture. If backup is database-only, restore is fresh-target-only, installation is bundle rendering, or dashboard route disablement is unproved, encode those exact inert states and block stronger claims;
- classify target-changing rollout actions as `mutation`, backup/locks as `safeguard`, checks as `verification`, and human decisions as `approval`. Require exactly one rollback inverse for each mutation, but do not invent destructive “inverses” for retained safety backups;
- keep rollback order operationally safe: freeze consumers, stop children, stop broker, acquire an exclusive restore lock, unwind policy/consumer/native-route changes, verify databases in fresh staging, promote exact targets, restore code/config/metadata, restart the baseline, then verify drift and unfreeze;
- state the source/test evidence actually inspected and whether tests ran. For a no-write task, compare initial and final repository status and explicitly separate pre-existing dirty files from agent writes.

A stored `shadow` mode is not shadow evaluation. Trace request and dispatcher gates: if they require exact `enforce`, describe the current state as quarantine and require durable would-allow/would-deny evidence before shadow approval.

## Phase-8 shadow and cutover prerequisites

Keep shadow behavior and cutover validation as distinct contracts:

1. Shadow must evaluate the exact policy and durably record would-allow/would-deny while preserving the selected pre-cutover authoritative behavior. A stored mode string is not shadow behavior. If runtime construction accepts `shadow` but request, control, or worker-dispatch gates require exact `enforce`, the implementation is quarantine, not shadow.
2. Cutover validation remains inert. Track a strict schema and loader, but keep an environment-specific manifest outside a reusable repository when it contains private profiles, boards, UID/GID values, or paths. Do not add an execution CLI.
3. Require separate approvals for live shadow activation and later enforcement. Shadow approval never authorizes ownership/ACL changes, native-writer disablement, database promotion, or `enforce` mode.
4. Bind the cutover manifest to the clean release commit, wheel/install-bundle hashes, pinned upstream contract and ledger, identities and filesystem metadata, consumer/plugin state, dashboard HTTP and WebSocket posture, authenticated backup and restore drill, shadow thresholds, rollout/rollback step IDs, and drift checks. Store secret references only.
5. Give every rollout mutation one unique inverse rollback step. Rollback begins with consumer freeze, launcher/worker reap, broker stop, and an exclusive restore/generation lock before inverses are applied.

For measurable shadow acceptance, prefer a dedicated append-only, idempotent decision table keyed by request fingerprint over inferring metrics from generic audit prose. Record policy id/version, operation, actor class, would-allow, decision code, observed native outcome, digest, and timestamp; never record credentials or approval plaintext.

## OS-isolation audit traps

Check the actual process creator and UID, not only logical principal names:

- If the broker directly spawns and enrolls the launcher while requiring `launcher.uid == os.getuid()`, launcher and workers share the database-owner UID. This blocks sole-writer cutover.
- Two Unix sockets created by one service with `0660` inherit the same effective GID unless socket activation or explicit ownership handling assigns different groups. Separate parent directories alone do not create separate public-client and private-registrar group boundaries.
- A `UMask=0077` service that dynamically creates its socket parent can make a nominally `0660` client socket unreachable. Require pre-provisioned runtime directories or exact post-bind ownership/group handling.
- A long-lived dashboard needs a distinct read-only principal selected from kernel peer identity. One fixed PID-bound human principal cannot simultaneously authenticate a short-lived operator CLI and a separate dashboard process.

The minimum strong model normally separates broker/database owner, launcher/workers, human operator, registrar, and dashboard identities; uses distinct client and registrar groups; makes trusted code root-owned and immutable; and denies non-broker identities authority-directory traversal.

## Cross-surface blocker detection

Treat these as cutover blockers, not documentation gaps:

- quiescence proven only by socket-path absence, especially when unlinking a live socket bypasses the check;
- backup manifests that cover databases but omit service/config/plugin/ACL metadata;
- source-copy or `PYTHONPATH` plugin tests presented as installed-wheel proof;
- process-local locks presented as cross-process sole-writer fencing;
- dashboard operation-ledger coverage presented as native route parity;
- an uncommitted or dirty candidate selected as release provenance.
