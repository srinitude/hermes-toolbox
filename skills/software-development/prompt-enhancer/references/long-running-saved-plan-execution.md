# Long-running saved-plan execution

Use this pattern when an approved saved plan spans many TDD slices, multiple deployment surfaces, and later approval gates.

## Core loop

1. Re-read the saved plan and record immutable baselines for the plan, upstream checkout, watched/public repositories, active automation, and live services.
2. Convert plan tasks into bounded vertical slices. Keep one writer per shared worktree; read-only audits may run in parallel.
3. Give delegated writers one narrow task with exact allowed paths, prohibited side effects, structural limits, required RED/GREEN evidence, and a clean-commit finish line. A broad multi-task delegation often reaches its tool-call ceiling mid-RED.
4. While a writer owns files, do not repair its expected RED. If a verification interrupt arrives, run only the narrow committed/relevant tests and do not touch worker-owned files.
5. On worker completion, treat its summary as unverified. Re-read every modified file, run the unfinished focused test first, repair from the witnessed RED if needed, then run focused and full suites.
6. Run parser-based file/construct/nesting checks, compile/lint, banned-test-double/private-path/secret scans, `git diff --check`, author/trailer checks, and upstream/public drift comparisons before committing.
7. Commit each green slice before starting the next writer. Record exact test counts and commit SHA in session state, not persistent memory.
8. When live source disproves a plan or prior audit assumption, write a failing regression test for the live contract, correct the implementation, and keep the plan's safety outcome.
9. Treat custom-policy, privileged cutover, publication, paid action, and reviewed-manifest decisions as later gates. Blanket approval to execute the plan does not cross a gate whose concrete scope did not yet exist.
10. Continue non-dependent repository work up to a gate. Before live mutation, pause only relevant automation, create rollback artifacts, validate idempotence, and present the exact manifest.

## Plan-to-implementation traceability reset

Before continuing from a prior completion claim, build a task-by-task matrix from the exact saved plan: acceptance criterion, implementation path, public behavior test, verification command, and commit. Compare semantics rather than filenames or task numbers—a file named `dispatcher.py` does not prove a planned UDS dispatcher, and a green suite can validate the wrong workflow model. If the exact plan disproves the active task list or a prior summary, reopen the affected item immediately, preserve the evidence explaining why, and reconcile it through a witnessed regression RED before adding later-phase work.

## Tool-budget checkpoints

Treat every full focused/full-suite GREEN as a mandatory checkpoint, not merely an opportunity. Run structural and drift checks, commit the bounded slice, and run the smallest foreground post-commit regression before beginning another behavior family.

Before starting each slice, reserve enough calls for: focused GREEN, structural checks, the authoritative suite, log/status retrieval, commit, foreground post-commit verification, drift capture, and a user-visible handoff. If the remaining budget is unknown or visibly tight, do not start the slice; leave the prior committed checkpoint clean. Once the full suite for a slice starts, perform no new exploration or adjacent implementation until that slice is committed and its clean status is proven.

When the parent session approaches a tool-call or context ceiling, stop expanding scope. Never strand an already-green behavior family as a dirty worktree merely to start or investigate another group. If the runtime blocks further tools anyway, the final response must report the last real test output, last observed HEAD/status, and any known uncommitted paths accurately; never replace that evidence with a generic failure or fabricated uncertainty.

## Latency-conscious correctness

Optimize elapsed time, not merely tool-call count. Keep one writer, but fill safe read-only capacity with independent specification, security, and adversarial audits pinned to the same digest. If review rounds repeatedly uncover different blockers, add one broad adversarial preflight alongside the required reviewers and consolidate every returned finding into the next single RED→GREEN generation rather than repairing findings serially.

Overlap waits only with non-invalidating prerequisites: source quiet-window monitoring, exact inventory enumeration, immutable hash capture, and next-slice dependency ordering are useful while a frozen candidate is reviewed. Do not edit the frozen worktree, protected sources, or adjacent deliverables until the checkpoint is accepted. Start long quiet-window and stability proofs as early as their baseline is valid so they mature during review instead of becoming a later serial delay.

Run focused and authoritative suites once per changed digest after all currently known findings are repaired. Re-run a gate only when bytes, environment, or the relevant acceptance contract changed. Do not repeat an OS-temp verifier when a successful digest-bound run was cleaned up and a tracker merely replays stale attribution. On dual review PASS, verify the exact digest and clean status, commit immediately, run the smallest foreground post-commit regression, then release the next bounded slice.

## Delegation sizing

A practical coding delegation should target one plan task or one coherent behavior family. If a worker twice returns partial work at its call ceiling, stop re-delegating the same broad scope: finish the remaining RED/GREEN slices in the parent or split into smaller independent tasks.

## Drift evidence

Capture and compare:

- authoritative plan hash;
- upstream commit and dirty-status hash;
- watched/public repository commit and dirty-status hash;
- target worktree status and commit sequence;
- live process/cron/service state before any cutover;
- fresh post-edit test timestamps/results.

Do not claim “no drift” when a baseline was never recorded. Distinguish pre-existing dirt, intentional scoped writes, sibling-writer changes, and external concurrent drift.

## Live orchestration and restore contracts

When a saved plan depends on Herdr/Hermes process identity or full-server restoration, load [Herdr real-service restore TDD](herdr-real-service-restore-tdd.md). Disable native auto-restore inside the isolated fixture, prove no child launched before confirmation, and treat pre/post-restart terminal continuity as a live contract to test rather than an assumption. A safe compatibility path may need to correlate an exact pane/workspace/tab/cwd slot and a newly rebound terminal ID while retaining explicit profile/session ownership and human confirmation.

## Verification-interrupt rule

Repeated automated “unverified” notices can refer to already committed files. First confirm the target HEAD and clean status rather than assuming the notice describes current disk state. Re-run the narrow tests named by the notice and confirm temporary verifiers were removed. Avoid a full-suite run while another TDD writer may intentionally be RED; perform the comprehensive full-suite check after that writer reports completion.

Treat test processes as writers of runtime state even when they do not edit source. Never overlap suites that share `HOME`, profile/session directories, sockets, launcher state, board databases, or other fixed runtime paths. Serialize them, or give each process a distinct isolated HOME/basetemp/runtime root. If an overlapped daemon/worker test fails while the same test passes alone, first remove the overlap and reproduce in isolation before changing code; the isolated rerun is diagnosis, while a later sole authoritative suite is acceptance evidence.

For suites longer than the foreground tool timeout, run the complete suite as a tracked background process and retain its final exit code/output. Some verification trackers do not credit a successful `process.log` result as fresh foreground evidence. After the background suite passes, run the smallest directly relevant `pytest` set in a normal foreground terminal call so the tracker observes an ordinary zero exit. Report both results distinctly; do not rerun the entire long suite merely to satisfy tracker bookkeeping.
