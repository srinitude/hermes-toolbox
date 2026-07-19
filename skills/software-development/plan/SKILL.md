---
name: plan
description: "Use when the user wants a plan without execution."
version: 3.0.0
author: Kiren Srinivasan
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, plan-mode, implementation, workflow, design, documentation]
    related_skills: [global-coding-policy, subagent-driven-development, test-driven-development, requesting-code-review]
---

# Plan Mode

## Outcome

Use this skill when the user wants a plan instead of execution.

A plan is ready only when an executor can act without routine rediscovery and a validator can decide PASS or BLOCKED from named evidence. If an executor or validator must guess, the plan isn't ready.

The plan must reduce risk before execution starts. It must also turn completion into a set of explicit checks rather than a fresh reasoning task.

## Plan-only boundary

For this turn, stay in plan mode.

- Don't implement code or change runtime state.
- Don't edit project files. Write only the plan and its plan-owned companions under `.hermes/plans/`, the plan-owned completion-report template under `.hermes/reports/<plan-slug>/`, and disposable validation fixtures under that report directory.
- Don't run project-mutating commands, commit, push, publish, deploy, perform external actions, or cause external side effects. Don't call external write APIs.
- Use read-only tools to remove uncertainty before drafting.
- Don't expose secrets, credential values, or unreviewed sensitive data in plans or evidence.

## Mandatory contract and ownership

Before drafting every plan, load `references/execution-ready-plan-contract.md`, `templates/execution-ready-plan.md`, `templates/completion-report.json`, and `scripts/validate_completion_report.py` with `skill_view`, then apply all four. A section may be marked `N/A` only with a concrete reason.

`PD-003`: `references/execution-ready-plan-contract.md` owns the detailed planning rules and mechanical quality gate. Load it for every plan. This `SKILL.md` owns plan-mode boundaries, discovery, save behavior, and the requirement to load that reference. The reference links back here.

`PD-004`: `templates/execution-ready-plan.md` owns the exact header, matrices, task layout, command contract, gate table, and final report layout. Load it for every plan together with the contract reference. The template links back to both owners.

`PD-005`: `templates/completion-report.json` owns the machine-readable whole-plan completion schema. Load it for every plan and require the final validation task to create a plan-specific report from it. Its `_meta` object links back to the contract reference.

`PD-006`: `scripts/validate_completion_report.py` owns the dependency-free mechanical PASS or BLOCKED check for that report. Load it for every plan and require the final validation task to run it. The script's module docstring names its owner as this `SKILL.md` and links to the contract reference.

`PD-007`: The plan template is above the 150-line disclosure gate because its always-needed Hermes handoff header, rollout and approval gates, and validator register must remain inline. Keep new branch-specific detail in the contract reference or another owner-appropriate support file, and preserve this backlink.

## Discovery before drafting

Inspect requirements, acceptance criteria, constraints, current behavior, relevant code, tests, manifests, and governing docs before drafting.

- Read the active project context and every narrower rule file that applies.
- Trace every named symbol to its definition and relevant usages before prescribing an edit.
- Inspect neighboring patterns, callers, tests, schemas, task runners, CI, deployment, and rollback paths.
- Record the exact paths, symbols, commands, versions, and official sources that informed the plan.
- Label each material statement as verified, assumed, or unknown.
- If read-only discovery can settle an uncertainty, inspect first instead of asking.
- For a bare `/plan`, use the current conversation task.
- Ask one concise question only when a material choice can't be retrieved and would change the plan.
- If a material fact remains unknown, mark the affected work BLOCKED and add a pre-flight discovery gate. Don't fabricate detail.

## Required plan content

A plan must resolve every material choice before marking itself READY. If the user hasn't chosen a product, safety, or scope tradeoff that discovery can't settle, mark it BLOCKED and name the decision gate.

Every plan includes:

- Header with goal, user-visible outcome, non-goals, approach, stack and versions, constraints, source snapshot, assumptions, approval boundaries, and status.
- A source inventory that separates observed facts from assumptions and unknowns.
- A closed requirement-to-evidence matrix with stable IDs for requirements, acceptance criteria, tasks, risks, and validators.
- A decision log for material choices and rejected alternatives.
- A dependency-ordered task graph with explicit inputs, outputs, interfaces, side effects, and handoff state.
- A risk, rollout, recovery, and rollback contract.
- Task-local validation and a separate whole-plan closeout.

No requirement may lack an implementing task and validator. No task or validator may lack a requirement it serves.

## Task contract

Write tasks in dependency order and mark safe parallel work explicitly.

- Keep each task to one focused action, normally 2 to 5 minutes of active work.
- Each numbered step performs one action and names its expected state change.
- Name exact paths, actions, symbols, and line anchors when they were observed.
- State prerequisites, inputs, outputs, contracts, invariants, side effects, and approval needs.
- Code tasks need exact file and symbol targets, user-facing test cases, and focused plus broader verification commands.
- Use vertical TDD: RED with the expected failure reason, minimal GREEN, REFACTOR while green, then broader checks.
- Within verified dependency constraints, include applicable tasks in this order: setup or infrastructure, core behavior, edge cases, integration, then cleanup and documentation. Mark an omitted category `N/A` with a concrete reason.
- Name failure signals, immediate response, rollback, cleanup, retry limit, and exact resume point.
- Define binary local completion and the evidence handed to dependent tasks.
- Include commit checkpoints only when the user or repository rules authorize them. When authorized, place one after every completed task.

- Give every plan, baseline, requirement, task, risk, residual-risk record, gate, validator, changed file, artifact, evidence record, cleanup entry, review, and human report a stable ID, then cross-link those IDs in the plan and completion report. Use `PLAN-###`, `BASE-###`, `REQ-###`, `TASK-###`, `RISK-###`, `RESIDUAL-###`, `GATE-###`, `VAL-###`, `FILE-###`, `ART-###`, `EVID-###`, `CLEAN-###`, `REVIEW-###`, and `REPORT-###`.
- Declare task-to-artifact and task-to-evidence links in each task's outputs and handoff. Declare gate-to-task or gate-to-validator links in the gate trigger or resume point. The final changed-file inventory and machine report must use the same IDs.
- Plan-owned validation fixtures are generated per plan from the completion schema. Don't copy the fixtures from this skill-hardening task.
- One task's proof validates only that task. It never proves the full plan.

## De-risk execution

For each material risk, state prevention, detection, response, owner, and the task or gate that handles it.

Cover every applicable boundary: data loss, migrations, partial writes, compatibility, concurrency, idempotency, security, privacy, secrets, external services, rate limits, performance, resource use, rollout, restart, stale caches, cleanup, and rollback.

- Name backups, checkpoints, restoration commands, and proof that recovery works.
- Put irreversible or externally visible actions behind explicit approval gates.
- Define pre-flight, revision, escalation, and abort gates with trigger, failure behavior, owner, retry limit, and resume point.
- Turn material assumptions into verified facts, accepted decisions, or blocking gates before execution.
- Record safe parallel work and serialize tasks that share files, state, data, or external resources.

## Mechanical validation

Every acceptance check must name scope, method, expected result, failure condition, and evidence.

- Prefer commands, parsers, schemas, status codes, hashes, counts, and observable invariants over subjective review language.
- For dynamic output, specify a stable pattern or invariant instead of an invented exact message or count.
- State the working directory, prerequisites, timeout, expected exit status, pass signature, fail meaning, and evidence location for each command.
- Compare against a recorded baseline when unrelated failures already exist. Only new failures block unless governing rules say otherwise.
- Run checks from focused behavior to affected module, integration boundary, and required full suite.
- Make the final task inventory actual changes and reconcile every requirement, acceptance criterion, risk, and validator with fresh evidence.
- Require independent spec review before quality review when review tools are available.
- Report final status as PASS or BLOCKED with commands, exit codes, artifacts, evidence records, waivers, and residual risks. During planning, create the plan-owned report template under `.hermes/reports/<plan-slug>/completion-report.json` from `templates/completion-report.json`; keep its truthful initial status BLOCKED. Require the final execution task to replace placeholders with fresh evidence, record each evidence kind, check names, reciprocal producing validator, covered structured IDs, normalized path inside the report directory, and SHA-256, bind the evidence JSON exactly to the producer's result, make the human JSON report exactly match the machine report's plan ID, status, checks, and check-evidence map, close every required gate and risk, account for every changed file and artifact, complete cleanup, and run `scripts/validate_completion_report.py` against it.

Whole-plan PASS requires every non-waived acceptance criterion to pass, every required artifact to exist, every blocker to be closed, and every required full-scope check to pass. Component-only evidence must not be described as whole-plan proof.

## Writing rules

- Keep the plan self-contained and as detailed as grounded evidence allows. Use compact tables before moving branch-specific detail to linked plan-owned files.
- Include exact code or diffs for small, grounded edits. For larger work, specify signatures, data shapes, control flow, errors, and invariants.
- Use DRY, YAGNI, and vertical TDD. Don't add speculative behavior or unrelated cleanup.
- Don't leave `TODO`, `TBD`, vague placeholders, hidden choices, or unexplained `N/A` entries in a ready plan.
- Use clear, plain English in this skill, its reference, and every generated plan.
- Keep each governed Markdown file under 200 lines. Start progressive disclosure at 150 lines or before the next addition would cross the limit. A parent may remain above 150 lines only when every remaining line is always needed and each moved detail has an owner, load trigger, and backlink.
- Record every plan-specific move as `PD-###` with destination, owner, load trigger, and backlink.

## Save and verify

Save the deliverable with `write_file` under `.hermes/plans/` in the active workspace.

- Use `.hermes/plans/YYYY-MM-DD_HHMMSS-<slug>.md` unless the runtime gives an exact target path.
- Treat relative plan paths as relative to the active backend workspace.
- Re-read the saved plan and every companion file.
- Verify frontmatter or required header fields, line limits, links, IDs, cross-references, task ordering, gate behavior, and evidence contracts.
- Run the reference's plan quality gate. Validate every named plan structure and companion schema with an available parser or checker. Generate one passing fixture and negative fixtures for forged checks, omitted or extra keys, malformed scalar, collection, ID, link, and encoding types, boolean exit codes, broken reciprocal links, orphan or duplicate nodes, invalid status or scope, task-local evidence used for whole-plan checks, missing check names, noncanonical evidence or human-report content, absolute, traversal, symlink-escape, malformed, missing, or mismatched evidence paths and hashes, failed gates, incomplete or uncovered risks and residual risks, unexpected files, missing artifacts, incomplete cleanup, and unknown, unused, or invalid waiver scope. Run `scripts/validate_completion_report.py` on each fixture and the plan-owned BLOCKED template. The final execution task must later run it on the filled plan-specific report with evidence for every true check. Revise until all planning checks pass or mark the plan BLOCKED with exact failures.
- Use a read-only independent reviewer for high-risk or multi-step plans when delegation is available. Review the ready plan, completion-report template, and quality-gate evidence before handoff. Limit revision to 3 cycles, then escalate.

After saving, report the path, planned scope, status, and any blocker. Offer to execute through `subagent-driven-development` unless the user asked for plan-only output with no follow-up question.

## Execution handoff

Every saved plan starts with `> **For Hermes:** Use subagent-driven-development to implement this plan task-by-task.`

The completion report declares every structured collection named by `templates/completion-report.json`. Every referenced ID must resolve, reciprocal links must agree, aggregate evidence must come from a whole-plan validator and cover the claimed structured IDs, and the validator must reject every orphan, unknown, malformed, or unused link.

When execution is requested, dispatch a fresh `delegate_task` per task with the complete task contract and prior evidence. Review spec compliance first, then code quality. Fix and re-run each failed gate before continuing. Don't advance while either review has an open issue.

## Common failures

- Invented paths, APIs, commands, versions, or expected outputs.
- Tasks that hide several edits or leave an executor to choose the design.
- Validation that says only "works", "looks right", or "tests pass".
- A test command with no expected failure reason, pass invariant, scope, or evidence.
- Task-local proof presented as whole-plan completion.
- Risks listed without prevention, detection, response, rollback, and ownership.
- Material assumptions hidden in prose instead of resolved or gated.
- A final status that ignores unavailable required checks or unexplained waivers.

## Verification checklist

- [ ] The mandatory contract, plan template, completion-report schema, and report validator were loaded, and every section was used or justified as `N/A`.
- [ ] Read-only discovery grounded all material paths, symbols, commands, versions, and sources.
- [ ] Every requirement has an implementing task, validator, and evidence target.
- [ ] Every task has preconditions, exact actions, failure recovery, rollback, local completion, and handoff state.
- [ ] Every risk has prevention, detection, response, ownership, and a gate or task.
- [ ] Every validator has a binary pass condition, fail condition, scope, method, and evidence location.
- [ ] Task-local checks and whole-plan checks are separate.
- [ ] The final closeout proves all requirements, writes and validates the completion report, and reports PASS or BLOCKED without inference.
- [ ] No placeholders, invented facts, hidden choices, or unexplained exclusions remain in a ready plan.
- [ ] The saved plan and companions were re-read and meet active size, link, voice, and path rules.
