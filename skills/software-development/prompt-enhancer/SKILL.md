---
name: prompt-enhancer
description: "Use when a user wants a prompt improved, clarified, made safer, or tailored to the current conversation. Produces context-aware prompts with explicit Hermes write-safety boundaries, then executes the enhanced prompt when safe."
version: 0.1.0
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

## Prompt Enhancement Procedure

### 1. Extract the intent

Identify these fields before rewriting the prompt:

- **User outcome:** What should exist or be true after the task?
- **Context:** What conversation facts, paths, files, docs, or constraints matter?
- **Session continuity:** What active task list items, unfinished work, or accumulated session context should continue while this prompt is executed?
- **Action type:** Answer only, plan only, read-only investigation, or write/execute task.
- **Write scope:** Whether the task may create, overwrite, edit, update, delete, commit, publish, or schedule anything.
- **Validation:** What objective tool output, file state, tests, docs, or command results prove correctness?

Completion criterion: every field is either filled or explicitly marked as an assumption/open question.

### 2. Convert unknowns into assumptions or questions

If the ambiguity changes what tool to call, what file to modify, or whether a write is safe, ask a brief clarifying question.

If the ambiguity is low-stakes, choose the safest default and label it as an assumption.

Safe defaults:

- Prefer read-only investigation before writes.
- Prefer user-local Hermes customization surfaces over source-code edits.
- Prefer `skill_manage` for user-local skills.
- Prefer `hermes config`, setup commands, or purpose-built tools over direct edits to sensitive config/credential files.
- Prefer a plan when the user invoked `/plan` or explicitly asks for a plan.
- For repository-author-authored new skills or config/toolbox/profile repositories, public or private, default to `version: 0.1.0`, `author: <repo-author-name>`, `license: Apache-2.0`, git author `<repo-author-name> <<private-term>>`, and no AI co-authoring commit trailers.
- For public Hermes config/toolbox/profile documentation, make tracked public content identity-neutral by default: describe generic customization mechanisms and future-update rules without specific profile names, personal plugin names, private paths, personal identifiers, or language that links public artifacts to the repository owner as a person unless the user explicitly approves those names.
- Treat approved authorship metadata as an explicit exception to public identity-neutrality for the repository owner's repos: public skill frontmatter may/should say `author: <repo-author-name>`, and repo-local Git config/commit metadata should use `<repo-author-name> <<private-term>>`. Do not rewrite repository-author-authored public skills to generic contributor names such as `Hermes Toolbox Contributors`, and do not use `noreply@example.com` for the repo Git identity.
- For public repo artifacts derived from private Hermes configuration, add an explicit identity-neutrality validator/check alongside public-safety validation. Public copies should use placeholders such as `$HERMES_HOME`, `$HOME`, `<profile>`, `<repo>`, `<user>`, and `example.com`; avoid private profile names, personal plugin names, private email addresses in tracked files, and user-specific absolute paths. Validators must allow approved `author: <repo-author-name>` skill metadata while rejecting personal/private context elsewhere.
- For public Hermes toolbox/profile repos, distinguish user-specific profiles from reusable role/use-case/category/responsibility profiles. Profiles prefixed `<first-name>-` are private/user-specific and must not be published. Profiles not prefixed `<first-name>-` may be published only as sanitized reusable profile packages: include declarative/profile metadata such as `PROFILE.md`, `config.public.yaml`, and `manifest.json`; strip `.env`, auth/OAuth/token stores, memories, sessions, logs, caches, `state.db*`, pairing state, cron outputs, and runtime/private data. Public tracked docs should describe the rule generically with `<first-name>-`; pass `<first-name>-` as a local private prefix via CLI/env/untracked config rather than hardcoding it into public docs/scripts.
- For public Hermes toolbox/plugin repos for this Hermes environment, gate public plugin publishing by source profile as well as sanitization: only plugins sourced from the `non-<first-name>-plugins` profile may be uploaded to the public repo. Plugins from global/default Hermes homes, `<first-name>-plugins`, any `<first-name>-*` profile, or any other profile stay private unless the user explicitly changes the source gate. Public plugin packages must be non-`<first-name>-` named, generic/reusable, manifest-backed, and stripped of `.env`, auth/OAuth/token stores, memories, sessions, logs, caches, `state.db*`, pairing state, cron outputs, and runtime/private data. Public tracked docs should describe this generically as a configured public-plugin-source profile; pass `non-<first-name>-plugins` via CLI/env/untracked config rather than hardcoding it in public prose.
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
- If execution requires writes or external side effects, enforce the enhanced prompt's scope and write-safety boundaries.
- Ask for clarification only when ambiguity changes the target, safety, or validation threshold.
- Verify the resulting work against the validation threshold; if validation fails, iterate or report the blocker honestly.
- If code/config/script changes lack a canonical test/lint/build command, create and run a focused temporary verifier under `/tmp` with a `hermes-verify-` filename prefix, then clean it up when practical. Label the result as ad-hoc verification, not suite green. See `references/ad-hoc-verification.md`.
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

- `references/public-private-hermes-repo-prompts.md` — prompt patterns for public/private Hermes config repositories, including identity-neutral public publishing and non-reinstallable private backup scoping.

## Common Pitfalls

1. **Enhancing the prompt but losing the user's actual outcome.** Keep the first sentence outcome-driven.
2. **Adding generic safety prose without exact paths.** Name allowed and prohibited paths explicitly.
3. **Treating a Hermes source checkout as a customization surface.** Normal users should use `$HERMES_HOME` skills/plugins/config/context files instead.
4. **Reading or rewriting secrets directly.** Use auth/setup/config flows; never ask the model to inspect raw secret stores unless the user explicitly provides a safe redacted excerpt.
5. **Ignoring profile boundaries.** A named profile has its own `$HERMES_HOME`; do not modify another profile's `skills/`, `plugins/`, `cron/`, or `memories/` without explicit direction.
6. **Over-asking.** Ask clarification only when ambiguity changes safety, target paths, or validation.
7. **No objective finish line.** Every enhanced prompt needs a validation threshold that can be proven by tool output or source content.
8. **Executing a saved plan loosely.** When the user says “execute this plan,” the saved plan becomes the scoped task brief. Read it first, keep its write boundaries, do not add adjacent work, and finish with the plan's own validation evidence.
9. **Dropping in-progress session work.** A prompt-enhancer invocation is normally additive. Do not treat it as a reset unless the user explicitly says to start over, discard prior work, or replace the current task.

## Verification Checklist

Before returning an enhanced prompt, confirm:

- [ ] The user's desired outcome is explicit.
- [ ] Relevant conversation context is included.
- [ ] The enhanced prompt includes session-continuity wording unless the user explicitly requested a reset or prompt text only.
- [ ] Assumptions and open questions are separated.
- [ ] The action mode is clear: answer, plan, read-only, or execute.
- [ ] Allowed write surfaces are exact.
- [ ] Prohibited/clarification-required write surfaces are exact.
- [ ] Hermes Agent claims are tied to official docs/repo or live tool output.
- [ ] The validation threshold is objective and finite.
- [ ] The output format is specified.
- [ ] The prompt does not authorize edits to Hermes source checkout files unless the user explicitly requested fork/upstream development.
- [ ] After the prompt is enhanced, it is executed in-session unless the user requested prompt text only or execution is blocked by a required clarification/safety issue.
