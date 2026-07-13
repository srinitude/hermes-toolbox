# Pre-cutover validation and shadow-mode audits

Use this when a staged rollout separates comprehensive repository validation from later shadow activation, privileged installation, and enforcement cutover.

## Evidence boundary

Freeze the repository HEAD, dirty overlay, pinned upstream SHA, and both initial/final statuses. In a no-write review, use AST/static probes with bytecode disabled and distinguish tests present from tests executed. Do not turn a green full suite into evidence for absent adversarial, packaging, installed-wheel, shadow, or cutover contracts.

## Comprehensive validation packets

Require independently runnable, cache-free packets rather than one undifferentiated full-suite claim:

1. pinned native callable, model-tool, public-protocol, CLI-parser, and dashboard-route equations;
2. protocol bounds, storage migrations, capabilities, approvals, audit, journal recovery, and cross-store finalization;
3. native parity, late-failure recovery, exact replay, and unrelated-board concurrency;
4. workflow policy, selector ambiguity, cross-board/profile denial, and lifecycle invariants;
5. public broker/client/daemon/plugin/operator/launcher/worker process paths;
6. backup, restore, installer, and package behavior;
7. a dedicated adversarial package and an installed-wheel package.

The adversarial package should prove no native fallback, zero mutation for replayed/expired/altered/cross-scope authority, model-versus-human separation, capability scope, slow/partial/reset/oversized connection isolation, same-UID sibling denial, genuine controlling-foreground-TTY confirmation, secret absence across argv/environment/FDs/logs/databases, post-commit recovery without authority replay, and independent-board progress.

## Packaging acceptance

A source checkout and packaging metadata are not installed-wheel proof. Build into a disposable output and verify, from outside the source tree:

- exact console entrypoints and metadata;
- all immutable contract data required by runtime loaders;
- explicit treatment of policies, schemas, service templates, and other external deployment inputs;
- source-versus-packaged contract hash equality;
- no tests, caches, bytecode, private paths, secrets, runtime databases, or unreviewed artifacts;
- entrypoint startup and pure config/contract loading without repository fallback.

An inert renderer containing only a service unit and config is not an install bundle if production also requires a wheel/executable, policies, keys, socket units, user launcher, ownership/ACL setup, or rollback metadata.

## Detect fake shadow mode

Trace mode handling through runtime construction, policy evaluation, request dispatch, dispatcher gates, journaling, and native calls. If startup accepts `shadow` but mutation/policy paths require exact `enforce`, shadow is quarantine—not shadow behavior.

Real shadow mode must:

- preserve the selected pre-cutover native authority and dispatcher;
- evaluate the exact pinned policy against a read-only snapshot or online backup;
- never reserve/consume approvals, issue capabilities, dispatch, mutate authority, mirror terminal state, or block native behavior;
- durably append idempotent decisions keyed by request fingerprint;
- record policy ID/version, operation, actor class, canonical scope digest, would-allow, decision code, observed native outcome, exact native post-state digest, comparator/schema version, timestamp, and mismatch classification;
- omit credentials, plaintext approvals/capabilities, claim locks, and unbounded bodies.

Shadow exit needs a measured window (normally at least two full dispatcher intervals), complete observation coverage, zero unexplained mismatch, an audit/decision-chain checkpoint, and a separate approval for enforce. Shadow approval never authorizes ownership, ACL, database promotion, native-writer disablement, or enforce mode.

## Inert cutover/rollback envelope

Prefer exact top-level sections `version`, `install_state`, `approval_boundaries`, `rollout`, `rollback`, and `drift`. Keep private profiles, board IDs, UID/GID values, and host paths in an environment-specific external instance of the same schema.

Require:

- clean release/upstream SHAs, wheel/install-bundle/package-data hashes;
- identities plus every socket/database/key/config/policy/log/backup/runtime path with owner/group/mode/ACL;
- consumer/plugin/override/dispatcher/CLI/notifier/dashboard HTTP+WebSocket state;
- policy and Project-binding hashes/modes;
- authenticated backup inventory, service-level quiescence/generation lock, fresh-staging restore drill, and exact future live targets;
- fixed rollout step IDs with mutation/verification class, approval, preconditions, expected state, verification, blocker, and one unique inverse;
- rollback beginning with consumer freeze, worker/launcher reap, broker stop, and exclusive restore lock, followed by exact config/plugin/dashboard/service/database/owner/mode/ACL restoration;
- drift pins for native contracts, operation ledger, parser, dashboard routes, plugin tool set, service/config, and installed artifacts.

## Privileged probes remain later gates

Defer service user/group creation, root-owned installation, chown/ACL changes, systemd reload/start/stop/restart, profile or gateway mutation, CLI wrapper replacement, authority migration, live backup/restore, dashboard route cutover, and enforcement activation. Later privileged acceptance must prove distinct broker/registrar/operator/launcher/worker/dashboard identities; exact socket-group access; denial of authority/key/control paths to non-broker identities; process-tree/FD/environment separation; direct native/SQLite bypass denial; live HTTP and WebSocket posture; and deterministic rollback.

## High-value implementation traps

- A broker-spawned launcher with no credential drop shares broker database authority.
- `chmod 0660` without explicit socket group ownership does not implement a registrar boundary.
- `ReadWritePaths` granting launcher/workspace locations to the broker can collapse intended separation.
- `stdin.isatty()` does not prove a genuine controlling foreground terminal.
- Generic operation/JSON RPC is not native CLI parser/flag parity.
- A dashboard operation ledger is not route disablement; inventory every pinned HTTP method and WebSocket route.
- Socket-path absence is not backup quiescence; unlinking a live socket bypasses it.
- Fresh-staging restore is not live exact-target rollback.
- Subscription/cursor storage is not notification delivery.
