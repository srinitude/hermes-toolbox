# Fast Security-Candidate Execution

Use this pattern for large, security-sensitive candidates with slow real-service suites.

## Objective

Minimize wall-clock time without weakening digest, review, or real-integration gates. The main avoidable cost is starting an hour-scale suite before the candidate and its exhaustive fixtures are complete.

## Fast gated sequence

1. **Freeze scope and appoint one writer.** Run independent security, installer, compatibility, and schema audits read-only and in parallel. Give each auditor the base HEAD, current digest, parent-owned dirty paths, and explicit no-edit/no-suite rules.
2. **Map changed contracts to every constructor and fixture before the long suite.** Search for all direct dataclass/config constructors, `dataclasses.replace` calls, exact field sets, command tuples, migration-version lists, installed-bundle schemas, and clean-environment probes. A closed command grammar or new required field must update every exhaustive fixture before the first authoritative suite.
3. **Use vertical RED → GREEN packets.** Combine tightly coupled behaviors in one focused command after each witnessed RED. Run structure and touched-file lint in parallel with focused tests, but never run tests sharing HOME/profile/socket/database/runtime state concurrently.
4. **Prove the installed consumer before the long suite.** Build a disposable wheel, install it with the exact pinned upstream dependency, render authenticated inert artifacts, and invoke the real loader from outside both source trees. This catches missing package data, arbitrary profile paths, and source-root/import assumptions cheaply.
5. **Run one pre-suite adversarial trace.** Manually follow active, terminal, crash-recovery, and replacement paths across public APIs. In particular, verify that healthy occupied capacity returns the documented busy/idle response while mismatched generations quarantine.
6. **Size the authoritative timeout from evidence.** Use the slowest observed complete suite plus at least 20% margin. Focused-suite duration and early percentage progress are not valid full-suite estimates. If no complete duration exists, choose a conservative bound and preserve a numeric exit artifact.
7. **Do not start the authoritative suite until audits that can alter architecture have returned.** Audits may overlap focused work, wheel preflight, and read-only inspection. They should overlap the final suite only when any late finding will explicitly invalidate that run and the expected wall-clock saving outweighs rerun risk.
8. **Use sparse progress checks.** For a known 30–60 minute suite, check every 5–10 minutes rather than polling every minute. Keep exactly one authoritative process ID. Never run tracker-facing focused tests beside it.
9. **On failure, repair the narrow boundary first.** Read the complete saved log, classify production defect vs stale exhaustive fixture vs load-sensitive race, witness the focused failure, repair once, and stress-repeat only the real flaky boundary. Do not weaken a closed production contract to preserve an obsolete fixture.
10. **Regenerate all digest-bound evidence after any edit.** Recompute candidate digest, rebuild reproducible wheels, rerun installed-artifact proof, and dispatch fresh digest-pinned audits. Prior evidence remains diagnostic only.

## Robust long-suite evidence

- Write to `/tmp/hermes-verify-full-<digest>.log` and `/tmp/hermes-verify-full-<digest>.exit`.
- Use `set -o pipefail` when a pipeline is unavoidable.
- Treat a printed pytest summary without process exit and numeric exit artifact as incomplete evidence. Inspect descendants, terminate the superseded runner, and do not call it GREEN.
- If a failed run prints the complete failure summary but hangs during interpreter shutdown, retain it only as failure diagnostics. The replacement authoritative run still needs a normal zero exit.
- Bind wheel paths, logs, audit reports, and installed proofs to the exact candidate digest.

## Completion packet

Require all of:

- unchanged start/end candidate digest;
- focused public-contract GREEN;
- parser-based structure GREEN;
- touched-surface lint/compile/diff GREEN;
- current first-party freshness oracle GREEN;
- one uninterrupted full-suite zero exit;
- reproducible exact-candidate wheel digest;
- clean installed-artifact real-loader proof;
- returned, provenance-linked digest-pinned audits;
- clean commit and standalone foreground post-commit regression.
