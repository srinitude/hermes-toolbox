# Execution-Ready Plan Template

Load this template for every plan together with `references/execution-ready-plan-contract.md` and `templates/completion-report.json`. `SKILL.md` owns plan-mode boundaries. The reference owns the rules and quality gate. This file owns the exact plan layout and links back to both owners.

`PD-004`: This template owns the reusable header, matrices, task layout, command contract, gate table, and final report layout. Load it for every plan. The reference keeps the rules that govern each field.

Use `templates/completion-report.json` as the machine-readable form of the whole-plan completion report.

Don't omit a section. If it doesn't apply, write `N/A` with a concrete reason.

## Header

```markdown
# [Outcome] Implementation Plan

**Status:** READY | BLOCKED

> **For Hermes:** Use subagent-driven-development to implement this plan task-by-task.

**Goal:** [one observable end state]
**User-visible outcome:** [what changes for the user or operator]
**Non-goals:** [explicit exclusions]
**Approach:** [chosen architecture, integration seams, and why it fits the observed codebase]
**Stack and versions:** [observed languages, frameworks, tools, and version constraints]
**Constraints:** [scope, safety, compatibility, time, data, and approval limits]
**Current-state evidence:** [paths, symbols, commands, docs, and observed behavior]
**Execution environment:** [working directory, platform, toolchain, services, and required access]
**Assumptions:** [verified, accepted, or blocking]
**Open questions:** [resolved, accepted, or blocking choices]
**Approval boundaries:** [actions that need user or operator approval]
**Plan status reason:** [why the plan is READY or BLOCKED]
```

## Source inventory

| Source | Exact path, symbol, command, or URL | Status | What it proves |
| --- | --- | --- | --- |
| [source type] | `[exact source]` | verified | [specific fact] |

## Requirement and evidence matrix

| ID | Requirement or acceptance criterion | Source | Implementing task | Validator | Evidence |
| --- | --- | --- | --- | --- | --- |
| `REQ-001` | [binary statement] | [user, issue, doc, or rule] | `TASK-001` | `VAL-001` | [artifact or output] |

## Decision log

Record each material choice, alternatives rejected, evidence, and the task or gate affected.

| ID | Decision | Evidence | Rejected option and reason | Affected task or gate |
| --- | --- | --- | --- | --- |
| `DEC-001` | [chosen behavior] | [verified source] | [option and concrete reason] | `TASK-001` |

Use a material assumption as a pre-flight gate, not as hidden executor judgment.

## Risk, rollout, and recovery matrix

| ID | Hazard or dependency | Prevention | Detection | Response and rollback | Owner or task |
| --- | --- | --- | --- | --- | --- |
| `RISK-001` | [concrete failure mode] | [control] | [signal] | [bounded response] | `TASK-001` |

## Rollout plan

| Phase or `N/A` reason | Owner | Entry gate | Health signal and observation window | Abort or rollback action | Exit gate |
| --- | --- | --- | --- | --- | --- |
| [canary, stage, production, or concrete N/A] | [owner] | `GATE-###` | [metric, threshold, and duration] | [trigger and exact response] | `GATE-###` |

## Execution graph

| Task ID | Depends on | Safe parallel with | Shared state | Start condition |
| --- | --- | --- | --- | --- |
| `TASK-001` | [task IDs or none] | [task IDs or none] | [files, data, service, or none] | [verified precondition] |

## `TASK-001`: [One observable change]

**Objective:** [one observable state this task creates]
**Covers:** `REQ-###`, `AC-###`, `RISK-###`
**Depends on:** [task IDs or `none`]
**Local completion:** [binary task result, not whole-plan success]

**Preconditions:**
- [state, permission, dependency, backup, or prior evidence]
- Pre-flight failure: [stop condition, response, and exact resume point]

**Inputs and outputs:**
- Input: [file, schema, API, data, or decision]
- Output: [changed behavior, artifact, or state]

**Files and symbols:**
- Create: `exact/path` at `[owner or module]`
- Modify: `exact/path:line-range` in `ExactSymbol`
- Delete or rename: `exact/path` with all known callers listed

**Contracts and invariants:**
- Interface before and after: [signature, schema, route, event, or CLI]
- Invariants that must remain true: [compatibility, ordering, security, data]
- Side effects: [filesystem, network, database, process, external service]

**Steps:**
1. [one action with exact target] -> [expected observable state change]
2. [one action with exact target] -> [expected observable state change]
3. [one action with exact target] -> [expected observable state change]

**Behavior and TDD:**
| Case | User-facing behavior | Test target | Expected result |
| --- | --- | --- | --- |
| `CASE-001` | [input and condition] | `exact/test::name` | [observable result] |
- RED command: `exact focused command`
- Expected failure: [exact error, assertion, or invariant that proves RED]
- GREEN target: [smallest implementation change]
- Focused pass: `exact focused command` and [pass invariant]
- Broader regression: `exact affected or full-suite command`

**Verification:**

| ID | Scope | Command or inspection | Expected | Failure means | Evidence |
| --- | --- | --- | --- | --- | --- |
| `VAL-001` | task | `exact command` | exit 0 and [invariant] | [specific gap] | [saved output] |

- Pass condition: [observable invariant, output pattern, status, or artifact]

**Failure and recovery:**
- Owner and retry limit: [responsible owner and maximum attempts]
- Failure signal: [observable result]
- Immediate response: [stop, revise, restore, or escalate]
- Checkpoint or backup: [path, ID, command, or N/A reason]
- Rollback: [exact command or restoration procedure]
- Restoration proof: [validator and evidence that recovery worked]
- Cleanup: [temporary state, partial writes, processes, or N/A reason]
- Resume from: [step, gate, or clean checkpoint]

**Handoff:**
- Evidence produced: [path, output, diff, report, or hash]
- State passed to next task: [facts the next task may rely on]

## Gate table

| ID | Type | Trigger or linked task | Failure behavior | Owner and validator | Evidence and resume point |
| --- | --- | --- | --- | --- | --- |
| `GATE-001` | Pre-flight | Missing precondition for `TASK-001` | Block before mutation | [owner], `VAL-001` | `EVID-001`; retry after proof |
| `GATE-002` | Revision | `TASK-001` misses a criterion | Return exact gaps | Maximum 3, [owner] | `EVID-002`; re-run check |
| `GATE-003` | Escalation | Material choice or stalled revision | Ask user with evidence | [owner], no automatic retry | `EVID-003`; chosen branch |
| `GATE-004` | Abort | Safety boundary fails | Stop and restore when safe | [owner], no automatic retry | `EVID-004`; named checkpoint |
| `GATE-005` | Approval | Irreversible or externally visible action in `TASK-001` | Block until the named approver grants the scoped action | [approver], `VAL-001` | `EVID-005`; approval record and exact resume point |

## Whole-plan completion report

**Overall status:** PASS | BLOCKED

| Item ID | Type | Linked task | Linked validators or gates | Status | Fresh evidence | Waiver |
| --- | --- | --- | --- | --- | --- | --- |
| `REQ-001` | requirement | `TASK-001` | `VAL-001` | PASS | `EVID-001` | none |

| Validator ID | Scope | Working directory and prerequisites | Command or method | Timeout | Expected result and pass signature | Failure condition | Baseline comparison | Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `VAL-001` | whole plan | `[cwd]`; [prerequisites] | `exact command` | [duration] | exit 0 and [invariant] | [specific failure] | [baseline ID or none] | `EVID-001` | PASS |

| Evidence ID | Kind | Check names | Producing validator and scope | Covered structured IDs | Normalized report-local JSON file | SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `EVID-001` | report | [exact aggregate check names] | `VAL-001`; whole plan | `PLAN-001`, `REQ-001`, `VAL-001`, [other claimed IDs] | `evidence/whole-plan.json`; content exactly binds metadata and producer result | [fresh hash] |

**Machine report and human report:** [machine report path plus a normalized report-local human JSON path, `REPORT-###`, matching status, fresh SHA-256, and exact plan ID, status, checks, and check-evidence content]

**Blockers:** [empty for PASS; otherwise blocker ID, owner, trigger, and resume condition]

**Changed-file inventory:** [every actual change mapped to an approved task]
**Artifacts and hashes:** [paths and hashes when identity matters]
**Rollback and cleanup:** [result of applicable recovery checks]
**Waivers:** [approver, scope, reason, revisit condition, remaining risk]
**Residual risks:** [accepted risks and owner]
**Final status reason:** [mechanical reason for PASS or BLOCKED]
