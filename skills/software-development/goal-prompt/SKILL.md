---
name: goal-prompt
description: "Use when turning a rough request into a copy-pasteable /goal prompt. Applies prompt-enhancer discipline to make the goal deterministic, finite, safe, and objectively judgeable."
version: 0.1.1
author: Kiren Srinivasan
license: Apache-2.0
metadata:
  hermes:
    tags: [prompting, goals, hermes-agent, workflow, validation]
    related_skills: [prompt-enhancer, hermes-agent]
---

# Goal Prompt

## Overview

Use this skill to transform an input request into a prompt that is safe and effective to run through Hermes' `/goal` command. `/goal` sets a standing goal Hermes works toward across turns; after each turn an auxiliary judge decides whether the goal is done or should continue. A good `/goal` prompt is therefore finite, self-contained, scoped, tool-grounded, and objectively judgeable.

This skill uses the `prompt-enhancer` discipline, but adapts it for persistent goal execution. The output should not just sound better; it should make the eventual `/goal` loop deterministic enough that another Hermes run can execute it, know what not to touch, validate completion, and stop as soon as the validation threshold is met.

By default, this is a **prompt-only** skill: produce the improved `/goal` prompt and do not execute the underlying task. Only start or mutate an active `/goal` if the user explicitly asks you to do so.

## When to Use

Use this skill when the user asks to:

- turn a rough task into a `/goal` prompt;
- make a long-running autonomous Hermes task safer or more deterministic;
- convert a desired outcome into a standing goal with explicit DONE criteria;
- harden a prompt for correct execution across multiple turns;
- prepare a goal prompt involving files, code, Hermes config, profiles, skills, plugins, cron, gateway, or other side effects.

Do not use this skill when:

- the user wants the task executed immediately rather than converted into a goal prompt;
- the request is a short factual answer with no persistent execution needed;
- the user invoked `/plan` and wants a plan file rather than a `/goal` prompt;
- there is no input prompt or desired outcome. Ask for the input instead.

## Required Input Extraction

Before writing the output prompt, extract these fields from the user's request and current session context:

1. **Desired outcome** — what should exist, change, or be proven true after `/goal` completes.
2. **Execution mode** — answer-only, read-only, plan-only, or execute. Default to execute only when the requested goal needs real work; otherwise choose the safer mode.
3. **Context** — relevant paths, repositories, profiles, docs, active task-list items, constraints, and user preferences.
4. **Write scope** — exact allowed write surfaces and explicit prohibited surfaces.
5. **External side effects** — commits, PRs, messages, deployments, purchases, scheduled jobs, profile/plugin/config changes, or public publishing.
6. **Source-of-truth checks** — docs, code, CLI output, tests, or live system state required before acting or finalizing.
7. **Validation threshold** — finite, objective conditions that prove the goal is complete.
8. **Stop condition** — what tells the `/goal` loop to stop rather than continue optimizing.

Completion criterion: every field is filled, explicitly marked as an assumption, or turned into a concise clarification question if guessing would change target, safety, privacy, or validation.

## Prompt-Enhancer Dependency

Apply the `prompt-enhancer` procedure when producing the goal prompt:

- Preserve the user's actual outcome.
- Include session continuity unless the user explicitly asked to reset.
- Convert low-stakes ambiguity into labeled assumptions.
- Ask only when ambiguity changes the target, write safety, privacy, approvals, or validation.
- Prefer read-only discovery before writes.
- Prefer user-local Hermes customization surfaces over Hermes source-code edits.
- Prefer official Hermes CLI/tools over direct edits to sensitive files.
- Include exact allowed and prohibited write surfaces for any task with side effects.
- Require objective validation against first-party docs, local source, tests, or live tool output.
- Do not fabricate outputs.

If the skill tool is available and the `prompt-enhancer` skill is not already loaded in the current context, load it before drafting. If it is already loaded, follow its current content as the source of truth.

## Goal-Mode Adaptation Rules

A normal enhanced prompt often tells the agent to execute immediately. A `/goal` prompt must instead be optimized for a persistent continuation loop.

### Make the goal finite

The output prompt must include a clear DONE state. Avoid goals like "keep improving," "monitor forever," or "make it as good as possible" unless the prompt also defines a bounded stopping rule.

Good:

- "Stop when the listed tests pass and the final answer includes the command output."
- "Stop when a plan file exists at the stated path and contains the required sections."
- "Stop if a required credential, approval, or inaccessible system blocks validation; report the blocker instead of continuing."

Bad:

- "Continue until everything is perfect."
- "Keep checking for updates."
- "Optimize the project."

### Make the judge's job easy

Because `/goal` uses a judge to decide DONE vs CONTINUE, include a compact checklist of completion criteria that can be evaluated from artifacts and tool output. Use numbered criteria, not vague prose.

The goal prompt should say:

```markdown
## DONE Criteria
The goal is complete only when all of these are true:
1. ...
2. ...
3. ...
```

### Prevent scope creep

The prompt must explicitly say not to broaden the task, not to perform adjacent cleanups, and not to keep iterating after the validation threshold is met.

### Preserve continuity without resetting

Unless the user explicitly asks to start over, include:

> Continue all previous and existing work within this session, using the accumulated session context and active task list. Treat this prompt as an additional steering instruction, not a reset.

### Handle blockers deterministically

The prompt should say what to do when the goal cannot be completed:

- If missing context is retrievable, retrieve it with tools.
- If missing context is not retrievable and changes safety or target, ask one concise clarification.
- If an external dependency blocks execution, report the blocker with the command or source that proved it.
- If a dangerous side effect is needed but not explicitly authorized, stop and ask for approval.

## Output Format

Return a copy-pasteable goal command by default:

````markdown
```text
/goal You are Hermes Agent operating in [mode] mode.

## Objective
...

## Context
- ...
- Continue all previous and existing work within this session, using the accumulated session context and active task list. Treat this prompt as an additional steering instruction, not a reset.

## Scope
Allowed actions:
- ...

Not in scope:
- ...

## Write Safety
Allowed write surfaces:
- ...

Prohibited or clarification-required write surfaces:
- ...

## Source-of-Truth Checks
- ...

## Execution Rules
- Use tools for current facts, file contents, git state, dates, calculations, and live validation.
- Do not fabricate outputs or claim success without tool-backed evidence.
- Do not broaden scope or perform adjacent cleanup.
- Stop immediately once the DONE criteria are met.

## DONE Criteria
The goal is complete only when all of these are true:
1. ...
2. ...
3. ...

## Blocker Rule
If the goal cannot be completed safely or verifiably, stop and report the blocker with evidence.

## Required Final Response
...
```
````

If the user asks for the prompt body without the `/goal` prefix, return only the body. If the input is too ambiguous to make safe, return:

```markdown
Clarification needed before I can produce a safe /goal prompt:
1. ...
```

## Write-Safety Defaults for Hermes Tasks

When the goal involves Hermes Agent itself, include these boundaries unless the user explicitly narrows or changes them.

Allowed or encouraged write surfaces:

- `$HERMES_HOME/config.yaml` for non-secret settings, preferably via `hermes config`.
- `$HERMES_HOME/.env` for secrets/API keys, preferably via setup/auth/config commands, not raw reads or manual edits.
- `$HERMES_HOME/SOUL.md` for global identity/personality.
- Project context files in the active workspace: `.hermes.md`, `HERMES.md`, `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.cursor/rules/*.mdc`.
- `$HERMES_HOME/memories/MEMORY.md` and `$HERMES_HOME/memories/USER.md`, preferably via the `memory` tool.
- `$HERMES_HOME/skills/<category>/<skill>/SKILL.md` and skill support directories `references/`, `templates/`, `scripts/`, `assets/`, preferably via `skill_manage`.
- `$HERMES_HOME/plugins/<plugin>/` for personal/team plugins.
- `$HERMES_HOME/cron/jobs.json` via `hermes cron` or the `cronjob` tool.
- Workspace `.hermes/plans/` for plan documents.

Prohibited or clarification-required write surfaces:

- Hermes source checkouts such as `$HERMES_HOME/hermes-agent/**`, `/usr/local/lib/hermes-agent/**`, or cloned `NousResearch/hermes-agent` repos unless the user explicitly requests upstream/fork development.
- Core source directories/files such as `agent/`, `tools/`, `toolsets.py`, `run_agent.py`, `model_tools.py`, `cli.py`, `hermes_cli/`, `gateway/`, `cron/`, `tui_gateway/`, and `acp_adapter/` for normal customization.
- Repo `plugins/`, repo `skills/`, and repo `optional-skills/` for personal customization.
- Another profile's `skills/`, `plugins/`, `cron/`, or `memories/` unless the user explicitly targets that profile.
- Credential/token stores by direct file read/write: `auth.json`, `.anthropic_oauth.json`, `mcp-tokens/`, project `.env*`, and similar secret stores.
- Runtime stores such as `state.db`, `sessions/`, `logs/`, `cache/`, `pairing/`, checkpoints, backups, venvs, managed Node, or managed `uv` unless using the official CLI/tool that owns them.

Completion criterion: a Hermes-related `/goal` prompt states exact allowed and prohibited surfaces instead of saying only "be safe."

## Public/Private Artifact Defaults

If the goal prompt could produce public repo artifacts, profile exports, plugin packages, docs, or backups, include privacy and authorship constraints:

- Public tracked content should be identity-neutral by default except approved skill frontmatter and approved repo-local Git identity.
- Public copies should use placeholders such as `$HERMES_HOME`, `$HOME`, `<profile>`, `<repo>`, `<user>`, and `example.com` instead of private profile names, private plugin names, personal identifiers, private emails, or user-specific absolute paths.
- Profiles prefixed with a person's first-name prefix are private/user-specific and must not be published unless explicitly approved.
- Public plugin packages must come only from the configured public-plugin-source profile and must be sanitized of auth, memory, sessions, logs, caches, state, pairing, cron outputs, and runtime data.
- Private backup prompts should distinguish non-reinstallable custom state from reinstallable/generated artifacts and require a manifest.

## Common Pitfalls

1. **Producing a plan instead of a goal prompt.** A plan may be useful, but the requested artifact is a copy-pasteable `/goal` command unless the user asks otherwise.
2. **Executing the task accidentally.** This skill prepares the standing goal. It does not start the goal loop unless explicitly asked.
3. **No finite stop condition.** Persistent goals need a hard DONE threshold or blocker rule.
4. **Vague validation.** "Looks good" is not judgeable. Use file paths, tests, command outputs, source links, or checklist items.
5. **Unsafe write scope.** Any goal that can edit files needs exact allowed and prohibited write surfaces.
6. **Forgetting first-party checks for Hermes tasks.** Validate Hermes claims against official docs, the official repo, local source when intentionally working on a clone, or live CLI/tool output.
7. **Ignoring default `/goal` budget.** Keep prompts focused enough to finish within the default continuation budget, or explicitly tell the agent to report a scoped blocker instead of widening the task.
8. **Letting continuation loops chase perfection.** The prompt must say to stop immediately once DONE criteria are met.

## Verification Checklist

Before returning a `/goal` prompt, confirm:

- [ ] The output is a copy-pasteable `/goal ...` command unless the user requested prompt body only.
- [ ] The original outcome is preserved.
- [ ] The prompt includes session-continuity wording unless reset was requested.
- [ ] The execution mode is explicit.
- [ ] Assumptions are labeled and no unsafe ambiguity remains.
- [ ] Allowed actions and exclusions are concrete.
- [ ] Any write surfaces are exact.
- [ ] Hermes-specific claims require official docs, official repo, local intended source, or live CLI/tool output.
- [ ] DONE criteria are finite, objective, and judgeable from artifacts or tool output.
- [ ] A blocker rule prevents unsafe or unverifiable continuation.
- [ ] The required final response format is specified.
- [ ] The prompt tells Hermes not to broaden scope and to stop once the threshold is met.
