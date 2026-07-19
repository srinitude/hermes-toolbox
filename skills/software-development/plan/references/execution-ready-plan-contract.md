# Execution-Ready Plan Contract

`SKILL.md` owns plan-mode boundaries and requires this file for every plan. This file owns the rules and mechanical quality gate. `templates/execution-ready-plan.md` owns the exact layout. `templates/completion-report.json` owns the machine-readable closeout schema. `scripts/validate_completion_report.py` owns its mechanical validator. Load all four files before drafting, and return to `SKILL.md` before saving.

`PD-004`: `templates/execution-ready-plan.md` owns the reusable header, matrices, task layout, command contract, gate table, and final report layout. Load it for every plan. This reference owns the rules that govern those fields, and the template links back here.

`PD-005`: `templates/completion-report.json` owns the machine-readable whole-plan completion schema. Load it for every plan. Its `_meta` object names this contract as its governing reference.

`PD-006`: `scripts/validate_completion_report.py` owns the dependency-free PASS or BLOCKED check for that schema. Load and run it for every plan. Its module docstring links to `SKILL.md` and this contract.

## Applicability

- Use the full contract for every plan, including work that first appears simple.
- The same contract applies whether execution is manual, delegated, or done by the planner later.
- The plan must stand alone for a skilled implementer with no prior chat or codebase context.
- Every contract section must appear in the plan or be marked `N/A` with a concrete reason.
- Don't leave `TODO`, `TBD`, vague placeholders, or hidden choices in a ready plan.
- If a material fact can't be verified, mark the plan `BLOCKED` and turn that fact into a pre-flight discovery gate.
- Keep each plan file under 200 lines. Use compact tables first. If detail still won't fit, create a plan-owned reference and record a `PD-###` row with its path, owner, load trigger, and backlink.

## Source inventory

Record versioned official docs and local context files that govern the change.

- Trace every named symbol to its definition and relevant usages before prescribing an edit.
- Inspect neighboring implementations, tests, manifests, task runners, CI, and deployment files that constrain the change.
- Mark each source `verified`, `assumed`, or `unknown`. An unknown source that can change the design blocks the affected task.
- Record what each source proves. A path, URL, or command without a factual claim isn't enough.
- For cross-component work, record current and target control flow, data flow, ownership, trust boundaries, and compatibility transitions.
- For platform, version, feature-flag, or configuration differences, enumerate the supported matrix and identify every changed cell.
- Record working directory, toolchain and lockfile versions, required services, permissions, test data, environment variables by name, and local, CI, staging, and production differences that affect execution.

## Requirement and decision rules

- Give each requirement and acceptance criterion a stable ID.
- Map every requirement to one implementing task, one or more validators, and an evidence target.
- Don't add a task or validator that serves no requirement.
- State each acceptance criterion as a binary observable result.
- Record each material choice, alternatives rejected, evidence, and the task or gate affected.
- Use a material assumption as a pre-flight gate, not as hidden executor judgment.
- Mark each validator as task-local or whole-plan.

## Task rules

- Write tasks in dependency order. Mark safe parallel work and serialize shared files, state, data, or external resources.
- Keep each task to one focused action, normally 2 to 5 minutes of active work.
- Each numbered step performs one action and names its expected state change.
- State preconditions, inputs, outputs, interfaces, invariants, side effects, approval needs, local completion, and handoff state.
- Name the failure signal, immediate response, rollback, cleanup, retry limit, owner, and exact resume point.
- One task's evidence proves only that task. It doesn't prove the whole plan.

## Files

List each created, modified, renamed, or deleted path with the symbol or section and reason. Name every caller, test, fixture, schema, generated artifact, configuration entry, and document that must stay in sync. If line numbers may drift, pair them with a stable symbol or heading. Include applicable API docs, migration guides, examples, changelog or release notes, accessibility and localization work, dashboards, alerts, and runbooks.

## Implementation detail

Include full, copy-pasteable code or a precise diff for small edits whose surrounding code was inspected. For larger edits, state exact signatures, control flow, data shape, invariants, error behavior, and integration points. If the code shape can't be known before execution, specify signatures, invariants, and a discovery gate. Don't invent code.

Use DRY, YAGNI, and vertical TDD. Don't add speculative behavior or unrelated cleanup.

## TDD sequence

For each user-facing behavior slice:

1. RED: write one user-facing test and run it until it fails for the expected missing behavior.
2. Expected failure: [exact error, assertion, or invariant that proves RED]
3. GREEN: make the smallest change that passes the focused test.
4. REFACTOR only while green, then run focused checks before broader regression checks.
5. Add the next behavior slice only after the prior slice is green.

State edge, boundary, error, compatibility, and negative cases. Use real interfaces and services when the project permits them. If a mock is unavoidable, explain what integration proof covers the mocked boundary.

## Command and evidence rules

For every command, name the working directory, prerequisites, expected exit status, pass signature, fail meaning, and captured evidence.

- Pass condition: [observable invariant, output pattern, status, or artifact]
- Give every machine evidence record a kind, check names, a reciprocal producing validator, covered structured IDs, a normalized file path inside the completion-report directory, and SHA-256. Reject absolute paths, escapes, symlink escapes, oversized files, and unreadable paths. Require the evidence JSON to exactly match its metadata and producer's scope, status, exit codes, and actual result.
- Whole-plan `check_evidence` may use only evidence produced by a whole-plan validator, naming that check, with a kind allowed for that check. Task-local evidence never proves whole-plan completion.
- The completion report must match the schema's exact top-level and nested keys, ID formats, enums, links, and file contracts. Reject omitted, extra, malformed, unknown, orphan, duplicate, nonreciprocal, or unused records.
- Use an invariant or output pattern for dynamic results. Don't invent an exact count or message.
- Compare against a recorded baseline when the repository has unrelated failures. Only new failures block unless project rules say otherwise.
- Run checks from narrowest to broadest: focused behavior, affected module, integration boundary, then required full suite.
- Name timeouts, retry limits, environment variables by name, fixtures, services, and cleanup steps.
- Never paste secrets or credential values into the plan or evidence.
- The final task must run an available JSON parser that exits nonzero unless `plan.status` is `PASS`, every `checks` value is true, `blockers` is empty, every requirement is `PASS` or has a complete waiver, every task, validator, gate, and cleanup entry is `PASS`, every risk is mitigated or accepted, and every required artifact exists.

## Risk and recovery rules

For each material risk, state prevention, detection, response, rollback, owner, and the task or gate that handles it.

Cover applicable data loss, migrations, compatibility, concurrency, idempotency, security, privacy, external outages, rate limits, performance, resource use, partial writes, stale caches, rollout, restart, cleanup, and rollback. Mark each item `N/A` with a reason when it doesn't apply.

Put irreversible or externally visible actions behind approval gates. Name backups, checkpoints, restoration steps, and the check that proves recovery works.

For rollout work, name the feature flag, stage or canary sequence, compatibility window, health signals, monitoring period, abort thresholds, rollback or roll-forward path, and decision owner.

For security, privacy, or authorization work, record assets, trust boundaries, permissions, data classification and retention, abuse cases, audit evidence, and required review.

For performance-sensitive work, set measurable latency, throughput, memory, storage, and cost budgets with the load shape and evidence method.

For data or schema migrations, define backup, dry run, batching, lock and downtime behavior, forward and backward compatibility, partial-failure recovery, rollback limits, and post-migration verification.

## Whole-plan closeout

The final validation task must:

1. Inventory actual changed files and map each one to an approved task.
2. Re-run every required full-scope test, lint, type, build, security, schema, docs, packaging, and deployment check.
3. Exercise cross-task integrations plus negative, recovery, migration, rollback, restart, and cleanup paths that apply.
4. Reconcile every requirement, acceptance criterion, risk, and validator with fresh evidence.
5. Run an independent spec review before the quality review when review tools are available.
6. Create a plan-specific machine report from `templates/completion-report.json`. Create the human JSON report with exactly the machine report's plan ID, status, checks, and check-evidence map, then hash and reference it from the machine report.

Overall PASS requires every non-waived requirement and acceptance criterion to pass. Any failed or unavailable required check makes the result BLOCKED. A waiver applies only to requirements and must name the approver, exact requirement scope, reason, expiry or revisit condition, and remaining risk. Reject unknown or unused waiver records and waiver IDs on passing requirements.

## Plan quality gate

The plan is READY only when all checks pass:

- Every requirement, acceptance criterion, risk, residual-risk record, task, validator, and evidence record has a unique ID and complete reciprocal links.
- Every path, symbol, command, version, and source is verified or explicitly blocks the affected work.
- Every task has preconditions, exact targets, ordered actions, command contracts, failure recovery, rollback, local completion, evidence, and handoff state.
- Every validator has a binary pass condition, fail condition, scope, method, and evidence location.
- Task-local checks and whole-plan checks are separate.
- Dependencies are ordered, safe parallel work is marked, and no cycle remains.
- Material assumptions and open questions are resolved, accepted, or blocking.
- Risks cover prevention, detection, response, rollback, and ownership.
- No ready section contains a placeholder, invented output, hidden choice, or unexplained `N/A`.
- The final closeout can be filled from tool output without reconstructing intent.
- The plan and each companion file meet the active Markdown size and voice rules.
