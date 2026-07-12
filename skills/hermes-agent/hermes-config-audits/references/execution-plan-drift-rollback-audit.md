# Read-only execution-plan drift, rollback, automation, and gate audit

Use this procedure when deciding whether a saved implementation plan may proceed against an existing rollback/evidence directory. The deliverable is an execution gate decision, not implementation.

## Strict boundary

- Do not edit target files, trigger cron, restart services, mutate policy, contact remote machines, or inspect credential stores.
- Prefer in-memory hashing (`subprocess.check_output` + `hashlib`) over `mktemp`, redirects, or generated audit files. A strict read-only audit should not create even short-lived probe files.
- Avoid `session_search` unless historical conversation context is essential: oversized results can spool under `/tmp/hermes-results/`. If any managed tool creates a cache/spool artifact, disclose its exact path and whether it remains.
- Query local daemons and local service managers only when that does not initiate remote probes. Mark externally hosted state (for example, current paid sandbox inventory or remote publication effects) **not revalidated** rather than inferring it from stale evidence.

## Baseline sequence

1. Hash the saved plan and identify which plan hash each evidence artifact references. Historical artifacts for an earlier plan remain evidence but cannot certify the current plan.
2. Inventory the rollback directory: file count, modes, hashes, JSON validity, and the precise planned artifacts that are absent.
3. Recompute protected repository `HEAD` and the SHA-256 of exact `git status --porcelain=v1` bytes. Do not inspect, stage, reset, or revert protected drift unless separately authorized.
4. Enumerate cron state through native read surfaces and the backing job metadata where needed. Record `enabled`, `state`, `paused_at`, `last_run_at`, and `last_status` separately.
5. Check for independent watcher processes, systemd path units, and timers. A paused cron job does not prove there is no second automation path.
6. Inspect local service state, unit hashes, listeners, and checksum-guarded rollback targets.
7. Compare current artifacts to the plan's allowed-write list and approval gates. Return exact paths and phase ordering.
8. Re-read volatile files and recompute repository/service baselines immediately before reporting. Concurrent actors may update approval ledgers or pause automation during the audit.

## Drift classifications

Keep these categories distinct:

- `UNCHANGED`: current digest matches the captured baseline.
- `PREEXISTING_DIRT_PRESERVED`: dirty state is byte-identical to baseline.
- `CONCURRENT_EXTERNAL_DRIFT`: HEAD/status changed outside the audited execution; preserve it and recapture before mutation.
- `EXPECTED_SUPERSESSION`: a newer plan intentionally replaces an older plan, but old evidence is historical only.
- `CURRENTLY_SAFE_WITH_INTERVENING_ACTIVITY`: automation is paused now but ran after an earlier audit claimed it was paused. Report both present state and intervening history.
- `NOT_REVALIDATED`: proof requires a forbidden remote call or human action.
- `STALE_OR_NON_AUTHORITATIVE`: a logical rollback template or rejected candidate is not an exact active prestate.

Never infer causation merely because a repository advanced near a successful publisher run. State temporal correlation and leave attribution unknown unless direct evidence exists.

## Pre-mutation gate model

Report gates in dependency order:

1. current first-party contracts and cost;
2. exact active prestate export, restrictive mode, and hash;
3. complete human/admin inventory, including offline/shared/tagged exceptions;
4. merged candidate and semantic diff;
5. negative/positive policy tests with RED then GREEN evidence;
6. fresh local and approved-client baseline matrix;
7. explicit approval naming the exact candidate hash;
8. human policy save and immediate preservation checks;
9. zero-resource and paid-action preflight;
10. human-bound authentication and visual acceptance;
11. exact cleanup and zero-residue proof;
12. independent privileged rollback gates kept separate from the main task.

Broad approval to execute a plan is not approval of an unreviewed policy hash, paid resource, gateway restart, publication, or privileged command.

## JSON reporting contract

When JSON is requested, return one valid JSON document with:

- audit timestamp, mode, and overall classification;
- saved-plan integrity;
- rollback/evidence inventory and authority drift;
- protected repository baselines and classifications;
- cron, watcher, and publication state;
- service/network baselines;
- required pre-mutation artifacts;
- exact allowed writes grouped by phase;
- approval gates and blockers;
- a read-only-boundary disclosure listing target mutations, concurrent external changes, and tool-created cache/spool artifacts.

Use `BLOCKED_FOR_MUTATION` whenever any prerequisite artifact or human gate is missing, even if current services are healthy.
