# Inherited Untracked Work Under a Hard Execution Budget

Use this note when a numbered plan task begins with meaningful untracked source/tests and must end as one verified commit.

## Preflight ledger

Before editing, capture:

- exact task acceptance bullets and named APIs;
- repository instructions and commit-author requirements;
- tracked/untracked/ignored status;
- baseline focused and full-suite results;
- current file, function, method, and class-span limits;
- which inherited tests already prove behavior versus merely exercise implementation.

Treat inherited untracked code as user work: preserve it, review it, and refactor in place. Do not claim test-first provenance for behavior that existed before the session. Record it as inherited baseline evidence instead.

## Budget by acceptance slice

List only task-required vertical slices first. For each, reserve calls for test edit, RED, production edit, GREEN, and regression. Reserve a final block for structural verification, full tests, diff/security review, author configuration, commit, and clean-status verification.

Implement acceptance-critical public behavior before optional internal utility tests. A helper such as canonical JSON still needs coverage, but it should normally be proved through the first public persistence slice unless the plan explicitly names the helper as an API. This avoids spending the execution budget while core acceptance bullets remain untouched.

## Commit-boundary reconciliation

When repository instructions say “commit each green vertical slice” but the user explicitly requests “one clean commit” for a single numbered task, treat the user’s requested task-level commit as the governing boundary unless it would violate a safety rule. Keep each slice green locally, but create the one commit only after the whole requested task passes final verification. Mention the reconciliation in the evidence ledger.

## Stop/go gate

Before starting each remaining slice, recount unfinished acceptance bullets and reserved final checks. If the budget cannot cover them all, do not spend calls polishing completed internals. Finish the highest-value coherent public slice, preserve a green tree, and report the exact gap. Never start a result-recording or mutation API without enough budget to run its focused GREEN afterward.

Reserve verification capacity mechanically: a production patch consumes two budget units—the patch itself and its focused GREEN—and three when a regression run is also required. Do not count a test edit and RED as proof that there is enough capacity for implementation.

If an external iteration ceiling interrupts after production changed but before GREEN, the continuation order is fixed:

1. Re-read the exact changed source and test rather than relying on the handoff summary alone.
2. Run the pending focused GREEN first.
3. If it fails, repair only that slice and rerun focused GREEN.
4. Run the relevant regression suite.
5. Only then mark the slice complete or begin another RED.

The handoff must call this slice **unverified**, name the focused command, and distinguish its state from the last verified checkpoint. This prevents a plausible implementation from being mistaken for completed work.
