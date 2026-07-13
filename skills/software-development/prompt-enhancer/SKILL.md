---
name: prompt-enhancer
description: "Use when a user wants a prompt improved, clarified, made safer, or tailored to the current conversation. Produces context-aware prompts with explicit Hermes write-safety boundaries, then executes the enhanced prompt when safe."
version: 0.1.32
author: Kiren Srinivasan
license: Apache-2.0
metadata:
  hermes:
    tags: [prompting, safety, hermes-agent, workflow, planning]
    related_skills: [plan, hermes-agent]
---

# Prompt Enhancer

## Overview

Use this skill to turn a rough user request into a stronger prompt that is specific, context-aware, outcome-driven, and safe for Hermes Agent to execute. After successfully enhancing and verifying the prompt, execute the enhanced prompt unless the user explicitly requested prompt text only or execution is blocked by missing context or unsafe side effects requiring clarification.

The enhanced prompt should preserve the user's intent while making the task easier to verify. It should name the desired outcome, relevant context, constraints, source-of-truth checks, allowed write surfaces, prohibited write surfaces, and the validation threshold that proves success.

Session continuity is part of the enhanced prompt by default. Unless the user explicitly asks to start over, reset context, or replace prior work, append a continuity instruction to the enhanced prompt: "Continue all previous and existing work within this session, using the accumulated session context and active task list. Treat this prompt as an additional steering instruction, not a reset, while also executing the new request."

<!-- universal-freshness-minimal-change-contract:start -->
## Universal Freshness and Minimal-Change Contract

Apply this contract to every enhanced prompt, including answer-only, plan-only, read-only, and execute modes:

1. **Anchor time live.** Before making choices, obtain the current date, time, and timezone from an available live system tool; never infer them from model knowledge. Include the concrete runtime value in the enhanced prompt. Refresh it if a long-running task crosses a date boundary or the decision time materially affects the answer.
2. **Ground changing facts.** Classify the task’s facts and choices as stable or time-sensitive. Treat versions, prices, APIs, policies, laws, schedules, availability, compatibility, rankings, recommendations, and recent events as time-sensitive unless proven otherwise. Validate them against current first-party or authoritative live sources, comparing publication and effective dates when relevant. A current date is context, not evidence and does not repair a model knowledge cutoff. If live evidence is unavailable, label the uncertainty or blocker instead of guessing.
3. **Apply YAGNI.** Implement only behavior required by the current objective and explicit acceptance criteria. Treat requests justified only by hypothetical future needs as non-goals even when listed by the user. Do not add a future-facing seam, hook, plugin point, or compatibility layer unless a present concrete consumer or current externally observable acceptance requirement needs it; wrapping today’s implementation solely to anticipate a future caller is insufficient. Exclude speculative features, extension points, compatibility layers, dependencies, configuration, files, refactors, and optional polish that are not needed now.
4. **Search before adding.** Inspect the smallest relevant surface for existing helpers, patterns, dependencies, tests, and documentation before creating anything. Reuse compatible existing code directly and extend the nearest existing abstraction only when the current task requires it. Do not create a generic abstraction solely for possible future reuse.
5. **Make the smallest coherent diff.** Prefer the least broad, reviewable change that fully solves the task, preserves unrelated behavior and user changes, and keeps validation honest. Minimize changed files and lines only after correctness, clarity, safety, and maintainability; do not line-golf, hide coupling, weaken tests, or force reuse across incompatible responsibilities.
6. **Prove necessity.** Map every changed file, hunk, new dependency, and validation artifact to an acceptance criterion or required proof. Remove anything unmapped. If correctness requires a broader change, state why the narrower alternatives fail before proceeding.

Completion criterion: the enhanced prompt has a live time anchor, a resolved freshness strategy, explicit non-goals, identified reuse candidates, a bounded diff surface, and no unproven or speculative scope.
<!-- universal-freshness-minimal-change-contract:end -->

<!-- honcho-persistent-memory-contract:start -->
## Honcho and Persistent Memory Context Contract

This contract amends Prompt Enhancement Procedure steps 1, 5, and 6 and the Verification Checklist. Apply it whenever memory context could change the objective, assumptions, safety boundary, personalization, or result, and whenever a task creates, reads, updates, or deletes memory.

### Context intake and source priority

1. Treat the current user message and directly inspectable primary sources as authoritative for the current task. Built-in memory and Honcho are contextual evidence, not proof that an external source still has the same state.
2. Start with the built-in MEMORY/USER snapshot and any Honcho context already injected into the session. In `hybrid` or `context` recall mode, do not re-fetch facts already present merely to be thorough.
3. If relevant context is missing and Honcho tools are available, use the least expensive sufficient read: `honcho_profile` for a quick peer-card fact; `honcho_search` for a query-curated representation and card—do not treat it as raw-source excerpts in the current Hermes implementation; `honcho_context` for the current summary, representation, card, and recent messages; `honcho_reasoning` only when synthesis across evidence is actually required. Choose the lowest sufficient `reasoning_level`.
4. In `tools` mode, retrieve required memory explicitly. In `context` mode, tools are unavailable; use injected context or report a blocker. Never invent a Honcho result or assume Honcho is active because this skill mentions it.
5. Target `peer="user"` for facts about the human and `peer="ai"` for profile-specific AI self-knowledge. Use an explicit peer ID only when the current workspace/identity mapping is known and the task requires it.
6. Surface contradictions between the current user, built-in memory, Honcho, session history, and direct sources. Current explicit user correction wins for the current task; repair durable stores only through the CRUD rules below.

### CRUD routing

- **Create:** Use built-in `memory` for compact durable facts that should be available in future Hermes sessions, but only when that target's prompt injection is enabled: `target="user"` for identity/preferences/style and `target="memory"` for stable environment facts, conventions, and reusable lessons. The shared store/tool may still accept writes when a target's injection is disabled, so do not equate write success with future prompt inclusion. Use `honcho_conclude(conclusion=..., peer=...)` for a specific factual persistent conclusion that belongs in Honcho. Do not store secrets, raw dumps, one-off task state, progress logs, completed-work diaries, transient paths, speculative inferences, or facts likely to be stale within a week.
- **Read:** Built-in memory has no read action; use the injected session-start snapshot. Successful built-in writes return status, target, usage, and entry count, not live entries; the current Hermes tool has no successful post-write list/read operation. Use the Honcho read ladder above. Prefer `session_search` over durable memory when the question is “what did we discuss?” and inspect a user-supplied direct source before treating session or memory history as current evidence.
- **Update built-in memory:** Use `replace` with a short unique `old_text`. If several edits or capacity consolidation are needed for one target, send one atomic `operations` batch so removals/replacements and additions are checked against the final character budget.
- **Update a Honcho card:** First read the card, merge the correction while preserving unrelated facts, then call `honcho_profile(card=[...], peer=...)` with the complete desired non-empty card. `set_card` overwrites the full card; `card=[]` is not a supported clear operation through the current Hermes handler. Do not use a whole-card overwrite when a new/corrective conclusion is sufficient.
- **Correct a Honcho conclusion:** As a Hermes safety policy, add a precise corrective conclusion so Honcho can process the contradiction asynchronously rather than deleting a non-PII conclusion merely because it is stale or wrong. This is a Hermes safety policy, not a Honcho backend guarantee of deterministic self-healing.
- **Delete built-in memory:** Use `remove` with a short unique `old_text`; use a batch when deletion and replacement must be atomic.
- **Delete a Honcho conclusion:** Under the current Hermes safety policy, use `honcho_conclude(delete_id=..., peer=...)` only for PII removal and only with a known conclusion ID; the Honcho backend API itself permits generic ID-based deletion. Pass exactly one of `conclusion` or `delete_id`. Current Hermes Honcho tools expose no conclusion-list/created-ID workflow, so exact conclusion CRUD read-back is unavailable through current Hermes tools. If the ID or exact proof is required, report the blocker and require a separately approved first-party Honcho UI/SDK/API path. Eventual representation/card changes are indirect evidence only. Do not claim that deleting one conclusion erases source messages, sessions, all derived context, or all copies of the information.

### Dual-store consistency and verification

1. Honcho is additive to built-in memory. A successful built-in `add` to `target="user"` may be mirrored asynchronously to Honcho, but mirroring is best-effort and non-atomic: it runs in an untracked daemon thread, can be dropped when Honcho is not session-ready, and has no cross-store retry or rollback. The current Honcho provider does not mirror built-in `replace`, `remove`, or `target="memory"` writes. When both stores must agree, plan and verify both operations explicitly; never assume automatic bidirectional synchronization or guaranteed eventual consistency.
2. Respect `memory.write_approval`; a staged write is not committed, and approved staged writes are not forwarded to the provider bridge by the current approval path. Prefer one batched built-in-memory call for multiple changes to the same target.
3. After a mutation, inspect the tool’s real response. For built-in memory, verify success, target, usage, and entry count; successful responses do not return entries, and prompt injection refreshes only in a new/rebuilt session when that target is enabled. For Honcho card updates, use the cheapest appropriate read-back and allow for documented asynchronous processing. For conclusion create/delete, Hermes tool success confirms only that the SDK call did not raise; exact conclusion-record read-back is blocked through current Hermes tools, and representation/card changes are indirect evidence only. Bounded retry is acceptable, fabricated success is not.
4. Do not perform a memory mutation solely to test this contract. Static/fresh-process contract validation and disposable fixtures are the default proof.

### Enhanced-prompt integration

When memory is relevant, add this section to the enhanced prompt:

```markdown
## Memory and Honcho Context
- Relevant injected context: [facts used, or none]
- Additional retrieval: [tool, peer, query, and why it was necessary, or none]
- Conflicts/freshness: [current-user/direct-source precedence and any unresolved contradiction]
- Memory action: [none | create | read | update | delete]
- Store and target: [built-in user | built-in memory | Honcho user peer | Honcho AI peer | explicit peer]
- Consent/approval: [write gate, PII deletion limitation, or not applicable]
- Read-back proof: [exact tool result required, next-session boundary, or blocker]
```

Completion criterion: the enhanced prompt uses all relevant available context without redundant calls; any memory mutation is necessary, correctly routed, privacy-safe, approval-aware, and paired with the best available read-back evidence or an explicit exact-readback blocker; unsupported Honcho update/delete semantics are reported as blockers rather than invented.
<!-- honcho-persistent-memory-contract:end -->

## When to Use

Use this skill when:

- The user asks to improve, rewrite, enhance, harden, or optimize a prompt.
- The prompt needs to account for the current conversation context.
- The user wants Hermes to work inside or around the Hermes Agent codebase or profile data.
- The prompt may cause file writes, overwrites, updates, edits, deletes, commits, scheduled jobs, plugin changes, skill changes, or config changes.
- The prompt needs a clear objective validation threshold.

Do not use this skill when:

- The user only wants a direct factual answer.
- The user asks for creative prose and does not need operational constraints.
- The prompt is already sufficiently scoped and no safety-sensitive writes are possible.

<!-- universal-coding-contract:start -->
## Universal Coding Contract for Code Work

Whenever an enhanced prompt can create, modify, refactor, review, or validate code, make this contract explicit in the operative prompt and its validation threshold:

1. **Size limits are hard gates.** Every source and test file Hermes creates or modifies is at most 200 physical lines. Every individual function, method, constructor, class, interface, protocol, trait, enum, or comparable named language construct is at most 30 physical lines. Count decorators/annotations, declarations/signatures, comments, blank lines, and bodies. If a touched file already exceeds a limit, split it before or as part of the scoped change; report untouched legacy violations without expanding scope silently.
2. **Nesting is shallow.** Semantic block/control nesting is at most three levels inside the enclosing construct. Formatting-only indentation does not count. In tests, measure relative to the test declaration so an outer test class or framework suite does not consume the test’s nesting budget.
3. **TDD is mandatory.** Work in vertical behavior slices using `BOOTSTRAP → RED → GREEN → REFACTOR`: establish the real test environment and command; write one behavior test; run it and observe the expected failure before production code; implement only enough real code to pass; run the focused and relevant full suites; then refactor while green.
4. **Tests prove user-visible contracts.** Focus tests on user-facing situations, public contracts, APIs, integration boundaries, and interfaces. Do not test private implementation details or add tests merely to increase test counts or coverage.
5. **Everything is real.** Do not use TODOs, mocks, stubs, fakes, spies, placeholder implementations, synthetic success responses, skipped/xfail placeholders, or unimplemented branches in delivered source or tests. Use real behavior, real services, real functionality, and real integration paths. Test containers, local service processes, sandbox accounts, and explicitly approved live test environments are valid real dependencies. If a required credential, paid call, or external side effect is not approved, stop with a blocker instead of simulating it.
6. **Validation is objective.** Before completion, run project-native tests plus language-aware file-length, construct-length, and nesting checks where available. If the project has no such checker, create a focused real parser-based verifier under `/tmp/hermes-verify-*`, run it against every created or modified code file, and remove it after verification. Regex-only checks are not sufficient for construct or nesting claims.

A code task is incomplete if any created or modified code file violates this contract, if RED was not observed before GREEN, or if the only evidence comes from a test double or implementation-detail assertion.
<!-- universal-coding-contract:end -->

## Prompt Enhancement Procedure

### 1. Extract the intent

Identify these fields before rewriting the prompt:

- **User outcome:** What should exist or be true after the task?
- **Context:** What conversation facts, paths, files, docs, or constraints matter?
- **Current-date and freshness scope:** What is the live runtime date/time/timezone, which facts or choices can change over time, and which current first-party or authoritative sources must be checked?
- **Minimal-change scope:** What acceptance criteria are required now, what is explicitly out of scope, which existing helpers/patterns/dependencies/tests/docs are candidates for direct reuse, and what is the smallest coherent read/write surface?
- **Session continuity:** What active task list items, unfinished work, or accumulated session context should continue while this prompt is executed?
- **Action type:** Answer only, plan only, read-only investigation, or write/execute task.
- **Coding scope:** Whether the task can create, modify, refactor, review, or validate source or test code and therefore requires the universal coding contract.
- **Write scope:** Whether the task may create, overwrite, edit, update, delete, commit, publish, or schedule anything.
- **Validation:** What objective tool output, file state, tests, docs, or command results prove correctness?

Completion criterion: every field is filled or explicitly marked as an assumption/open question; the live date/time/timezone is recorded, time-sensitive choices have a current-source strategy, and no requested change lacks an acceptance-criterion or reuse/diff decision.

### 2. Convert unknowns into assumptions or questions

If the ambiguity changes what tool to call, what file to modify, or whether a write is safe, ask a brief clarifying question.

If the ambiguity is low-stakes, choose the safest default and label it as an assumption.

Safe defaults:

- Prefer read-only investigation before writes.
- Prefer user-local Hermes customization surfaces over source-code edits.
- Prefer `skill_manage` for user-local skills.
- Prefer `hermes config`, setup commands, or purpose-built tools over direct edits to sensitive config/credential files.
- Prefer a plan when the user invoked `/plan` or explicitly asks for a plan.
- For new skills or config/toolbox/profile repositories, use the repository owner's approved metadata defaults. When no project rule exists, propose `version: 0.1.0`, `author: <repo-author-name>`, `license: Apache-2.0`, repository-local Git identity `<repo-author-name> <repo-author-email>`, and no AI co-authoring trailers; obtain approval before writing.
- For public Hermes config/toolbox/profile documentation, keep tracked content identity-neutral by default: describe generic customization mechanisms and update rules without private profile names, personal plugin names, private paths, or personal identifiers unless explicitly approved for publication.
- Treat approved authorship frontmatter and repository-local Git metadata as narrowly scoped exceptions to public identity neutrality. Do not replace an approved author with a fabricated generic contributor and do not invent a placeholder email as the actual Git identity.
- For public artifacts derived from private Hermes configuration, require both public-safety and identity-neutrality validation. Use `$HERMES_HOME`, `$HOME`, role-based names, and `example.com`; keep private source names and rejection evidence in untracked local metadata.
- For public profile packages, distinguish user-specific profiles from reusable role/use-case/category candidates. Require an explicit untracked allowlist and a current native distribution containing only declared distribution-owned paths. Strip environment/auth stores, memories, sessions, logs, caches, databases, pairing state, cron outputs, provenance timestamps, absolute paths, and other runtime/private data; validate with the real profile installer in a disposable Hermes home.
- For public plugin packages, require a deployment-configured public plugin source profile supplied through CLI, environment, or untracked config. Other source profiles remain private unless the user changes the gate explicitly. Public packages must be reusable, identity-neutral, manifest-backed, and free of credentials, memories, sessions, logs, caches, databases, pairing state, cron outputs, and runtime/private data.
- For private Hermes backup prompts, distinguish non-reinstallable custom configuration/state from reinstallable/generated artifacts. Prefer backing up user-authored config, secrets, identities, profiles, memories, cron definitions, local scripts, local plugins, local skills, gateway/pairing state, and continuity state; exclude Hermes source checkouts, bundled/hub packages, virtualenvs, managed runtimes, dependency caches, build products, generated logs, and model/web caches unless the user explicitly asks for a full disk-style archive. Require a manifest documenting included paths, excluded reinstallable categories, and restore actions.

Completion criterion: no remaining ambiguity can cause an unsafe write, privacy leak, authorship mismatch, or unverifiable result.

### 3. Apply Hermes write-safety boundaries

When the enhanced prompt involves Hermes Agent files, include this policy.

#### Allowed / encouraged write-overwrite surfaces

Use these for normal Hermes customization:

- `$HERMES_HOME/config.yaml` for non-secret settings, preferably via `hermes config`.
- `$HERMES_HOME/.env` for secrets/API keys, preferably via setup/auth/config commands, not raw file reads.
- `$HERMES_HOME/SOUL.md` for global identity/personality.
- Project context files in the active workspace: `.hermes.md`, `HERMES.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.cursor/rules/*.mdc`.
- `$HERMES_HOME/memories/MEMORY.md` and `$HERMES_HOME/memories/USER.md`, preferably via the `memory` tool.
- `$HERMES_HOME/skills/<category>/<skill>/SKILL.md` and allowed skill support directories: `references/`, `templates/`, `scripts/`, `assets/`, preferably via `skill_manage`.
- Configured `skills.external_dirs` when the skill already exists there and the directory is intentionally writable.
- `$HERMES_HOME/plugins/<plugin>/` for personal/team plugins.
- Trusted project-local `.hermes/plugins/` only when explicitly enabled and trusted.
- `$HERMES_HOME/cron/jobs.json` via `hermes cron` or the `cronjob` tool.
- Workspace `.hermes/plans/` for plan documents.

#### Not allowed / not recommended overwrite surfaces

Avoid these unless the user explicitly requests upstream/fork development and the task includes tests/review:

- Hermes source checkout files such as `$HERMES_HOME/hermes-agent/**`, `/usr/local/lib/hermes-agent/**`, or any cloned `NousResearch/hermes-agent` repo.
- Core source directories/files: `agent/`, `tools/`, `toolsets.py`, `run_agent.py`, `model_tools.py`, `cli.py`, `hermes_cli/`, `gateway/`, `cron/`, `tui_gateway/`, `acp_adapter/`.
- `agent/prompt_builder.py` for normal prompt customization; use `SOUL.md`, context files, skills, or config instead.
- Repo `plugins/`, repo `skills/`, and repo `optional-skills/` for personal customization.
- Internal skill state such as `$HERMES_HOME/skills/.bundled_manifest` and most of `$HERMES_HOME/skills/.hub/`.
- Plugin-provided `plugin:skill` content via `skill_manage`; those skills are read-only from the skill tool's perspective.
- Another profile's `skills/`, `plugins/`, `cron/`, or `memories/` unless the user explicitly targets that profile.
- Credential/token stores by direct file read/write: `auth.json`, `.anthropic_oauth.json`, `mcp-tokens/`, project `.env*` files, and similar secrets.
- Runtime stores such as `state.db`, `sessions/`, `logs/`, `cache/`, `pairing/`, checkpoints, backups, venvs, managed Node, or managed `uv` unless using the official CLI/tool that owns them.

Completion criterion: the enhanced prompt clearly says where writes may occur and where they must not occur.

### 4. Add source-of-truth validation requirements

For Hermes Agent tasks, require validation against first-party sources before acting or finalizing:

- Official docs: `https://hermes-agent.nousresearch.com/docs/`
- Official repo: `https://github.com/NousResearch/hermes-agent`
- Local repo files only when intentionally working on a clone/fork.
- Relevant Hermes CLI/tool output when checking the live install.

Completion criterion: the enhanced prompt names the first-party sources needed for the task.

### 5. Produce the enhanced prompt

Use this structure unless the user requested a different format:

```markdown
You are Hermes Agent operating in [answer-only | plan-only | read-only | execute] mode.

## Objective
[One sentence: desired outcome]

## Context
- [Relevant conversation/project facts]
- [User constraints]
- [Assumptions]
- Continue all previous and existing work within this session, using the accumulated session context and active task list. Treat this prompt as an additional steering instruction, not a reset, unless the user explicitly says to start over or replace prior work.

## Freshness and Minimal Change
- Current runtime date/time/timezone: [exact live tool output]
- Freshness classification: [stable facts | time-sensitive facts/choices and required current sources]
- Current-source evidence: [first-party/authoritative sources with publication/effective dates, or an explicit unavailable-evidence blocker]
- Required behavior and non-goals: [current acceptance criteria and excluded speculative work; classify future-only seams, hooks, plugin points, and compatibility layers as non-goals unless a present concrete consumer or current externally observable acceptance requirement needs them]
- Reuse candidates: [existing helpers/patterns/dependencies/tests/docs inspected before adding anything]
- Smallest coherent diff boundary: [exact files/surfaces allowed to change]
- [Insert the complete Universal Freshness and Minimal-Change Contract here; do not merely cite it by name.]

## Scope
Allowed actions:
- [Read/search/plan/write commands]

Not in scope:
- [Explicit exclusions]

## Write Safety
Allowed write surfaces:
- [Exact allowed paths/tools]

Prohibited or clarification-required write surfaces:
- [Exact disallowed paths/tools]

## Source-of-Truth Checks
- [Docs/repo/files/commands to validate against]

## Execution Rules
- Convert unknowns into assumptions or clarifying questions.
- Use tools for current facts, file contents, git state, dates, or calculations.
- Do not fabricate outputs.
- Stop once the validation threshold is met.

## Coding Contract
- [When code is in scope, insert the complete Universal Coding Contract for Code Work, including its structural limits, real-test requirements, and BOOTSTRAP → RED → GREEN → REFACTOR sequence.]

## Validation Threshold
The task is complete only when:
1. [Objective proof]
2. [Safety proof]
3. [Output/schema proof]

## Required Output
[Final answer format]
```

Completion criterion: the enhanced prompt is copy-pasteable and contains no hidden assumptions about unsafe writes.

### 6. Execute the enhanced prompt

After the enhanced prompt passes the verification checklist, execute it immediately in the same session unless the user explicitly requested prompt text only or execution is blocked by missing context or unsafe side effects requiring clarification.

Execution rules:

- Treat the enhanced prompt as the operative task brief.
- Preserve session continuity: continue active task-list items, unresolved work, and relevant accumulated context while executing the new prompt, unless the prompt explicitly says to reset, discard, or supersede prior work.
- Use the required tools and actions specified by the enhanced prompt rather than only returning the prompt.
- When the user says to execute a previously saved plan, first treat that plan file as the source-of-truth scope: read it, preserve its allowed/prohibited write surfaces, execute only the listed target files/actions, and validate against the plan's stated threshold before reporting success.
- For Hermes profile/config migration plans, add a safety preflight before writes: check for active profile processes, gateway/cron state, source/target path existence, and whether the task is idempotent. Create rollback artifacts before mutation, prefer official `hermes config set`/profile commands for config, update generated aliases/wrappers only when in scope, and scan active human-authored surfaces afterward while excluding runtime stores (`sessions/`, `logs/`, `cache/`, `state.db`, checkpoints, backups). If a smoke-test subprocess prints the required output but exits nonzero after output, verify with a second independent check before reporting success or failure.
- For an hourly continuation cron that should resume a long task only when its interactive agent is no longer working, follow `references/hourly-continuation-cron-gates.md`: use a `wakeAgent` pre-run script, combine exact process descendants with bounded supported session activity, recheck inside the prompt, fail open on unverifiable state, and prove both manual and real scheduled suppression.
- For an approved multi-profile skill contract rollout, follow `references/hermes-multi-profile-skill-rollout.md`: preserve customized copies with marker-delimited targeted patches, seed only missing allowlisted skill trees, witness real RED before mutation, validate fresh local and enabled-only discovery, run temporary negative controls, and distinguish concurrent drift from the agent's own writes.
- Before writing into a workshop, distribution, public-source, or otherwise watched directory, inspect scheduled cron jobs, filesystem watchers, CI/export scripts, and downstream repositories that may consume a new child directory. Treat local creation, consumer installation, candidate export, and publication as separate approvals. If unapproved automation would act, pause only the relevant reversible publisher before writing, verify that no public copy, commit, or push appeared, leave it paused until the user decides or an explicit opt-out exists, and report the hold in the final result.
- If execution requires writes or external side effects, enforce the enhanced prompt's scope and write-safety boundaries.
- Ask for clarification only when ambiguity changes the target, safety, or validation threshold.
- Verify the resulting work against the validation threshold; if validation fails, iterate or report the blocker honestly.
- For long security-sensitive coding candidates, optimize wall-clock time deliberately: keep one writer, fill safe read-only audit capacity, batch independent static/focused checks, sweep exhaustive constructors before the long suite, prove the installed consumer early, and use sparse 5–10 minute progress checks. Follow `references/fast-security-candidate-execution.md`; speed never relaxes digest, RED→GREEN, real-service, audit-return, or post-commit gates.
- If code/config/script changes lack a canonical test/lint/build command, create and run a focused temporary verifier under `/tmp` with a `hermes-verify-` filename prefix, then clean it up when practical. Label the result as ad-hoc verification, not suite green. For Python 200-line/30-line/nesting checks, prefer the reusable parser-based `scripts/verify-python-structure.py <src> <tests>` instead of repeatedly hand-writing an AST verifier. See `references/ad-hoc-verification.md`.
- In the final response, include the enhanced prompt only when requested or useful; otherwise return the execution result and validation evidence.

Completion criterion: the enhanced prompt has been acted on, and the final response reports the actual result plus objective validation evidence or a clear blocker.

## Output Styles

### Compact prompt

Use when the user wants a short improved prompt.

```markdown
[Role/mode]. Improve/execute: [objective]. Continue all previous and existing work within this session using accumulated context and the active task list unless explicitly reset. Use current conversation context: [context]. Validate against [sources]. Write only to [allowed paths/tools]. Do not write to [prohibited paths]. Ask only if ambiguity changes safety or target. Success means [validation threshold]. Return [output format].
```

### Operational prompt

Use when the prompt may cause tool use or file changes. Include the full template from the procedure.

### Plan-mode prompt

Use when the user invoked `/plan` or asks for a plan. Add:

```markdown
Plan only. Do not implement. Write exactly one plan file under workspace `.hermes/plans/`. Do not edit other files.
```

## References

- `references/read-only-external-archive-review.md` — safe pattern for downloading, extracting, fully reading, and validating external archives in `/tmp` without installing or writing into Hermes profiles/configs.
- `references/temp-workspace-plan-execution.md` — pattern for executing a saved plan against a temporary extracted workspace using baseline/final manifests, dry-run-only installer checks, and focused `/tmp/hermes-verify-*` validation.
- `references/long-running-saved-plan-execution.md` — bounded one-writer TDD slices, delegated-worker handoff, drift evidence, verification interrupts, and later approval gates for large saved-plan executions.
- `references/herdr-real-service-restore-tdd.md` — isolated real-Herdr fixtures, official session-source identity, full-restart terminal rebinds, typed human confirmation, and fail-closed restore acceptance.
- `references/parallel-read-only-audits.md` — use maximum safe subagent parallelism for security, gap, and compatibility audits without racing a dirty one-writer TDD slice.
- `references/saved-plan-full-rollback.md` — exact-scope rollback manifests, targeted inverses, privacy-regressing prestates, runtime-session safety, allowlisted cleanup, and irreversible residue reporting.
- `references/saved-plan-drift-ledger.md` — baseline/checkpoint drift evidence, concurrent-change attribution, stale delegated-audit reconciliation, and precise completion language.
- `references/long-running-human-questions.md` — one-hour clarification configuration, current-session ordinary-chat fallback, and bounded work packets for user-side commands, GUI checks, OAuth, and acceptance evidence.
- `references/hourly-continuation-cron-gates.md` — hourly long-task recovery with `wakeAgent` pre-run gates, exact TUI/session activity checks, race rechecks, gateway heartbeat proof, and local TUI audit delivery.
- `references/public-private-hermes-repo-prompts.md` — prompt patterns for public/private Hermes config repositories, including identity-neutral public publishing and non-reinstallable private backup scoping.
- `references/public-repo-pr-cleanup.md` — focused upload pattern for cleaning stale dirty worktrees, backing up discarded diffs, starting from fresh `origin/main`, force-adding reviewed ignored public artifacts, and opening a scoped PR.
- `references/standalone-public-primitive-publication.md` — exhaustive candidate-universe classification, standalone dependency closure, cryptographically reusable decisions, last-known-good retention, transactional export, PR/CI, and fresh-clone verification for public Hermes primitives.
- `references/semantic-public-sanitizer-review.md` — final-boundary TDD, identity-neutral fixtures, narrow placeholder grammar, token-bounded rewriting, transactional rollback, and digest-bound reviews for public sanitization.
- `references/exact-single-skill-public-classification.md` — read-only expected-hash classification of one skill using an exact index projection, independent semantic/newline gates, clean-home discovery, end-hash sealing, and side-effect cleanup.
- `references/hermes-profile-spec-validation.md` — validation pattern for reconciling full Hermes profile specifications with current docs, live CLI output, supported hook names, Kanban/profile behavior, model data, and external first-party product docs.
- `references/remote-inference-continuous-training-plans.md` — validation and architecture pattern for plans where Hermes runs on one host, inference runs on a separate private server/workstation, and production traces feed a reviewed training loop.
- `references/remote-thin-client-plan-execution.md` — execution-surface verification and safe bootstrap when the user types through a local thin client but Hermes tools still run remotely; also covers user-visible delivery versus hidden tool output.
- `references/tailnet-only-ssh-cutover.md` — deadman-rollback SSH listener cutover, dynamic-UID confirmation, strict private reconnect probes, public-port denial, and exact rollback evidence.
- `references/cross-host-browser-preview-acceptance.md` — TDD and human-acceptance pattern for a local browser reaching a remote loopback preview through an exact SSH forward, including secure WebSockets, OAuth nonce safety, embedded-JS parsing, and rollback proof.
- `references/daytona-tailnet-vnc-preserve-access.md` — Segment tagged ephemeral or persistent Daytona browser sandboxes while preserving direct-member access; covers private loopback noVNC/Serve, pinned exit-node egress, policy TDD, human-local SSH authentication, archive/snapshot lifecycle, retention reminders, and exact cleanup/residue proofs.
- `references/cross-host-per-process-egress-acceptance.md` — Restricted per-process SSH SOCKS staging and acceptance: separate keys, out-of-band host-key verification, source-bound forwarding-only authorization, RED-before-install, `socks5h` proof, and teardown.
- `references/hermes-profile-online-training-specs.md` — reconciliation pattern for private Hermes profile specs that use managed online training, HF Jobs/Storage Buckets, detector loops, paid API caps, and exact approval gates.
- `references/secret-gated-paid-blocker-resolution.md` — pattern for fixing non-secret blockers under a spend cap while isolating HF/Pangram/API-key blockers behind no-echo user-side setup and readiness validation.
- `references/hermes-bulk-profile-model-rollout.md` — safe all-profile model/provider rollout: inventory, auth and process preflight, exact rollback for absent configs, profile-specific runtime overrides, residual scans, validation, and restart discipline.
- `references/hermes-multi-profile-skill-rollout.md` — safe all-profile skill-contract rollout: targeted rollback, witnessed RED, marker-preserving patches, allowlisted seeding, fresh enabled-only discovery, adversarial controls, concurrent-drift handling, and runtime activation boundaries.
- `references/hermes-multi-profile-plugin-purge.md` — safe procedure for uninstalling a plugin across live profiles, cleaning stale config/runtime/cron state, removing automatic reinstall rules, preserving out-of-scope source archives, and validating fresh-process absence.
- `references/post-commit-verification-tracking.md` — make background/full-suite results externally recognizable with a fresh foreground post-commit verification packet.
- `references/exact-candidate-python-release-seal.md` — bind one Python candidate’s long-suite evidence, staged digest, baseline-differential static analysis, reproducible wheel, installed-artifact proof, and exact-digest reviews.
- `references/security-sensitive-candidate-sealing.md` — digest-generation sealing, long-suite timeout sizing, audit invalidation, same-UID child confinement, descriptor-bound sockets, and inert installer evidence.
- `references/fast-security-candidate-execution.md` — one-writer/parallel-audit sequencing, exhaustive fixture sweeps, installed-consumer preflight, evidence-based timeout sizing, sparse progress checks, and digest-bound rerun discipline for long security candidates.
- `references/security-broker-remediation-race-patterns.md` — pidfd-coherent identity, post-commit liveness compensation, leaderless PGID cleanup, bounded quiescence, authenticated readiness, and crash-atomic no-replace publication.
- `references/fixed-systemd-worker-activation.md` — distinct broker/launcher/worker identities, broker-only fixed-unit activation, `LoadCredential` and `Type=notify` ordering, per-request invocation/cgroup revalidation, crash recovery, inert installer artifacts, and privileged acceptance gates.
- `references/inert-systemd-installer-sealing.md` — exact digest-command provenance, authenticated installed-tree mappings, bundled wheel/venv closure, real systemd boundary tests, independent schema/migration oracles, and valid baseline-differential static analysis.
- `references/native-kanban-operation-parity.md` — strict vertical slices for extending pinned Hermes Kanban broker mutations and fail-closed client transport.
- `references/kernel-bound-operator-cli.md` — kernel-bound ephemeral operator sessions, direct-child pidfd enrollment, gated broker-only CLI execution, bounded Unix sockets, and inert dashboard posture.
- `references/browser-media-profile-specs.md` — profile-spec pattern for browser, media, and creative API capabilities with protected-input, cost, and validation gates.
- `references/cross-host-command-surface-safety.md` — cross-host command routing, execution-surface labeling, and safe remote/local boundary checks.
- `references/humanized-writing-profile-specs.md` — private writing-profile design with corpus-grounded rules and external detector approval gates.

## Common Pitfalls

1. **Enhancing the prompt but losing the user's actual outcome.** Keep the first sentence outcome-driven.
2. **Adding generic safety prose without exact paths.** Name allowed and prohibited paths explicitly.
3. **Treating a Hermes source checkout as a customization surface.** Normal users should use `$HERMES_HOME` skills/plugins/config/context files instead.
4. **Reading or rewriting secrets directly.** Use auth/setup/config flows; never ask the model to inspect raw secret stores unless the user explicitly provides a safe redacted excerpt.
5. **Ignoring profile boundaries.** A named profile has its own `$HERMES_HOME`; do not modify another profile's `skills/`, `plugins/`, `cron/`, or `memories/` without explicit direction.
6. **Over-asking.** Ask clarification only when ambiguity changes safety, target paths, or validation.
7. **No objective finish line.** Every enhanced prompt needs a validation threshold that can be proven by tool output or source content.
8. **Executing a saved plan loosely.** When the user says “execute this plan,” the saved plan becomes the scoped task brief. Read it first, keep its write boundaries, do not add adjacent work, and finish with the plan's own validation evidence.
8a. **Racing an active background implementer.** A delegated coding worker may intentionally leave the shared workspace RED between test creation and implementation. Treat its target files as worker-owned until completion: do not launch overlapping writers or “repair” an observed RED concurrently. If an external verification interrupt requires a check, re-read the current files, run the narrowest relevant test, respect sibling-edit warnings, and verify the complete shared artifact yourself only after the worker reports completion.
8b. **Trusting a prior audit over current first-party evidence.** When a saved plan or delegated audit conflicts with the live pinned source, CLI, or official current contract, the live evidence wins. Preserve the plan's outcome and safety boundary, write a failing regression test for the corrected contract, then update the implementation. Do not encode a disproven assumption as an intentional permanent compatibility hold merely because it appeared in an earlier audit.
8c. **Treating blanket execution approval as permission to cross later plan gates.** If the saved plan explicitly requires a later reviewed manifest, privileged cutover approval, paid-action approval, publication approval, or custom-policy decision, execute up to that gate and present the exact evidence/manifest. Do not infer advance approval for a decision whose concrete scope did not yet exist when the user said “implement the plan.”
8d. **Over-scoping delegated implementation slices.** Delegate one coherent vertical behavior or tightly coupled contract at a time, not a long range of plan tasks or many independent APIs. A child’s completion summary is unverified evidence: after it releases the shared files, re-read every modified file, finish incomplete RED→GREEN slices, run focused and full tests plus structural/security checks, and create or verify the commit in the parent session. If the child stops mid-slice, narrow the next delegation rather than repeatedly redispatching the same oversized scope.
8e. **Trusting task labels, filenames, or prior green suites instead of the saved plan’s semantics.** Before continuing a claimed-complete phase, trace each exact plan acceptance criterion to a public behavior test, implementation path, verification result, and commit. A similarly named dispatcher or policy is not proof that the planned transport or workflow model exists. If the matrix disproves the active task list, reopen the item and witness a regression RED before later-phase work.
8f. **Starting another slice before sealing the current GREEN checkpoint.** Treat focused/full-suite GREEN as a mandatory stop: structural checks → commit → foreground post-commit regression → drift capture → handoff evidence. Reserve those calls before starting each slice. Once its full suite starts, do not explore or implement adjacent work until the commit is clean. After every sealed checkpoint, use the observed duration and tool-call cost of the preceding slice—not optimism about the remaining session—to decide whether another slice can still be fully RED→GREEN→full-suite→commit→post-commit verified. If the interface exposes no reliable remaining-call budget, repeated 15–20 minute suites or multiple recent tool-limit interruptions are a hard signal to stop at the clean checkpoint rather than begin another RED. A user request to continue autonomously does not justify knowingly stranding a dirty worktree; continue in a fresh continuation session from the clean handoff instead. If tools are cut off anyway, report the last real HEAD/status/test evidence and known dirty paths; never substitute a generic failure summary.
8g. **Calling a clean target repository “no drift” while protected external boundaries changed.** Record readable status plus HEAD/status digests before writes and after every committed slice. Treat live candidate-source trees outside the worktree as protected boundaries: hash the exact candidate packages with a stable generated/runtime exclusion policy before classification, immediately before export, and after the slice. If a watched/public/source boundary changes without an authorized write, preserve it untouched, classify it as concurrent or unattributed drift, and restart classification for changed candidates rather than mixing source snapshots. A prior export is “last-known-good,” not “current,” and may remain only if it passes the current full contract. Keep publication/rollout/cutover blocked and never claim no drift throughout the run. A delegated audit is valid only for its pinned HEAD; reconcile it against current source before treating findings as current. Follow `references/saved-plan-drift-ledger.md`.
8h. **Assuming a successful background suite satisfies every fresh-verification tracker.** First prove the committed HEAD and clean status. Preserve the complete background suite’s final zero exit and output, then run the smallest directly relevant `pytest` set in a normal foreground terminal invocation when an automated verifier still reports the touched files as unverified. If the verifier repeats after a successful chained packet (`pytest && structure && status`), run one plain foreground `python -m pytest <directly-relevant-tests> -q` command by itself—no `&&`, linters, status checks, wrappers, or background log retrieval—so command-shape-sensitive trackers can recognize it. If a combined direct-test invocation is still not credited, do not repeat an equivalent combined packet: escalate immediately to each directly relevant test file in its own standalone foreground invocation and report those zero exits separately. Treat a fresh system verification notice as command-shape feedback even when equivalent evidence appeared earlier in the conversation; produce current-turn standalone evidence instead of arguing from prior output. For every long background suite, write a named `/tmp/hermes-verify-*` log and numeric exit artifact tied to the exact candidate digest; a vanished runner without a recoverable exit artifact is invalid evidence and should be stopped rather than allowed to consume the remaining runtime. Do not rerun a 10–20 minute full suite for tracker bookkeeping, and do not loop indefinitely when a tracker repeats after file-by-file GREEN—state that the external tracker did not credit the evidence while preserving the exact commands and outputs. When one guard-mandated OS-temp verifier has run successfully in a top-level foreground call and cleaned up, a later notice that lists the removed verifier or replays unrelated older output is stale attribution: follow `references/post-commit-verification-tracking.md`, preserve the candidate-bound proof, do not recreate an equivalent verifier, and never claim tracker-visible green. If a generated test launcher has a stale interpreter path, first use the functioning project interpreter with `-m pytest` rather than mutating venv/runtime files. If a command-shape-sensitive tracker still requires an exact `pytest` entrypoint, do not rewrite the stale wrapper: create a disposable project environment from the repository's declared test/dev dependencies (for a uv project, for example, `UV_PROJECT_ENVIRONMENT=/tmp/hermes-verify-pytest uv run --extra dev pytest <direct-test-file> -q`) and run each directly relevant test file in its own foreground invocation. This both preserves the user environment and verifies that the dependency declaration is sufficient for a clean test bootstrap. Use a unique `/tmp/hermes-verify-*` path, never hardcode a host-specific interpreter path, and report comprehensive, foreground, and clean-environment results separately. Follow `references/post-commit-verification-tracking.md`.
8i. **Equating maximum delegation with multiple writers.** During an active RED→GREEN slice, keep one writer and spend available subagent capacity on independent read-only security, semantic-gap, and compatibility audits. Pin the base HEAD, enumerate parent-owned dirty paths, prohibit edits/commits/full suites/side effects, and reconcile returned findings against current files before use. Verify every report's provenance against the requested repository, task, HEAD/digest, and delegation linkage; never select the newest globally cached summary by timestamp alone, because it may belong to an unrelated concurrent workflow. Never claim an audit that did not return before the checkpoint was sealed. Follow `references/parallel-read-only-audits.md`.
8j. **Treating a private Unix socket or same UID as operator authority.** A socket mode and `SO_PEERCRED` UID restrict access but do not distinguish same-UID siblings or survive PID reuse. Separate static principal provisioning from ephemeral authority; enroll only a gated direct child through a private registrar, bind UID/PID/process-start/generation/expiry, hold a pidfd through the atomic bind, and keep mutations on exact preview → sanitized TTY confirmation → same-process execution with no native fallback. Bound public and private connection concurrency so a partial frame cannot head-of-line block valid work. Follow `references/kernel-bound-operator-cli.md`.
8k. **Running tracker-facing focused tests beside an authoritative full suite.** Tests that share a HOME, profile, daemon, worker launcher, database, socket, or runtime directory can interfere even when pytest `tmp_path` values differ. Never start a focused tracker run concurrently with the authoritative suite unless the selected tests are proven process-local and resource-isolated. Prefer waiting for the full suite; if immediate guard evidence is mandatory, stop the background suite first, run the exact named tests alone, then restart one authoritative suite. Track the one authoritative process ID, and treat delayed completion notices from superseded or SIGTERM-invalidated process IDs as stale evidence rather than new regressions. Follow `references/post-commit-verification-tracking.md`.
8l. **Adding schema, credential, or closed command/config fields without updating exhaustive contract tests.** After every migration, persisted identity-field addition, required config field, or command-grammar restriction, search before the long suite for hardcoded migration-version lists, synthetic next-migration numbers, exact record fixtures, direct dataclass constructors, `dataclasses.replace` calls, multi-argument command tuples, installed-bundle schemas, clean-environment probes, and public storage/config API tests. Derive expected applied versions from the canonical migration registry; inject rollback failures at `latest + 1`; populate every newly required public record/config field; and replace obsolete synthetic argv with real single executable fixtures rather than weakening production validation. Run these boundaries before an expensive full suite so it does not fail on stale exhaustive fixtures.
8m. **Treating exact fleet propagation as proof that the propagated contract is true.** Marker identity, baseline reconstruction, fresh discovery, and adversarial structure tests prove rollout mechanics, not semantic correctness. Before sealing a multi-profile contract rollout, reconcile an independent read-only semantic audit against the installed release-pinned handlers, response shapes, approval paths, and current first-party docs. Keep the focused verifier and completion report open until that audit returns. If it disproves a plan-authored claim after initial GREEN, supersede the premature completion statement, witness a focused fleet regression RED, correct only the canonical marker block and exact old copies, rerun discovery/disposable-profile/protected-boundary validation, and refresh all report hashes. Follow `references/hermes-multi-profile-skill-rollout.md`.
8n. **Treating staged security work as one timeless candidate.** Identify each generation by the staged binary diff digest. A late self-review fix, stronger test oracle, audit-driven edit, or exhaustive-fixture repair invalidates that generation’s wheel, full suite, installed proof, and audits: stop the old process, issue a new digest, and regenerate evidence. Size background timeouts from the slowest observed complete suite plus at least 20% margin; a focused-suite duration or early progress percentage is not a valid full-suite estimate. When no complete duration exists, choose a conservative bound rather than knowingly stranding a nearly complete run. Never count SIGTERM, a printed summary without normal process exit, a missing numeric exit artifact, or a stale delayed notice. Treat “audit dispatched” as in-progress state, not review evidence: require a delivered, provenance-linked report that independently verified the current digest, and preflight reviewer CLI authentication before launching parallel reviewers. For same-UID descendants, descriptor-sensitive local brokers, or authenticated inert bundles, require kernel-enforced child confinement/readiness, explicit `SO_PEERCRED` server identity, monotonic deadlines, bounded drain/dedup, descriptor-relative filesystem operations, and immutable verified bytes as applicable. Follow `references/security-sensitive-candidate-sealing.md` and `references/fast-security-candidate-execution.md`.
8o. **Interpreting “publish all possible standalone primitives” as a broad copy or as permission to repair failures.** First enumerate the intentional candidate universe by primitive class and source gate; separately account for bundled/Hub provenance, modified bundled skills, profile-only families, and noncanonical overlays. Define standalone by package-local reference closure, public/bundled hard-dependency closure, and clean-home real-loader behavior. Reuse an old decision only when source, pipeline, runtime, and contract digests match. Treat static exporter/validator GREEN as necessary but insufficient: audit the exact public bytes for sanitizer-corrupted commands/product names, disallowed runtime paths, doubled placeholders, and cross-skill marker/version closure. Use `accepted-current`, `retained-last-known-good`, `hold`, `rejected`, and `withdraw` dispositions; delete an existing package only when its own public bytes fail, not merely because newer source fails. Keep rejection details untracked, do not remediate live source or resume an automatic publisher unless separately authorized, and publish through a transactional idempotent branch/PR/CI flow with fresh-clone verification. Close tracked defaults, YAML examples, discovery metadata, non-vacuous installer sentinels, fingerprint regeneration, and final-newline hygiene before sealing. Treat every staged-diff edit as a new digest generation, and re-freeze/reclassify any source that drifts during review before dispatching the final reviewers. After source drift, require a quiet window at least as long as the slowest observed final review plus explicit margin before redispatching; a shorter arbitrary window is not evidence of stability. If the protected source changes during two consecutive review generations, stop the reclassify/review loop and require the other writer or workflow to become quiescent before trying again. Treat class-level skill maintenance as a possible competing writer even when a delegated audit reports no writes: a reusable-reference or `SKILL.md` update may land only after the child returns, so always rehash after result delivery rather than trusting the child's end hash. If repeatedly delegating the same classification causes a self-invalidating procedural update, do not keep redispatching it. First obtain the full quiet window; then classify the exact current bytes once through a parent-controlled disposable projection that does not load or patch the candidate skill, preserve the report privately, and immediately rehash. This is an escape hatch for cyclic evidence generation, not permission to weaken any gate or ignore unrelated drift. A review PASS is interval-bound: recheck protected sources after commit and before push; post-commit drift keeps the commit local/unpushed and requires affected-source reclassification plus a fresh review, not an unnecessary commit rewrite when public bytes are unchanged. Follow `references/standalone-public-primitive-publication.md`.
8p. **Testing security races at the wrong boundary.** A fixed sleep or an early database lock can accidentally exercise an already-safe precondition instead of the post-commit race named by the audit. Synchronize on a real externally visible milestone, keep the relevant pidfd/descriptor open across the boundary, and inject death or namespace contention immediately after the real persistence/publication step. For leaderless process groups, account for Linux `pidfd_open` returning `EINVAL`; for installer output, stage privately and publish with `renameat2(RENAME_NOREPLACE)`. Require explicit compensating state and immediate-retry proofs. Follow `references/security-broker-remediation-race-patterns.md`.
8q. **Treating a native tool name as proof of broker contract parity.** Trace every callable and side effect behind the native surface. A nominal read may recompute state; an aggregate response may not fit the ledger’s simple-read schema. Do not hide composite behavior behind a caller flag or an unrelated operation ID. Model exact approval/journal/result semantics or retain a broker-owned fail-closed hold. For local brokers, also treat additive Landlock reads, service supplementary groups, incomplete process identities, missing signed audit genesis, and automatic exactly-once journal eviction as candidate-invalidating architecture findings. Follow `references/native-kanban-operation-parity.md` and `references/security-sensitive-candidate-sealing.md`.
8r. **Calling authority integrity “full isolation” while same-UID availability remains.** Setgid socket directories, removed supplementary groups, Landlock, pidfds, and complete process binding can protect trusted bytes without preventing a same-UID worker from signaling or resource-starving the broker. Make integrity and availability separate acceptance rows. Require a genuinely distinct worker service identity or equivalent privileged boundary plus a real launch-path process proof for availability; otherwise stop at an explicit residual-risk gate. Never weaken direct-child PID binding or use `sg`/`newgrp` intermediary processes as proof. Follow `references/security-sensitive-candidate-sealing.md`.
8s. **Letting a disposable or delegated runtime home contaminate authoritative verification.** Persistent terminal snapshots can retain `HOME`, `HERMES_HOME`, or `PATH` exported by a disposable classifier after that directory is deleted, causing real-runtime tests to resolve a nonexistent Hermes checkout or virtualenv. Before every authoritative suite that follows delegation or clean-home probing, print and verify `HOME`, `HERMES_HOME`, `Path.home()`, the Hermes CLI, and the expected runtime interpreter; run the suite with an explicit known-good `HOME`. If a stale environment invalidates a run, classify it as harness-invalid, restore only the environment, and rerun the complete required proof—do not change production code or tests to fit the contaminated shell. For tracker-specific ad-hoc evidence, allocate `/tmp/hermes-verify-*` with an OS-safe tempfile primitive, invoke the exact focused tests and structural checker, label it ad-hoc rather than suite green, and remove it afterward. Follow `references/standalone-public-primitive-publication.md`.
8t. **Calling one skill accepted because the exporter and clean-home discovery pass.** For an expected-hash single-skill classification, freeze the exact source, project it from the exact repository index into a disposable root, and independently inspect every source-to-projection byte change plus final-LF hygiene. Static validators and real discovery are orthogonal evidence: malformed nested author/email placeholders, sanitizer-corrupted concrete profile or command names, and missing final newlines are hard rejection gates even when public-safety, identity-neutrality, package completeness, structure, and `hermes skills list` all pass. Distinguish advisory metadata peers from body-mandated skill loads, rehash source and projection at the end, and report all side effects. Follow `references/exact-single-skill-public-classification.md`.
8u. **Letting a multi-command verification packet hide an earlier failure.** A shell returns the status of its final command unless fail-fast behavior is explicit, so `ruff; structure; compile; git diff --check` can report exit 0 even when Ruff or structure failed. For ordinary local validation packets, start with `set -euo pipefail` or join required gates with `&&`, and preserve each gate's output. Treat any failure text as a failed packet even if the wrapper reports zero; rerun only the failed gate after repair, then rerun the complete fail-fast packet. Keep tracker-facing pytest invocations standalone when command-shape recognition requires it—do not solve tracker bookkeeping by combining pytest with unrelated gates. Run the parser-based structural verifier as soon as a touched file, class, or function approaches its limit, not only at slice end, so required splits happen before more code accumulates.
8v. **Treating semantic sanitization as successful after transformer-only tests.** Exercise the final exporter safety/identity boundary and transactional last-known-good behavior. Distinguish personal authors from product/project/community authors so legitimate product prose survives; use token-bounded profile-name replacement; define placeholder-like syntax narrowly enough to reject malformed, braced-home, and quoted executable paths without rejecting C++ templates or comparison prose; and keep tracked tests free of real private literals by constructing neutral fixtures at runtime. Every review-driven edit creates a new staged digest and requires fresh focused/full validation plus new reviews. Follow `references/semantic-public-sanitizer-review.md`.
8w. **Interpreting “always pin latest” as a floating dependency or as the installed checkout.** Resolve the current latest non-prerelease release from the first-party release API, read the version from that tag's first-party package metadata, and peel annotated tags to the immutable commit (`refs/tags/<tag>^{}`). Pin the exact version, tag, and peeled commit in stable package-data filenames; do not use the annotated tag-object hash, a mutable branch, or a post-release local checkout merely because its version string matches. Add a live seal-time freshness oracle that fails closed when any of tag/version/peeled commit differs from the current latest release. Keep compatibility tests bound to an explicit source-root helper so disposable exact-tag checkouts cannot silently fall back to `$HOME` or the protected live checkout. Treat every repin as a new candidate digest requiring regenerated contract bytes, focused/full tests, wheel proof, and fresh reviews. Follow `references/exact-candidate-python-release-seal.md` and `references/security-sensitive-candidate-sealing.md`.
8x. **Issuing a fixed-worker capability or `READY=1` before the real Hermes plugin is post-exec ready.** The pre-exec wrapper may authenticate the systemd credential, bind the exact PID/unit/invocation, receive only non-secret lease metadata, and `execve` Hermes with the same PID. It must not call protocol readiness, export the capability token, or set worker lifecycle environment variables that activate hidden native mutation paths. Preserve only the credential-directory path. After all exact tool overrides register, the real plugin must reread the systemd credential, call authenticated `launch.ready`, bind the capability in process memory, validate the returned profile/board lease, and only then emit `READY=1`. Use a real wrapper→same-PID exec→Hermes plugin-manager→broker→notify integration; a manually copied plugin or synthetic registration context is insufficient installed-bundle proof. Ensure `HERMES_HOME` has the first-party named-profile shape `<service-home>/.hermes/profiles/<profile>` because current Hermes derives plugin profile identity from that path; an arbitrary worker directory resolves as `custom` and fails exact profile authorization. Follow `references/fixed-systemd-worker-activation.md` and `references/security-broker-remediation-race-patterns.md`.
8y. **Serializing independent review, repair, and quiet-window waits.** For security-sensitive exact-digest work, fill safe read-only capacity concurrently: required specification review, required security/quality review, and one adversarial preflight when capacity permits, while retaining exactly one writer. Collect all concrete findings for the retired digest before the expensive replacement-generation full suite; use direct RED→GREEN tests during repair, then run focused/full validation once and redispatch. Overlap independent protected-source quiet-window monitoring, but use the exact canonical hash/exclusion algorithm—hashes from different algorithms are incomparable and do not prove drift. Never edit a still-viable frozen candidate merely because one reviewer finishes first, and never trade away exact-digest, privacy, transaction, or dual-review gates for speed. See `references/semantic-public-sanitizer-review.md`.
9. **Dropping in-progress session work.** A prompt-enhancer invocation is normally additive. Do not treat it as a reset unless the user explicitly says to start over, discard prior work, or replace the current task.
10. **Returning a changelog when the user asked for a reconciled full artifact.** If the user says to update/reconcile a prompt, profile spec, plan, or other artifact but also asks for no “updates/changes/versions/edits/etc.” language, return the complete integrated artifact as the canonical version. Do not preface it with what changed, do not include a diff/changelog, and avoid headings like “Updates” or “Changes.”
   - Treat the user’s banned wording as applying to assistant-authored prose in the reconciled artifact, not necessarily to required literal schema/frontmatter keys such as `version:` when removing them would alter the artifact’s meaning or validity.
   - Before returning a reconciled artifact verbatim, run a focused case-insensitive scan for the banned prose terms and plausible nearby variants; remove/rephrase prose hits or explicitly treat required literal-key/code exceptions as exceptions.
   - When the target is an existing plan file, preserve the original file path and full plan intent; do not create a new timestamped plan unless the user asks for a new plan.
   - Avoid broad global substitutions over code blocks or schema examples: they can silently break valid code (for example method names such as `.replace(...)`) or required keys. Prefer targeted replacements with validation.
   - If the reconciled artifact contains embedded code, extract and compile/lint that code when practical before returning the artifact verbatim. A clean prose scan is not enough if cleanup touched code examples.
   - For large verbatim artifacts, read/emit the exact final file content after validation rather than reconstructing from memory; chunk only if platform limits require it, and keep chunk boundaries lossless.
11. **Leaving superseded local/hardware assumptions in a reconciled artifact.** If the user asks to remove a platform path such as “Mac Studio,” “local,” “desktop,” or “on-device” and use only online products/services, actively remove the old lane from architecture, tool choices, commands, validation, costs, and open questions. Replace it with validated online equivalents, and ensure the final artifact reads as one coherent canonical plan rather than a hybrid of old and new assumptions.
12. **Treating “use all web tooling to validate” as rhetorical.** For planning/spec prompts with current-tooling risk, execute read-only validation with available web/search/extract/provider-ranking tools before producing the artifact, cite first-party docs where possible, and label only unavoidable assumptions. Do not fabricate validation or rely on model memory for current product capabilities.
13. **Repeating or replaying secrets from the user’s prompt.** If the user provides an API key, token, OAuth authorization code, PKCE/device code, or full localhost callback URL while asking for a prompt/profile/config specification, treat it as secret material. In the enhanced prompt or final artifact, use a named secret reference or environment/config key and describe storage/validation without printing the raw value again. Never paste a callback into a new agent-started login process: the user must paste it into the same waiting first-party CLI process that created its state/verifier, or restart the flow if that process is gone. Verify auth with an independent non-secret read command; a user-reported `done` does not pass when that probe still reports unauthorized. Classify a simultaneous client/API version warning separately from authentication: verify whether a newer first-party release artifact actually exists before upgrading, and do not misdiagnose credential failure as version skew. See `references/secret-gated-paid-blocker-resolution.md`.
13a. **Equating spend approval with permission to handle secrets.** A user may approve a spend cap and ask to fix all blockers, but credential-only blockers still require no-echo user-side setup or official auth flows. Fix non-secret blockers immediately, apply the spend cap to config/manifests/gates, and provide a readiness validator plus manual secret setup helper instead of typing or printing token values. See `references/secret-gated-paid-blocker-resolution.md`.
14. **Answering plan-cost questions from memory or vague intuition.** When a user asks how much a proposed workflow will cost, treat it as a read-only validation task: verify current first-party pricing pages with web tooling, separate fixed subscription/storage/compute costs from usage-sensitive API costs, state assumptions and formulas, calculate concrete scenarios with tools, and include approval caps before any paid action. If a local corpus/file has already been identified in the session, use its measured size/counts when available; otherwise label corpus-size assumptions explicitly.
15. **Collapsing control host and inference server into one machine.** When a plan involves a remote/local inference server, explicitly separate where Hermes is running, where inference runs, where training runs, and where traces/evals live. Validate the custom endpoint path, private networking path, and runtime security notes; do not write `localhost` commands as if they apply to both the VPS and the inference machine.
16. **Treating continuous training from generated outputs as ordinary SFT data.** When production traces or model outputs feed a training loop, add provenance, consent, privacy review, human-review gates, fixed human-only evals, and model-collapse safeguards. Raw model outputs should not become human-authored training targets; prefer human rewrites or preference pairs with generated outputs as rejected candidates.
17. **Treating a pasted current spec as loose background.** If the user provides a "current spec" or similar artifact alongside a prompt-enhancer invocation, treat it as the source artifact to reconcile. Preserve exact approval gates and do not create profiles, launch paid jobs, call paid APIs, or write plugins unless the provided gate is satisfied. For managed online training/profile specs, use `references/hermes-profile-online-training-specs.md`.
18. **Treating blanket profile-spec approval as approval to bypass the spec's own gates.** If the user says they approve an entire profile spec and all associated plugins/skills/projects/Kanban/profile artifacts, interpret that as approval to create the named local profile/workspace/plugin/skill/Kanban surfaces only. Keep credential, OAuth, paid API, Browser Use profile-sync, LTX/FLORA billable-run, Toolcraft execution, Impeccable mutation, upload, publish, email-send, and other external side-effect gates intact unless the user gives a separate scoped approval satisfying the spec. For large generated plugin suites, load `plugin-builder` and use its profile plugin-suite generation reference.
19. **Assuming quoted config values are safer for Hermes enum-like settings.** For Hermes `approvals.mode`, the official `hermes config set approvals.mode off` command writes YAML `false`, and first-party approval runtime normalization treats boolean `False` as approval mode `off`. Do not force the literal quoted string `'"off"'` into profile-builder prompts or validation; runtime normalization treats that string as unknown and falls back to `manual`. When validating this setting, check the runtime-normalized mode, not just the raw YAML scalar type.
19a. **Assuming `hermes config set` preserves structured YAML types.** Before using it for MCP `args`, tool include/exclude lists, or other arrays/maps, inspect the parsed value afterward. A JSON-looking CLI argument may be stored as a scalar string, producing misleading list/status output or a runtime launch failure. If the official interactive command cannot be completed noninteractively, make one targeted edit on the user-owned profile `config.yaml`, validate it with a YAML parser, confirm list/dict types explicitly, and run the real MCP/config probe. Do not call the transport configured merely because discovery succeeded—authentication and service operations need separate non-secret readiness checks.
20. **Treating hidden tool output as the delivered artifact.** Tool-call results may not be visible in the user's interface. If the user asks to print, show, or return an artifact—or says they cannot see it—place the content in the user-visible assistant response or attach the exact file. For a request to print an artifact **verbatim**, re-read the current source immediately before responding, then emit only its exact text: no introduction, summary, line numbers, enclosing code fence, normalization, or trailing commentary. Do not reconstruct it from memory or an earlier draft. If the exact artifact cannot fit in one response, use lossless ordered chunks or attach the exact file and state that delivery boundary instead of silently truncating or summarizing. Never claim hidden tool output was delivered.
21. **Inferring local execution from message origin or a thin-client UI.** A user can type on a Mac while Hermes terminal and computer-use tools still run on a VPS. Verify message origin, UI renderer, terminal backend, and computer-use backend separately before running local probes. Network reachability is not authenticated shell access or GUI control. For bidirectional SSH, verify each host key out of band, test each direction independently, and never assume the account name is symmetric across hosts; generated wrappers must use an explicit `user@host` when the local and remote usernames differ. Validate wrapper argv and quoting with a non-mutating command before attempting an interactive attach, then prove a bounded attach does not terminate the durable remote session. Follow `references/remote-thin-client-plan-execution.md` and preserve every later gate.
22. **Using a short clarification field for a long human work packet.** If the user must run commands, inspect a GUI, complete OAuth, or perform several acceptance checks, configure and verify the user's requested clarification window first. A running CLI/TUI may cache the old value, so use ordinary chat for the current work packet until restart. Never interpret an empty/timed-out field as refusal or approval, and never let a longer timeout weaken an explicit gate. Follow `references/long-running-human-questions.md`.
23. **Answering “what exactly now?” or “give me all commands” with status prose or an incomplete recipe.** Return one command-complete, execution-surface-labeled packet: distinguish local/native terminals from remote/thin-client panes, include every prerequisite/check/apply/rollback command in order, state expected output and stop conditions, identify unavoidable GUI gestures separately, and end with a compact reply matrix. Do not make the user reconstruct commands from prior messages. If one acceptance item remains unverified and the user explicitly says to move on, record an exception rather than a pass and ensure later gates do not rely on the missing evidence.
24. **Treating an approved Tailscale Serve port as available, or a persistent mapping as a durable backend.** Before applying Serve, inspect OS listeners as well as Serve configuration; identify but never kill an unrelated listener. A replacement port changes the exact gated target and requires revised approval. After application, prove old handlers and unrelated listeners are unchanged, interpret Funnel exposure from explicit current status markers rather than non-empty handler JSON, and state separately whether the loopback backend is disposable, session-scoped, or durably managed. Follow `references/cross-host-browser-preview-acceptance.md`.
25. **Treating the live date as a substitute for current evidence.** The runtime date offsets temporal disorientation but does not update the model’s training knowledge. For every time-sensitive claim or choice, verify a current first-party or authoritative source and distinguish source publication date, effective date, and event date when they differ. If no live source is available, state the uncertainty or blocker instead of presenting model memory as current.
26. **Optimizing raw diff size or reuse at the expense of the task.** “Smallest diff” means the smallest coherent change that fully satisfies the acceptance criteria while preserving correctness, clarity, safety, maintainability, unrelated behavior, and user edits. Search for direct compatible reuse first, but do not line-golf, hide coupling, skip tests, force an abstraction across incompatible responsibilities, or retain a wrong helper merely to reduce changed lines.
27. **Treating “undo all work” as one obvious destructive scope.** First reverse only an unambiguous active exposure whose exact rollback is already known, then distinguish feature, phase, and whole-session rollback. For a whole-session request, inventory exact prestates, targeted inverses, unrelated state, privacy/security regressions, irreversible loss, and user-local residue before mutation. Restore source artifacts instead of deleting them, remove shared-file changes surgically, prove the current agent is not inside a runtime session before deleting it, and clean temporary artifacts from an allowlist rather than a broad wildcard. Follow `references/saved-plan-full-rollback.md`.

## Verification Checklist

Before returning an enhanced prompt, confirm:

- [ ] The user's desired outcome is explicit.
- [ ] Relevant conversation context is included.
- [ ] The enhanced prompt includes session-continuity wording unless the user explicitly requested a reset or prompt text only.
- [ ] Assumptions and open questions are separated.
- [ ] The enhanced prompt records the current date/time/timezone from a live tool rather than model memory.
- [ ] Stable and time-sensitive facts/choices are distinguished; every time-sensitive item has current first-party or authoritative evidence with relevant dates, or an explicit unavailable-evidence blocker.
- [ ] Required acceptance criteria, non-goals, existing reuse candidates, and the smallest coherent diff boundary are explicit before writes.
- [ ] Every proposed file, hunk, dependency, abstraction, refactor, and validation artifact is necessary; there is no speculative scope, unrelated churn, line golfing, or forced incompatible reuse.
- [ ] The action mode is clear: answer, plan, read-only, or execute.
- [ ] Allowed write surfaces are exact.
- [ ] Prohibited/clarification-required write surfaces are exact.
- [ ] Downstream cron/watch/export automation was checked when writes target a workshop, distribution, public-source, or watched directory; publication approval is separate from local creation approval.
- [ ] Hermes Agent claims are tied to official docs/repo or live tool output.
- [ ] The validation threshold is objective and finite.
- [ ] Every code prompt includes the 200-line file limit, 30-line construct limit, maximum nesting depth of three, and test-declaration nesting baseline.
- [ ] Every code prompt requires witnessed `BOOTSTRAP → RED → GREEN → REFACTOR` ordering before production code.
- [ ] Code tests target user-facing situations, public contracts, APIs, integration boundaries, or interfaces rather than implementation details or test-count/coverage theater.
- [ ] Delivered source and tests use real behavior and real services with no TODOs, mocks, stubs, fakes, spies, placeholders, synthetic responses, or skipped/xfail placeholders.
- [ ] The output format is specified.
- [ ] The prompt does not authorize edits to Hermes source checkout files unless the user explicitly requested fork/upstream development.
- [ ] After the prompt is enhanced, it is executed in-session unless the user requested prompt text only or execution is blocked by a required clarification/safety issue.
