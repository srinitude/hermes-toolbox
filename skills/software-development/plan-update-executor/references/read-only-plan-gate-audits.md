# Read-only implementation-plan and cutover-gate audits

Use this reference when the user asks for a precise audit of numbered implementation tasks, approval gates, deployment readiness, or cutover blockers without changing anything.

## Evidence model

Keep these evidence layers separate:

1. **Plan requirements** — exact task artifacts, tests, prerequisites, approvals, and exit criteria.
2. **Canonical committed state** — the named commit or current `HEAD`; use tracked-file inventory and an isolated test run when practical.
3. **Live worktree state** — dirty/untracked files, especially work appearing concurrently during the audit.
4. **Installed/runtime state** — profiles, services, launchers, plugins, jobs, sockets, and narrowly selected config keys.
5. **Historical plan claims** — useful context, but not current proof.

Never blend an uncommitted in-progress edit into completed committed evidence. If the worktree changes during the audit, record the before/after status, treat the shared tree as concurrently owned, and avoid broad tests against a writer that may be between RED and GREEN. Test the named commit from a temporary archive or equivalent isolated checkout, remove the temporary material, and report committed and dirty evidence separately.

## Read-only discipline

- Do not patch plans, code, configs, profiles, services, jobs, or databases.
- Prefer read-only status/config-key commands and tracked-file inventories.
- Do not read secrets, auth stores, sessions, memories, or unrelated runtime databases.
- A nominal SQLite read can migrate schema, create WAL files, or update metadata. When mutation-free proof matters, use an existing validated plan snapshot, a consistent online backup opened read-only, or a broker/read adapter rather than the native connection path.
- For tests, suppress persistent caches and bytecode when possible (`PYTHONDONTWRITEBYTECODE=1`, pytest `-p no:cacheprovider`). If an isolated committed-tree test needs temporary extraction, use a uniquely scoped temporary directory, remove it on exit, and state that no persistent target files changed.
- Prefer a detached temporary clone over `git worktree add` for strict read-only audits: worktrees write metadata into the source repository. When reusing the source repository's virtualenv, remember that an editable install points back to the moving tree. Force pinned imports with `PYTHONPATH="<clone>/src:<clone>"`, disable bytecode/cache writes, and verify the clone remains clean afterward.
- Do not export a shared temporary-root variable such as `TMPDIR` across parallel commands in a persistent shell. One command can remove a directory another command inherited. Use an explicit unique `/tmp/<audit>.XXXXXX` root per command and child-local `env NAME=value command` assignments.
- End with a final status check on every audited repository and named protected checkout. If `HEAD` moved after pinning, report the new hash and dirty paths as concurrent work excluded from the pinned evidence; do not silently mix or repin.

## Procedure

1. Read the full requested task range and all later approval, go/no-go, shadow, migration, adversarial, review, and completion gates. Also read earlier tasks that are prerequisites for the requested range.
2. Pin the audit identity: plan path/digest, repository path, commit SHA, initial worktree status, runtime version/commit, and audit time when relevant.
3. Inventory tracked artifacts by task. Compare exact required paths and behavioral components to committed files; do not infer completion from similarly named lower-level helpers.
4. Inventory tests by acceptance bullet. Distinguish:
   - exact end-to-end proof,
   - partial substrate tests,
   - implied acceptance tests with no implementation,
   - deployed/live evidence that cannot exist before cutover.
   Trace each behavioral criterion through the real path: `public request -> decode/bounds -> authenticated origin -> canonical selectors -> policy -> reservation -> native mutation -> authoritative post-state`. A correct standalone engine is not acceptance evidence if the broker/handler never invokes it.
5. Run the canonical committed suite in isolation. A green lower-level suite proves only its collected tests, not later unimplemented task matrices. Add safe temporary-root probes for security- or semantics-critical gaps that green tests miss. Useful probes include same-commit unrecorded contract mutations, runtime/schema `N` versus `N+1` bounds, oversized or non-finite response serialization, stale capability use after an authoritative terminal transition, approval-label retargeting between preview and consume, and model-versus-human requests sharing one OS identity.
6. For every observed denial, identify the layer that denied it. An authorization requirement is not satisfied when the request was authorized, journaled, and only failed later as a native conflict. Likewise distinguish canonical identity binding from a mutable label, authoritative terminal state from a local cache flag, and a registry/library that exists from one actually used by production dispatch.
7. Inspect installed state narrowly: profile count, plugin presence/override mode, dispatcher flags, service principals/units/socket, launcher target, job enabled/error state, publisher state, and protected-upstream diff. Avoid printing full configs when selected keys suffice.
8. Build a task matrix with one row per task: `complete`, `partial`, `not started`, `blocked`, or `approval-gated`; present evidence; exact missing artifacts/tests; and gate dependency.
9. Build the cutover preflight as an independent pass/fail/unknown ledger. An instantaneous “no process found” can pass the process check while an enabled failing job remains a maintenance blocker.
10. Enumerate every approval boundary separately: source development, active-profile/plugin installation, launcher replacement, dashboard mode, root manifest, shadow exit, maintenance cutover, publication, and paid/live smoke when present.
11. Separate work that can proceed safely before approval from actions that must wait. Source-only implementation, temporary-root tests, dry-run units/installers, isolated integration fixtures, and documentation can usually proceed; live sync, root deployment, restarts, board migration, destructive adversarial testing, and publication cannot.
12. Verify no persistent files or live state changed, then report exact test outputs and any concurrent-work caveat.

## Split-plane proposal, scheduler, and launcher audits

When a plan separates model-assisted proposal generation, authoritative scheduling, and user-side process launch, audit each plane independently. Similar names such as `native_dispatch.py` are not evidence for a scheduler unless the file actually performs tick ordering, claiming, and lease issuance.

1. **Proposal plane:** Require a proposal-specific lease/envelope, bounded deterministic payload, canonical source-state fingerprint, profile/board/policy binding, single-use/expiry semantics, and authoritative revalidation before any write. Generic launch-lease storage, policy helpers, or create/link primitives are only prerequisites. If first-party specify/decompose entry points combine model calls with writes, run those entry points only against a non-authoritative snapshot; apply accepted results to authority through lower-level native mutation functions.
2. **Scheduler plane:** Trace the whole tick: reclaim/health/runtime maintenance, dependency promotion, live auto-decompose toggle, ready/review ordering, global and per-profile caps, respawn guard, native claim, then lease issuance. Prove claim-to-lease recovery or atomicity. Do not call a monolithic native dispatcher when it also resolves workspaces or spawns under the wrong OS identity.
3. **Launcher plane:** Require a broker polling/report protocol, owner-profile Project resolution, safe directory/worktree containment, fixed executable, complete task environment/argv semantics, and reports for PID/workspace/branch/startup/exit. The launcher must not select or claim tasks and must not open authority; broker-side native setters record launcher-reported post-state.
4. **Prerequisite field audit:** Compare the upstream task/create contract with the broker protocol and wrappers. Missing `project_id`, workspace kind/path, branch, skills/model override, goal mode/turn budget, run/claim, tenant, or session fields can make a launcher impossible even when the launcher files themselves are the named later task.
5. **Lease fail-closed probe:** In a temporary root, create a lease already past expiry, list consumable leases, and attempt its CAS transition. Acceptance requires the expired lease to be hidden or terminalized and transition denial. A state-only `WHERE id=? AND state=?` CAS is insufficient when expiry, lease kind, principal, board/task/run, and payload fingerprint are security boundaries.
6. **Cross-identity process control:** Native reclaim/timeout helpers may assume the DB owner can signal the worker PID. When scheduler and worker use different UIDs, require launcher-mediated terminate/acknowledge before authoritative requeue; otherwise a failed signal followed by DB reset can permit a duplicate live worker.
7. **Private-contract ledger:** Public-function-set pinning does not cover underscore helpers or adjacent modules such as proposal runners, profile/Project resolution, workspace helpers, and spawn builders. Record exact origin, signature, and—when behavior is copied or directly imported—source/body digest. Mark monolithic functions that are parity references but forbidden to call in the split architecture.

For the next strict-TDD recommendation, choose one earliest boundary behavior only, preferably a real broker/client/temp-authority denial such as “expired proposal lease cannot be consumed” or “malformed proposal cannot mutate authority.” State the RED assertion, expected stable error, terminal lease state, and proof of zero native mutation; do not jump to downstream scheduling or spawning.

## Output shape

Use this order:

1. **Audit outcome** — overall go/no-go and canonical test result.
2. **Task matrix** — every requested task, exact evidence, exact gaps.
3. **Current cutover blockers** — preflight pass/fail/unknown table.
4. **Outstanding approval gates** — ordered gate chain.
5. **Safe pre-approval work** — source/staging work versus forbidden live actions.
6. **Files/issues** — explicit no-change statement and concurrent writer or evidence limitations.

## Pitfalls

- Do not call a task complete because a schema table or helper exists; require the task's public behavior and named tests.
- Do not let “all tests pass” imply coverage for absent test directories or uncollected acceptance bullets.
- Do not run the native read path against a protected live database when that read can migrate or write WAL metadata.
- Do not race a concurrent writer or treat their dirty changes as yours.
- Do not collapse distinct approvals into one generic “needs approval.”
- Do not state that cutover approval is ready when the shadow exit gate, rollback restore, custom policy, binding decision, or backup-health decision is unresolved.
