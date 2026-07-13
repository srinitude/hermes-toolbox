# Tool-Call-Budgeted TDD

Use this worksheet before the first edit when a task requires strict RED→GREEN work under a finite orchestration ceiling.

## Preflight gate

Do not edit until all are true:

- The exact saved plan/task text is readable.
- Public API names and acceptance behavior come from that plan or live source, not inference.
- Repository commit boundaries and structural limits are known.
- A working focused-test command and full-suite baseline are recorded.

If a named plan cannot be found, ask for the path or contents. A short task title is not a substitute for the governing artifact.

### Enforce the missing-plan stop

Use at most two scoped retrieval rounds: first the named/workspace plan locations, then conversation history or a directly referenced parent artifact. If neither yields the complete governing task and its next-task boundary, stop and ask for the path or text. Do not keep widening into caches, spawn metadata, commit history, or adjacent plans; those can corroborate context but cannot establish omitted acceptance criteria. A detailed audit, prior implementation summary, or descriptive delegation title is supplemental evidence, not authorization to infer the plan. Spend no production-edit budget until this gate passes.

## Turn budget

Count sequential assistant tool turns, not commands inside a shell call.

For each planned slice, reserve:

1. Write one focused test or one parameterized behavior matrix.
2. Run and inspect RED.
3. Write minimal production code.
4. Run focused GREEN.
5. Run regression evidence when required.

Then reserve at least four final turns for:

1. Final focused/full verification.
2. Static, structural, and policy checks.
3. Diff/status review and fixes.
4. Commit plus clean-status proof.

Do not start if the planned slices plus final reserve do not fit.

## Matrix rule

A parameterized matrix is still one vertical slice when every row exercises the same public entry point and the same policy decision, such as rejecting exact-scope mismatches. It is not permission to write unrelated tests horizontally.

Prefer one matrix over separate cycles when:

- Inputs differ only by one selector or scope field.
- Expected error code/message is the same policy outcome.
- One production decision should satisfy all rows.

Keep separate cycles when rows require different public APIs, state transitions, persistence effects, or policy decisions.

## Reassessment gate

After every GREEN, recount unfinished acceptance bullets and remaining turns. Stop before the next test edit unless the next slice can reach GREEN and the final four-turn reserve remains intact.

If interrupted after a test edit but before RED, report it as unverified—not as a completed RED slice. If interrupted after production code but before GREEN, make that focused test the first continuation action.
