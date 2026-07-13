# Verification Evidence Trackers

## Problem class

Long suites often exceed foreground command limits, so they run through a tracked background process. A successful background log proves the tests passed to a human, but some workspace-verification systems only attach evidence from a foreground test command that exits directly in the active turn.

## Reliable sequence

1. Finish all edits and commits first; verification must target the final workspace state.
2. Run the complete suite in the background and retain its process log, pass count, duration, and exit status.
3. Run structural, compile, diff, and clean-tree checks.
4. Build a **changed-path closure** before choosing the foreground packet:
   - direct behavior tests for each changed feature module;
   - protocol/schema/argument tests for changed contracts;
   - composition or operation-coverage tests for changed registries, mixins, exports, and dispatch tables;
   - authorization, replay, persistence, and server-routing tests for changed lifecycle boundaries.
5. Run that closure as one plain foreground `pytest` command below the timeout and require exit status 0.
6. If the workspace tracker still reports `unverified`, do **not** repeat the identical narrow command. Widen once to include every changed module's nearest consumer/coverage suite, again in one foreground invocation. Preserve the earlier full-suite result; evidence attachment is not a reason to rerun the full suite.
7. Report the full-suite result and foreground attachment result separately.

## Serialize stateful verification

A background full suite and a foreground changed-path packet are safe to overlap only when both are hermetic. Treat tests that share any HOME, profile directory, named session, daemon socket, database, worker queue, port, or external account as **stateful** and run exactly one such pytest process at a time.

If immediate foreground evidence is required while a stateful full suite is active, choose only deterministic unit/static tests that cannot touch those shared resources. Otherwise stop or finish the full suite before running the changed-path integration packet.

When an overlapped run fails in a lifecycle test:

1. Do not patch production code from the concurrent failure.
2. Stop the competing suite/process.
3. Re-run the exact failing test alone with the same environment.
4. If isolated GREEN, classify the earlier failure as verification interference and rerun the intended packet serially.
5. If isolated RED, debug the actual failure normally.

A passing isolated reproduction plus a subsequent serial packet is valid evidence; partial dots from the killed overlapping suite are not.

## Ad-hoc verification when no canonical command is detected

When the tracker explicitly says no canonical test/lint/build command was detected, create one focused disposable harness rather than relabeling earlier suite logs:

1. Generate the filename with the OS tempfile API (`tempfile.mkstemp` or `NamedTemporaryFile`) under `/tmp`, using the exact requested prefix when one is supplied.
2. Write and execute the harness through direct top-level file/terminal tool calls. Nested terminal execution inside a code-orchestration tool can be valid human evidence yet remain invisible to path-based verification tracking.
3. Target the canonical merged checkout. If the tracker lists stale or removed worktree paths, prove the canonical tree equals the surviving changed-worktree tree when available, then exercise the merged files rather than recreating obsolete worktrees.
4. Include the focused changed-path tests plus direct temporary-resource probes for the critical behavior. For transaction code, prefer a real temporary Git repository over mocks: mutate tracked data, create residue, force rollback, and assert exact HEAD/index/worktree restoration.
5. Run the relevant validators, structure checks, and syntax checks from the same harness. Require a direct zero exit.
6. Delete the harness and any reviewer-only temporary configuration after execution, and print the cleanup result.
7. Label this evidence **ad-hoc verification**, not “full suite green.” If the harness itself fails only in reporting after checks ran, fix the harness and rerun it end-to-end; the earlier partial run is not the passing artifact.

## Why narrow packets can be missed

A tracker may associate evidence with changed paths rather than infer transitive coverage. Acceptance tests can thoroughly exercise a lifecycle while still leaving changed composition files—operation registries, protocol ledgers, contract extensions, or server routers—without attributable evidence. Passing the same narrow packet again adds no information. The correct response is a finite closure expansion, not an unbounded retry loop.

## Avoid

- Re-running a 15–20 minute full suite repeatedly when only evidence attachment is missing.
- Treating a clean Git tree as test evidence.
- Running the foreground suite before the final edit or commit.
- Claiming that a background process passed without reading its final log and status.

## Example evidence

```text
FULL: background pytest -> 352 passed, exit 0
ATTACHED: foreground changed-subsystem pytest -> 33 passed, exit 0
STRUCTURE: verifier + compile + diff -> exit 0
HEAD/TREE: exact SHA, clean
```
