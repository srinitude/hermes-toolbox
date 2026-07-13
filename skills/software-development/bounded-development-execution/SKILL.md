---
name: bounded-development-execution
description: Execute large multi-slice software plans safely under finite tool, time, or context budgets while preserving verified, committed checkpoints.
version: 0.3.20
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [software-development, execution, checkpoints, tdd, verification]
    related_skills: [test-driven-development, plan-update-executor, requesting-code-review]
---

# Bounded Development Execution

## When to Use

Use this skill when a software plan has multiple independently verifiable slices, execution is constrained by finite time/tool/context budgets, or interruption-safe committed checkpoints are required. Do not use it for a single small change that can be completed and verified in one ordinary TDD cycle.

## Overview

This skill keeps long, multi-slice coding work green, verified, and recoverable at every interruption boundary.

## Core Rule

```text
Never spend the remaining execution budget starting a slice you cannot bring to GREEN, verify, and checkpoint.
```

A partially started production change is worse than a clearly reported unstarted slice. A committed green checkpoint lets the next run continue without reconstructing intent from a dirty tree.

## Procedure

1. **Read governing artifacts first.** Read repository instructions, the complete requested plan range, current Git state, and relevant implementation sources before editing. If the request names a saved plan but the exact plan cannot be located and read, stop before writing tests or production code and ask for its path/content; do not infer public APIs or acceptance details from a short task title.
2. **Map vertical slices.** Convert each numbered task into the smallest independently testable public behavior slices. Record required files, focused test command, regression command, structural checks, and requested commit boundary.
3. **Budget the run.** Estimate tool-calling turns—not shell commands—for each task-required slice: test write, RED run, implementation, GREEN run, and regression. Reserve a final block for full-suite checks, structural verification, review, commit, and clean-status proof. If all required micro-cycles cannot fit, combine cases governed by one policy decision into a parameterized public-behavior matrix before the first RED rather than beginning a sequence that cannot reach the requested commit. Prioritize named acceptance behavior over optional helper-level tests; prove helpers through the first public slice when practical.
4. **Classify inherited work.** If meaningful untracked source/tests already exist, preserve and review them as user work. Record focused and full-suite baselines, but do not present already-existing behavior as new test-first work. Refactor it in place under green tests.
5. **Inspect live contracts source-first.** If the plan and current source disagree, capture the discrepancy as a failing/hold behavior. Never fabricate compatibility to make the plan appear complete.
6. **Run strict RED→GREEN.** Add one behavior test, run it and confirm the expected failure, write the minimum production change, run focused GREEN, then run the relevant regression suite.
7. **Checkpoint at the requested boundary.** Keep every slice green and recoverable. Commit each slice only when that is the governing boundary; when the user explicitly requests one clean commit for one numbered task, finish all task slices and verification before creating that one commit.
8. **Reassess before the next slice.** Recount unfinished acceptance bullets and compare them, plus reserved final checks, with the remaining execution budget. Continue only when the next slice can reach verified GREEN without imperiling completion.
9. **Finish with objective verification.** Run the full suite, compile/static checks, repository-specific structural checks, clean-tree/status checks, and requested scans. Report actual outputs only.
10. **Attach verification to the final workspace state.** When a full suite must run as a background process, treat its successful log as human evidence but not necessarily as automation-recognized verification. After all edits and commits are finished, run one representative foreground `pytest` command whose changed-path closure covers direct behavior plus protocol, composition/coverage, authorization, persistence, and routing modules touched by the diff. Require a direct zero exit status in the same turn. If the tracker remains unverified, never repeat the identical narrow packet: widen once to the nearest consumer/coverage tests for every changed path. Do not repeatedly rerun the entire long suite merely to satisfy an evidence tracker. Never overlap suites that share HOME/profile/session/database/daemon resources: keep one stateful integration suite active, and use only deterministic non-overlapping unit slices if immediate foreground evidence is required. If an external verifier explicitly repeats a requirement for a shared-state integration file, terminate the long suite first, mark that run superseded, run the exact foreground file, and restart one authoritative full suite from scratch; never race the two or cite the SIGTERM run. Follow `references/verification-evidence-trackers.md`.

### Unmask Boundary Failures Before Repair

When a socket, RPC, HTTP, subprocess, or worker boundary converts an unexpected exception into a generic availability error:

1. Preserve a RED through the public boundary so the user-visible failure remains the oracle.
2. Invoke the same handler directly with the identical fixture, identity, request, and fault injection to recover the underlying traceback. Do not weaken the production error envelope for diagnostics.
3. If direct invocation yields the intended domain error while only the full suite fails, classify the issue as order- or load-sensitive before changing domain logic.
4. Inspect collection adjacency, run the neighboring sequence, then stress-run the exact test.
5. Measure wall-clock duration around the boundary. Compare successful duration with both fixture and production deadlines; repeated success near the fixture deadline is unhealthy evidence.
6. If the fixture alone has an artificially short deadline, align it with production semantics. Do not enlarge production deadlines to hide a real regression.
7. When stricter integrity initialization invalidates old fixtures, provision them through the same authenticated production primitive rather than bypassing verification.

Follow `references/boundary-masking-and-suite-load.md` for the worked diagnostic sequence and evidence rules.

## Compact Evidence Ledger

Maintain this per slice while working:

```text
Slice: <behavior>
RED: <command> -> <expected failure>
GREEN: <command> -> <actual pass count>
REGRESSION: <command> -> <actual result>
COMMIT: <full SHA>
```

Keep command output compact. For parameterized boundary tests, assign short test IDs and construct huge inputs inside the test so a failure does not print megabytes of payload.

## Checkpoint Rules

- A valid checkpoint has focused GREEN, relevant regressions GREEN, and a commit when commits were requested.
- Do not call a task complete because files exist; exercise the public behavior.
- Do not postpone all structural checks until after dozens of slices. Run cheap line/construct checks at each task boundary and the canonical verifier at the end.
- Keep source/test size constraints visible while editing; discovering them only at final verification causes expensive rewrites.
- If setup must change, distinguish repository changes from local environment changes and never commit generated environments or caches.
- High-frequency observational polls must not consume mutation-journal rows, state-transition audit events, or completed replay-registry capacity. Distinguish true no-op, successful handoff, and stale-state cleanup before writing; only the latter two reserve and audit. Completed replay returns stored authority without another transition event. Prove this beyond every configured capacity with a stable test clock and a subsequent real handoff. Follow `references/durable-noop-polling.md`.

## Fail-Closed Contract Work

When pinning an external or installed contract:

- Inspect the exact local source/version read-only.
- Store observed reality separately from declared/desired compatibility.
- A disagreement should yield an explicit compatibility hold with evidence.
- Tests may be green because the hold is correctly detected; green must not mean unsupported parity was invented.
- Avoid importing modules that initialize or mutate live state when AST/source inspection is sufficient.
- For public-export semantic sanitizers, model YAML as a source-marked graph, analyze shell paths per word with symbolic projections, preserve valid markup/language constructs, and prove rejection at the real staging transaction. Follow `references/adversarial-semantic-sanitizers.md`.
- When a composed native helper must be atomic, audit nested transaction boundaries, process-global patching, retry topology, and pre-commit external side effects before proposing a wrapper. If unchanged native behavior cannot satisfy acceptance, preserve an explicit compatibility hold rather than fabricating parity. Follow `references/native-composite-atomicity.md`.

## Exact-HEAD Read-Only Audits

When a user asks for a plan/spec audit against current HEAD, pin the Git object before inspection and keep working-tree state separate. If concurrent edits appear, switch all evidence gathering and tests to `git show`/`git archive` for the captured SHA, then re-check HEAD before reporting. Run tests from disposable roots with bytecode and pytest caches disabled, and use deterministic adversarial probes for fail-closed claims that green tests do not prove.

Follow `references/exact-head-read-only-audits.md` for the full evidence-mapping, temporary-root, verdict, and concurrent-writer procedure.

## Reserve Verification Capacity

Treat each production edit and its focused GREEN run as an indivisible pair.

### Freeze scope when the final reserve begins

Once all named acceptance behavior is GREEN and the reserved final-verification block begins, stop adding optional hardening tests or refactors. A late RED is still a new slice, even when it looks like a tiny validation improvement. Start it only when it closes a stated acceptance gap **and** enough tool iterations remain for implementation, focused GREEN, full regression, structural/security review, commit, and clean-status proof. Otherwise record it as follow-up evidence and preserve the verified task boundary. Never trade a fully tested, committable task for one more speculative edge case that can leave the tree RED and uncommitted at the execution ceiling.

For security state machines, finish the complete exposure/transition matrix before declaring the first final-verification pass. Include token absence from database/journal bytes, logs/audit/recovery records, and every secret-bearing DTO's `repr()`—not only the mint response. A late assertion against a request or error object's representation can correctly reopen RED and invalidate earlier full-suite evidence. Follow `references/approval-state-machine-execution.md` for the atomic reservation, consumption, recovery, and secret-channel checklist.

1. Before a production patch, reserve at least one later tool iteration for focused GREEN and another when regression evidence is required.
2. Never spend the final available iteration on production code, schema changes, fixtures, or commit preparation. If remaining capacity is uncertain, stop before the edit and preserve the prior verified tree.
3. Batch independent reads and discovery, but serialize RED → implementation → GREEN because each step depends on the previous result.
4. Prefer one coherent public-scenario test per state transition over several nearly identical micro-tests. Do not weaken assertions; reduce orchestration overhead.
5. Update the evidence ledger immediately after RED and GREEN instead of reconstructing it at the end.

## External Paid-Resource Reconciliation

Treat cloud create/delete operations as a separate fail-closed state machine. A timed-out create, nonzero client result, or empty immediate list does not prove that no resource exists; providers may accept a request before inventory becomes consistent.

1. Persist a unique non-secret ownership tuple, lifecycle backstops, resource units, and spend cap **before** create.
2. After any ambiguous create response, never issue a second create. Reconcile the authoritative provider inventory with bounded retries until exactly one owned resource or a proven zero result exists.
3. Persist the resource ID as soon as it is uniquely known. Stop and delete by that exact ID.
4. Distinguish `stopped`, `delete requested`, and `absent`. Only authoritative inventory absence proves cleanup; auto-delete is a backstop, not acceptance evidence.
5. If a residual paid resource remains, freeze unrelated execution and report/continue cleanup first. Do not let code review, feature work, or another provisioning attempt outrank cost containment.
6. Preserve the private evidence record on failure, including corrected units and delayed-billing limitations; never overwrite a failed cleanup into a success narrative.

Follow `references/paid-resource-lifecycle-recovery.md` for the durable intent record, eventual-consistency retry procedure, cleanup state machine, and evidence schema.

## Approaching a Hard Limit

1. Complete the current GREEN verification; never intentionally leave a production edit without its focused GREEN.
2. Commit only if the governing boundary permits a partial checkpoint. If the user requested one clean task-level commit, leave the verified partial tree uncommitted and state that clearly rather than violating the boundary.
3. Do not begin another production edit.
4. Record which acceptance bullets are complete, partial, and untouched.
5. Report the last full-suite result separately from any later focused result.
6. Explicitly identify uncommitted files and checks not yet run.
7. If an unexpected ceiling lands after an edit but before GREEN, label that exact slice unverified and make its focused test the first action on continuation.

### Hard ceiling tripwire

Treat **any** runtime orchestration warning as a scope-freeze signal, not merely an error to work around. This includes tool-loop/iteration warnings, repeated-exact-failure warnings, context-compression warnings during an unfinished slice, and a notice that the maximum tool-calling iterations is approaching. Immediately mark the current slice as the final slice in the task ledger; after that warning, every remaining tool call must belong to correcting the warned-about command, focused GREEN, regression, structure/drift review, commit, or clean-status proof for that slice. Do not dispatch new audits, add a new test family, inspect the next blocker family, or open another behavior slice even after obtaining an intermediate GREEN. **An intermediate GREEN does not clear the tripwire.** If the warning arrived after an unverified production/schema edit, freeze the changed-path set: do not add another module, operation, migration table, protocol route, or architectural layer until that exact edit has focused GREEN plus structural/static verification. If the remaining calls cannot attach those checks, stop immediately and report the edit as unverified rather than trying to “finish more” before the ceiling.

After a blocker audit invalidates a candidate, **rebudget the entire remediation packet before the first edit**. Count each confirmed blocker family as at least one serialized RED→edit→GREEN cycle, reserve regression/static/sealing turns, and stop at a clean evidence boundary if the packet does not fit. Do not interpret a large remaining task list as permission to keep beginning slices. When the governing boundary requires one final commit and therefore forbids intermediate commits, use stricter admission: begin a remediation family only if the remaining call budget can finish every already-open family and return the whole tree to verified GREEN. A tiny post-checkpoint test, import, or displaced test declaration can strand a previously clean repository and erase the checkpoint’s value.

When targeted patch insertion accidentally removes or displaces the following function/class declaration, repair that structural boundary **before** running RED. Treat patch-tool success as text replacement evidence, not syntax or test-boundary proof; immediately inspect the local edited seam or run the parser-based structural verifier when the replacement touched a declaration boundary.

### Budget tool-calling iterations, not just shell commands

A runtime may cap assistant tool-calling turns even when every command is fast. Count every sequential tool round trip against that ceiling; parallel calls in one turn are one orchestration opportunity, while RED → edit → GREEN remains necessarily serialized.

- Before the first edit, reserve at least four final tool turns: focused GREEN, relevant/full regression, structural and diff review, and commit plus clean-status proof.
- Recalculate that reserve after every RED→GREEN slice. Stop before an edit when the remaining turns cannot cover the edit's GREEN plus the final reserve.
- Put closely related negative cases into one parameterized public-behavior slice when they require the same production decision. Do not spend one RED/edit/GREEN cycle per field mismatch when one exact-scope matrix proves the contract.
- Batch independent reads, baselines, and final read-only checks. Never parallelize edits to the same file or steps with output dependencies.
- If the ceiling interrupts immediately after production code, do not infer GREEN from inspection. Report the exact unverified edit, leave it uncommitted, and begin the continuation with its focused test before making any further change.

## Delegated Writer Handoffs

When a background coding agent owns a slice, treat it as the sole writer for its declared files until it finishes. Do not run broad formatters, full-suite repair loops, or overlapping edits against an agent that may intentionally be between RED and GREEN.

1. Give the child one numbered task, exact file/repository boundary, acceptance matrix, final verification reserve, and commit boundary.
2. If an external verification prompt arrives while the child is active, run only a narrow non-overlapping suite for the previously committed files. State that full regression is deferred because the active writer may be in a deliberate RED phase.
3. Treat the child summary as a handoff, not proof. Re-read every noted changed file, run the first outstanding focused test, and inspect Git status before editing or committing.
4. If the child hit its tool ceiling after a production edit, continue with focused GREEN before adding hardening. If it stopped after adding a RED test, run that exact test to witness the inherited RED, then implement.
5. Re-run full regression, structural checks, scans, and diff review on the parent-owned final tree. Never commit merely because the child reported earlier GREEN evidence.

This preserves strict TDD without racing a delegated writer or laundering stale evidence across tree states.

## Prove Policy Semantics at the Authoritative Boundary

A green unit suite for a policy evaluator does not prove that the broker, server, dispatcher, or mutation handler actually invokes that evaluator. Before marking a policy phase complete:

1. Trace every acceptance rule from the saved plan through the authoritative request entry point, authenticated actor context, selector resolution, policy decision, native mutation, and durable sidecar result.
2. Add real public-boundary integration tests using temporary stores and native adapters. Evaluator-only tests are not phase evidence.
3. If generic transition and richer workflow evaluators coexist, prove which one the handler calls. An evaluator referenced only by wrappers and unit tests is disconnected implementation.
4. Carry the server-authenticated actor profile through selector and policy calls. Do not let a runtime-default profile silently replace a capability-authenticated worker profile; human and worker mismatches must still fail closed at their authentication boundaries.
5. Persist workflow identity only after native success: root/phase marker, parent binding, work key/run, invariant snapshot, and context-bundle chain state. A decision object without this durable path is incomplete.
6. When integration disproves stale tests, first witness the public regression RED, then reconcile those tests to the authoritative plan semantics.

Checkpoint this integration slice before expanding native operation coverage, transport, rollout, or cutover work.

## Reconcile Asynchronous Audits by Baseline

Background audits and reviewers may finish after the parent has advanced the tree. Treat every result as evidence about the exact revision it inspected, not as a verdict on the current working tree.

Before dispatching a pinned pre-commit audit, finish cheap formatting, structure, type, staged-diff, and security scans; then freeze both worktree and index until the audit batch returns. Do not restage “formatting-only” changes during an exact-digest audit: byte drift invalidates certification even when semantics are unchanged. Run the expensive authoritative full suite only after those cheap gates and blocking audits are clean, unless the user explicitly requires suite evidence first.

If audit artifacts are recovered from a cache, validate their repository path, task statement, HEAD, staged digest, and substantive content before attribution. A matching completion timestamp or filename is not provenance; unrelated cached summaries are invalid evidence and require a fresh dispatch.

1. Require each delegated audit to report its audited commit and whether it inspected committed Git objects or a dirty worktree.
2. Compare that baseline with current `HEAD` before accepting any pass, partial, or missing classification.
3. Mark findings as **still valid**, **superseded**, or **needs fresh verification**. Never copy an old acceptance matrix directly into current status.
4. Apply still-valid early-phase findings before advancing later phases. If a later slice is already GREEN, checkpoint it cleanly, then return to the earliest unmet fail-closed gate.
5. After material fixes, dispatch a fresh narrow audit against the new committed checkpoint rather than asking the old audit to stand in for current evidence.
6. Do not let a late asynchronous result trigger overlapping edits while another writer is active; reconcile read-only first.

7. Treat a late audit as a new scope decision, not permission to reopen every deferred rollout gate. First checkpoint any already-GREEN correction, classify the audit against its baseline, and estimate a fresh final reserve. Close only findings that were blockers for the audited slice; queue explicitly deferred follow-on slices unless each can still reach RED→GREEN→regression→structure→commit before the ceiling. Never chain “while here” lifecycle improvements after starting a long final suite.

When a hard ceiling is approaching, stop after a clean checkpoint. Do not use the remaining turns to begin an optional recovery, security, or selector edge case unless the full RED→GREEN→regression→structure→commit reserve still fits. A tiny unfinished import or test edit makes earlier full-suite evidence stale.

For deterministic tests of atomic authority races and post-native crash windows without fake adapters, follow `references/real-concurrency-and-crash-injection.md`.

## Independent Reviewer Hygiene

Treat independent review as a pinned-tree evidence process, not a ceremonial pass:

- Recompute the verdict locally; concrete security or logic findings override a contradictory `passed: true`.
- A timeout, malformed response, unknown baseline, provider policy refusal, or filtered review is no verdict.
- When a provider filters an otherwise legitimate local release review, keep the candidate frozen and re-dispatch against the same exact digest with narrower release-integrity, maintainability, and harmless-local-fixture wording. Do not weaken the requested checks, count the refusal as PASS/FAIL, or edit/reseal merely to retry review.
- Any amend, rebase, merge, or follow-up fix invalidates the prior verdict for the changed delta.
- Run external coding reviewers in an isolated worktree when possible and compare `git status --porcelain` before and after, including timeout paths.
- Remove only proven newly generated reviewer metadata; preserve inherited untracked work.
- Stage explicit reviewed paths rather than `git add -A`, then prove clean status after commit.

When live rollout reveals that a validator rejected a legitimate upstream identifier, preserve that failure as RED, inspect the pinned encoder/alphabet, add valid and invalid boundary cases, and patch the shared validator narrowly. Do not broaden to generic alphanumerics.

Follow `references/independent-reviewer-hygiene.md` for verdict reconciliation, stale-review handling, reviewer artifact cleanup, and pinned live-identifier corrections.

## Pitfalls

- **Treating a tested server helper as a deployable service.** Require strict production config, exact operator/launcher enrollment, request serving, dispatch reconciliation, supervised launcher startup/shutdown, installed-wheel execution, and offline backup/restore. Never weaken PID/start-time authentication to same-UID trust to make a static service file convenient. Follow `references/secure-local-broker-deployment.md`.
- **Binding a same-UID launcher before kernel confinement is proven.** Configuration metadata is not privilege separation. Transport sandbox policy through a sealed descriptor, require readiness before PID/start binding, keep writable roots disjoint from authority, and never convert arbitrary absolute argv into read allowlists. Follow `references/capability-gated-worker-launches.md`.
- **Keeping parent/child spawning after choosing distinct service identities.** Once broker, launcher, and worker are separate OS principals, production enrollment must be socket/pidfd/service-manager derived; the broker must not spawn the launcher, and the launcher must not spawn or identify the worker. Broker-only fixed-unit activation, credential delivery, invocation/cgroup binding, protocol-level `Type=notify`, recovery, and inert installer boundaries are one coherent vertical slice. Follow `references/fixed-systemd-service-boundaries.md`.
- **Re-resolving installer paths after validating a parent.** Retain a trusted parent dirfd through no-overwrite creation, file evidence, manifest verification, cleanup, and `fsync`; cleanup must run only when this invocation created the destination. The helper that performs `mkdirat` must own rollback until it successfully returns an opened, validated child dirfd—otherwise `EMFILE` between `mkdirat` and `openat` leaves an orphan. Prove this with a real child-process `RLIMIT_NOFILE` test, not syscall mocks. Follow `references/secure-local-broker-deployment.md` and `references/exact-candidate-sealing.md`.
- **Letting a clean-wheel tool choose a different interpreter.** Build and install with the project/pinned interpreter explicitly (`uv venv --python <validated-python> ...`); an implicit `uv venv` may select a newer interpreter and trigger legitimate fail-closed compatibility drift unrelated to wheel contents. Verify `sys.version_info`, import origin under `site-packages`, packaged data, and critical subprocess tests. Follow `references/exact-candidate-sealing.md`.
- **Blindly accepting broad linter auto-fixes.** Safe-looking B009/B010 rewrites can turn deliberate dynamic `ModuleType` `getattr`/`setattr` boundaries into statically invalid direct attributes. Re-run the candidate type checker after auto-fix, restore dynamic access with narrow justified ignores when the foreign module contract is genuinely dynamic, and rerun behavior tests. Follow `references/exact-candidate-sealing.md`.

- **Misreading the commit boundary.** Reconcile repository defaults with the user’s explicit request. “One clean commit” for one task means locally green slices followed by one final commit, not several intermediate commits.
- **Treating inherited untracked code as disposable or as fresh TDD work.** Preserve it as user work, baseline it, and distinguish inherited evidence from new RED→GREEN evidence.
- **Spending the budget on optional internals before public acceptance.** Test named APIs and end-to-end persistence first; helper-level tests are secondary unless explicitly required.
- **Starting the next task after a focused GREEN without a recoverable checkpoint.** A checkpoint may be a commit or a clearly recorded verified partial tree, depending on the requested boundary.
- **Oversized pytest parameter representations.** They can consume the output/context budget and hide the useful traceback.
- **Treating an expected compatibility hold as implementation failure.** Fail-closed detection can be the correct behavior.
- **Letting live acceptance tests inherit a default session.** For session-oriented local services, require an owned named test server, exact-socket environment on every consumer subprocess, protected-session before/after snapshots, and teardown assertions. A missing selector must produce typed unavailable, never native fallback. Follow `references/isolated-named-session-acceptance.md`.
- **Binding mutable pane state as identity.** Pane focus, status, and revision are operation preconditions, not stable caller identity. Binding them into confirmation identity turns ordinary state drift into the wrong `stale_identity` classification.
- **Transforming an approved request after fingerprinting.** Validation may inspect normalized text for emptiness, but native dispatch must preserve the exact approved value; silent trimming breaks exact-operation authority.
- **Checking replay only after active-capability authorization.** Terminalizing a worker capability can accidentally make its completed request unreplayable. Authenticate terminal replay credentials only against the same completed request ID, fingerprint, peer, and scope—never as authority for new work.
- **Marking the journal complete before sidecar policy state is durable.** If native and sidecar stores are separate, a sidecar failure must leave recovery-required ambiguity rather than a completed row that falsely claims full success.
- **Claiming a final suite result after later untested edits.** Timestamp results conceptually: state which commit/tree each result covers.
- **Using a final summary as a substitute for completion.** A summary must distinguish completed artifacts from partial work precisely.

## Verification Checklist

- [ ] Repository instructions and full task range were read before edits.
- [ ] Every production change had a focused failing test first.
- [ ] Every recorded RED failed for the intended missing behavior.
- [ ] Every completed slice reached focused and regression GREEN.
- [ ] Every requested green-slice commit has a full SHA.
- [ ] No next slice was started without enough budget to checkpoint it.
- [ ] Final structural and clean-tree checks were actually run.
- [ ] Reported test results identify whether they cover committed or uncommitted state.

## References

- `references/adversarial-semantic-sanitizers.md` — YAML graph/source-mark policy, semantic credential grammars including static byte values, shell-word symbolic projection, compact C++/markup compatibility, real-manager outcome checks, canonical/direct inventories and release fingerprints, complete per-target present/absent rollback seals with raw-JSON key uniqueness, recoverable batch journals, cache-safe/sharded verification, transactional rollback, and exact-digest review generations.
- `references/exact-candidate-sealing.md` — staged-tree invalidation, pinned-interpreter wheel proof, real RLIMIT atomic rollback tests, and linter auto-fix review.
- `references/large-multi-slice-runs.md` — worksheet and call-budget example for long strict-TDD implementation plans.
- `references/tool-call-budgeted-tdd.md` — pre-edit turn worksheet, matrix rule, saved-plan gate, and interruption recovery for finite orchestration ceilings.
- `references/untracked-single-task-runs.md` — preflight, acceptance prioritization, and commit-boundary reconciliation when a task inherits untracked implementation work.
- `references/approval-state-machine-execution.md` — exact approval/capability state-machine checklist for identity binding, atomic journal reservation, one-winner consumption, recovery inspection, and secret-channel tests.
- `references/broker-boundary-tdd.md` — server-derived operator identity, real UDS/RST acceptance, meaningful-RED recovery, sidecar migrations, Project drift, and last-verified-commit reporting.
- `references/capability-gated-worker-launches.md` — native workspace-bound leases, one-byte same-PID exec gates, minimal environments, replay-safe started acknowledgement, real subprocess tests, and exit-reconciliation cautions.
- `references/pinned-native-adapter-execution.md` — fail-closed contract verification, process-global import/environment isolation, production-origin checks, stable error/audit separation, and real temp-root native tests.
- `references/structural-contract-verification.md` — parser-based file/construct/nesting gates, bounded refactoring patterns, and final-tree verification order.
- `references/verification-evidence-trackers.md` — full-suite background evidence plus foreground changed-subsystem verification attachment.
- `references/real-concurrency-and-crash-injection.md` — deterministic real-store barriers and post-native fault injection for exactly-once capability, journal, approval, and recovery tests.
- `references/isolated-named-session-acceptance.md` — exact-socket live test fixtures, protected-session snapshot proof, bounded topology projection, and stable caller identity binding.
- `references/paid-resource-lifecycle-recovery.md` — durable ownership intent, eventual-consistency reconciliation, stop/delete/absence distinctions, cost containment, and residual-resource evidence.
- `references/secure-local-broker-deployment.md` — distinct service enrollment, daemon completeness, descriptor-bound inert publication, installed-wheel portability, and authenticated offline backup/staging restore.
- `references/fixed-systemd-service-boundaries.md` — pairwise service identities, pidfd/systemd generation binding, fixed worker-slot activation, credentials, protocol readiness, cgroup recovery, and inert installer proof.
- `references/independent-reviewer-hygiene.md` — pinned-tree verdict reconciliation, timeout/staleness handling, external reviewer artifact cleanup, targeted staging, and source-pinned live-identifier corrections.
- `references/transactional-repository-publishers.md` — outer rollback through export, validators, exact staging, commit, and push; real Git-hook regressions; fail-closed remote visibility; and safe publisher resume sequencing.
