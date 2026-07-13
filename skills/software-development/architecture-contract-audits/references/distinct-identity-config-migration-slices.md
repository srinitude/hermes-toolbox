# Distinct-identity config and migration slices

Use when a same-UID broker directly spawns a launcher that directly spawns workers, and the requested next slice is the smallest coherent move toward fixed broker/launcher/worker-slot identities.

## Do not accept config-only false security

Adding broker, launcher, and worker UID/GID fields is not an identity boundary while production still reaches same-UID `Popen`, caller-supplied worker PIDs, bare-PID/process-group termination, or a one-user service bundle. A coherent slice must either replace those paths or make production startup fail closed until the replacement exists.

A runtime test that merely asserts config values were copied into a dataclass is tautological. Require the running broker EUID/EGID, launcher socket peer, worker socket peer, exact unit, and invocation to match independent configured expectations.

## Smallest fixed-slot state model

For one literal slot such as `worker0`:

- keep broker, launcher, and worker primary UIDs and GIDs pairwise distinct;
- keep unit and slot names server constants, never request arguments;
- enroll the separately managed launcher from `SO_PEERCRED`, pidfd-coherent process reads, and exact unit/invocation evidence;
- have the worker register itself; remove launcher-supplied `worker_pid` from the public start contract;
- let only the broker start, inspect, and stop the literal worker unit;
- bind capabilities to lease, slot, unit, invocation, PID/start, UID/GID/groups, and task/run scope;
- serialize slot reuse until the prior cgroup is empty and credentials are gone.

Launcher enrollment should accept no caller-controlled identity fields. A live or ambiguously inspectable binding cannot be replaced; a verified-dead binding may be CAS-rebound.

## Migration shape

Prefer an additive migration with nullable columns for existing rows, for example service unit/invocation/slot on principals and separate launcher PID, worker PID, slot, worker unit, and worker invocation on launch leases. Add a partial unique index preventing two nonterminal leases from owning the fixed slot.

Do not backfill guessed unit/invocation identity, delete open leases, clear native claims, or reinterpret an overloaded legacy PID silently. Terminal legacy rows may remain nullable. Legacy `launching`, `running`, or `terminating` rows without exact identity must block readiness for explicit reconciliation.

Keep these versions independent:

- daemon/config schema;
- inert install-bundle manifest;
- SQLite migration sequence.

Startup remains read-only and rejects stale schema; only an explicit migration command mutates the database.

## Full-surface regression inventory

A config version bump usually also affects:

- daemon config fixtures and version-oracle tests;
- runtime assembly and authority-file ownership checks;
- installer config rendering, manifest verification, unit rendering, and bundle dataclasses;
- launcher enrollment and authorization;
- worker registration, capability authorization, exit, orphan, and startup reconciliation;
- protocol operation registry and strict argument schema;
- test helpers that pre-seed same-process principals.

Search specifically for single `service_user` models, bundle version literals, `os.getuid()` used as launcher or server identity, `Popen`, `killpg`, parent-PID checks, and request parsing of `worker_pid`.

## Vertical RED to GREEN order

1. Config parsing, complete collision matrix, and real broker-process identity.
2. Additive migration, rollback, legacy-row preservation, slot uniqueness, and stale-schema refusal.
3. Argument-free launcher enrollment with real peer/unit identity and binding replacement rules.
4. Worker-direct registration with no caller PID and replay to one capability/native start.
5. Broker-only literal-unit start/inspect/stop; remove all old production spawn/kill callers.
6. Restart and legacy-open reconciliation, invocation mismatch quarantine, and slot reuse.
7. Inert three-identity bundle rendering and verification; leave installation/cutover behind a separate approval gate.

Under strict no-mock repository contracts, systemd unit/invocation and cross-UID acceptance requires a root-capable isolated real-service job. Ordinary in-process tests may prove parsing and storage but must not be presented as OS-isolation proof.

## Active-worktree audit discipline

When a parent writer is editing during a read-only design audit, capture the literal HEAD plus staged and unstaged digests more than once. If they drift, report findings as live semantic guidance rather than an exact-candidate seal. Re-read any file whose content changed before citing line-specific defects, and avoid attributing transient half-written syntax or constructor mismatches as durable design findings.
