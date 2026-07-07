---
name: plugin-builder
description: "Use when the user wants Hermes to design, validate, confirm, and create a customized Hermes plugin through a prompt-enhanced goal-to-plugin-primitives collaboration loop."
version: 0.1.0
author: Kiren Srinivasan
license: Apache-2.0
metadata:
  hermes:
    tags: [plugins, hermes-agent, prompting, validation, workflow]
    related_skills: [prompt-enhancer, hermes-agent, hermes-agent-skill-authoring]
---

# Plugin Builder

## Overview

Use this skill to guide a user from a rough plugin idea to an agreed, validated, gold-standard Hermes plugin specification, then create the plugin only after explicit user agreement. The process is conversational, but not casual: every user reply is normalized through the `prompt-enhancer` procedure, every important decision is checked against Hermes plugin requirements, every user goal and desired outcome is captured, and every proposed plugin detail is validated before build.

The builder must treat goals as first-class plugin design inputs. When the user describes what they want to achieve, why they need a plugin, or what outcomes the plugin should produce, preserve those goals in the running spec and map each one across the Hermes plugin primitive set: identity, extension surface, capabilities, inputs/outputs, config/secrets, safety, performance, implementation, validation, final agreement, manifest, registration APIs, runtime contracts, and enablement/distribution. The result should be a plugin designed to achieve the user's stated goals through the new plugin itself, not by relying on unrelated default Hermes behavior.

The goal is to get to a customized, correct, fast plugin as quickly as possible by combining strong defaults, small clarification loops, read-only background validation, explicit goal-to-primitives coverage, and a final explicit agreement step.

## When to Use

Use this skill when the user wants to:

- Create a new Hermes plugin.
- Design or configure a plugin before implementation.
- Decide which Hermes extension surface to use.
- Convert a rough integration idea into plugin files.
- Build tools, hooks, slash commands, CLI commands, bundled skills, or provider backends.
- Validate that a plugin plan is safe, correct, fast, and aligned with Hermes best practices.

Do not use this skill when:

- The user only wants a direct factual answer about plugins.
- The user only wants a skill, not a plugin-building workflow.
- A simple skill, MCP server, shell hook, TTS/STT command provider, or config change is clearly the better surface and no plugin should be created.

## Mandatory Setup

At the start of a plugin-building session:

1. Load `prompt-enhancer` with `skill_view(name="prompt-enhancer")` unless its full instructions are already present in the session.
2. Load `hermes-agent` with `skill_view(name="hermes-agent")` unless already loaded.
3. Validate current plugin facts against official docs or live CLI/source before making strong claims.
4. Keep a working plugin specification in the conversation. If the spec becomes large, summarize it into a compact structured block before asking the next question.

Completion criterion: the agent has the prompt-enhancer procedure available, knows the active Hermes plugin rules, and has started or updated the structured plugin spec.

## Prompt-Enhanced Intake Contract

Every user reply in the plugin-building conversation must pass through the `prompt-enhancer` procedure before the agent acts on it.

For each user reply:

1. Treat the reply as a rough prompt or configuration update.
2. Apply `prompt-enhancer` extraction:
   - user outcome
   - relevant context
   - action type
   - write scope
   - validation threshold
   - plugin goals
   - desired outcomes
   - success measures
   - non-goals
   - why the outcome should be achieved by a plugin instead of a lighter Hermes primitive
   - assumptions/open questions
3. Update the plugin spec, `goals` section, and goal-to-plugin-primitives coverage matrix with only the confirmed or safely assumed details.
4. If ambiguity changes the plugin surface, goal interpretation, target paths, security model, credentials, destructive behavior, or validation threshold, ask a brief clarifying question.
5. If ambiguity is low-stakes, choose the safest default and label it as an assumption.
6. Do not display the full enhanced prompt unless it helps the user review a decision or the user asks for it.

When a user reply includes a goal or desired outcome, do not leave it as conversational context only. Convert it into a compact `goals.stated[]` or `goals.desired_outcomes[]` entry, then evaluate it against every plugin primitive category. If a primitive is irrelevant, mark it `not_applicable` or `skipped` with a reason. If a primitive is blocked by missing credentials, external service setup, unsafe writes, missing plugin support, or user decision, mark it `blocked` with the exact blocker and user action needed.

Completion criterion: no raw user reply directly changes the plugin plan without prompt-enhancer normalization, safety review, and goal coverage update.

## Working Plugin Specification

Maintain this spec throughout the conversation. Use it as the single source of truth.

For the local Hermes environment, also apply the plugin-profile routing convention in `references/plugin-profile-routing.md` before choosing a target plugin path: user-specific plugins belong to `<first-name>-plugins` and must start with `<first-name>-`; reusable/non-user-specific plugins belong to `non-<first-name>-plugins` and must remain identity-neutral.

```yaml
plugin_spec:
  identity:
    plugin_name: null
    human_label: null
    one_sentence_goal: null
    target_users: []
  goals:
    stated: []                    # user's compact goal statements
    desired_outcomes: []          # observable results the plugin should produce
    non_goals: []                 # outcomes explicitly out of scope
    success_measures: []          # how the user will know the plugin works
    assumptions: []               # inferred goals/defaults not explicitly stated
    goal_to_primitives:
      - goal: null
        desired_outcome: null
        primitive_coverage:
          identity: []            # name, label, one-sentence goal, target users
          extension_surface: []   # chosen/rejected surfaces and why
          capabilities: []        # tools, hooks, slash commands, CLI commands, skills, providers, data files
          inputs_outputs: []      # user inputs, schemas, JSON shapes, visible outputs
          config_and_secrets: []  # env vars, config keys, credential handling
          safety: []              # write boundaries, side effects, approvals, redaction
          performance: []         # lazy loading, timeouts, caching, schema budget
          implementation: []      # plugin path, files, dependencies
          validation: []          # docs, CLI checks, tests, prompts, debug commands
          final_agreement: []     # agreement wording and confirmation requirements
          manifest: []            # plugin.yaml fields, kind, provides_*, requires_env
          registration: []        # ctx.register_* or provider/backend registration APIs
          runtime_contracts: []   # handler, hook, command, provider contracts
          enablement_distribution: [] # enablement/trust config/install/update/docs
        not_applicable: []        # primitive names intentionally skipped with reason in notes
        unmapped_primitives: []   # must be empty before final agreement unless blocked
        status: pending | mapped | skipped | blocked
        notes: null
  extension_surface:
    chosen_surface: null       # general, platform, model-provider, memory, context-engine, image_gen, video_gen, web, browser, tts, stt, mcp, shell-hook, skill-only
    why_this_surface: null
    rejected_surfaces: []
  capabilities:
    tools: []
    hooks: []
    slash_commands: []
    cli_commands: []
    bundled_skills: []
    providers: []
    data_files: []
  inputs_outputs:
    user_inputs: []
    tool_schemas: []
    returned_json_shapes: []
    user_visible_outputs: []
  config_and_secrets:
    required_env: []
    optional_env: []
    config_yaml_keys: []
    credential_handling: null
  safety:
    allowed_write_surfaces: []
    prohibited_write_surfaces: []
    external_side_effects: []
    approval_requirements: []
    secret_redaction_notes: []
  performance:
    import_time_budget: "no heavy imports/network/client construction at import/register time"
    runtime_timeouts: []
    lazy_loading_plan: []
    caching_plan: []
    token_schema_budget: null
  implementation:
    target_plugin_path: null
    files_to_create: []
    files_to_modify: []
    dependencies: []
  validation:
    docs_checked: []
    cli_checks: []
    tests: []
    manual_prompts: []
    debug_commands: []
  final_agreement:
    status: "not_ready"       # not_ready, ready_for_review, agreed, rejected
    user_confirmed_at: null
```

Completion criterion: every required field is either filled, explicitly marked not applicable, or represented as an open question.

## Goal-to-Plugin-Primitive Mapping Rules

Treat goal mapping as a compact coverage matrix, not as a prose summary. For every stated goal or desired outcome:

1. Evaluate every plugin primitive category: `identity`, `extension_surface`, `capabilities`, `inputs_outputs`, `config_and_secrets`, `safety`, `performance`, `implementation`, `validation`, `final_agreement`, `manifest`, `registration`, `runtime_contracts`, and `enablement_distribution`.
2. Add the concrete plugin choice, manifest field, public registration API, tool schema, hook/command/provider contract, config/env requirement, file path, dependency, validation command, or policy that represents the goal in that primitive.
3. If a primitive does not apply to the goal, add it to `not_applicable[]` with a short reason in `notes`; do not leave it silently empty.
4. If a primitive is blocked by missing auth, credentials, external setup, unsafe writes, lack of Hermes support, or user decision, record it in the relevant blocked field and in `validation.debug_commands` or an explicit blocker note.
5. Do not present the final plugin agreement while any `unmapped_primitives[]` remain unless they are explicitly blocked and surfaced to the user.

A goal is fully covered only when the new plugin can carry the needed behavior through its own approved plugin primitives. Do not assume default Hermes behavior, a profile setting, or a separate skill will achieve the goal unless the final agreement explicitly includes that dependency and explains why it is not part of the plugin.

## Gold-Standard Requirements

A plugin is gold-standard only when all relevant gates pass.

### 0. Goal coverage gate

Capture and map the user's goals before final agreement.

Requirements:

- User goals, desired outcomes, success measures, and non-goals are captured or intentionally defaulted.
- The spec explains why the outcomes should be achieved by a Hermes plugin instead of a lighter primitive such as a skill, MCP server, shell hook, setup/config change, or profile customization.
- Every stated goal maps across the full plugin primitive set or each non-applicable/blocked primitive is explicitly marked with a reason.
- Every mapped goal has at least one validation command, test, manual prompt, or observable success criterion.

Completion criterion: every goal is `mapped`, `skipped`, or `blocked`, and no unmapped plugin primitive category remains hidden.

### 1. Surface-fit gate

Confirm the right extension surface before designing files.

| User wants | Prefer |
| --- | --- |
| Model-callable custom tools, hooks, slash commands, CLI commands, bundled skills | General Python plugin |
| External service tools with many existing tools | MCP server, if available |
| Simple event-triggered shell behavior | Shell hook or gateway hook |
| New LLM/inference backend | Model provider plugin |
| New messaging channel | Platform plugin |
| Cross-session memory backend | Memory provider plugin |
| Context compression strategy | Context engine plugin |
| Image/video/web/browser backend | Backend plugin |
| TTS/STT shell command | Config-driven command provider before Python plugin |
| Reusable agent instructions only | Skill, not plugin |

Completion criterion: the chosen surface is justified and at least one plausible alternative has been rejected for a concrete reason.

### 2. Write-safety gate

Normal plugin creation may write only under:

- `$HERMES_HOME/plugins/<plugin-name>/`
- `$HERMES_HOME/plugins/<category>/<plugin-name>/` for categorized providers/backends
- trusted project-local `.hermes/plugins/<plugin-name>/` only when explicitly enabled and trusted
- user-local skills bundled inside the plugin directory, registered read-only via `ctx.register_skill()`

On the local Hermes environment, `$HERMES_HOME` for generated plugins should usually be the owning plugin workshop profile from `references/plugin-profile-routing.md`: `<first-name>-plugins` for private/user-specific plugins and `non-<first-name>-plugins` for reusable/non-user-specific plugins. Treat writes to any other profile's `plugins/` tree as clarification-required unless the user explicitly approved that target.

Do not write to Hermes source checkout files, bundled repo `plugins/`, bundled repo `skills/`, runtime databases, logs, caches, credential stores, or another profile unless the user explicitly requests that target.

Completion criterion: exact intended write paths, owning profile, and privacy/routing classification are stated before any write happens.

### 3. Manifest gate

General directory plugins need:

```text
plugin.yaml or plugin.yml
__init__.py with register(ctx)
```

Recommended manifest fields:

```yaml
name: my-plugin
kind: standalone
version: 1.0.0
description: Clear one-line description
provides_tools: []
provides_hooks: []
requires_env: []
```

Use explicit `kind`: `standalone`, `backend`, `exclusive`, `platform`, or `model-provider`.

Completion criterion: manifest fields match the chosen extension surface and all secrets are declared through `requires_env` or setup flow rather than hardcoded.

### 4. Registration gate

Use supported public APIs only:

- `ctx.register_tool(...)`
- `ctx.register_hook(...)`
- `ctx.register_command(...)`
- `ctx.register_cli_command(...)`
- `ctx.register_skill(...)`
- `ctx.dispatch_tool(...)`
- `ctx.llm.complete(...)` / `ctx.llm.complete_structured(...)`
- specialized provider registration APIs for platform/provider/backend plugins

Do not reach into private internals such as `ctx._cli_ref.agent`.

Completion criterion: each desired capability maps to one public registration API.

### 5. Tool schema gate

Every model-callable tool schema must be minimal, precise, and useful.

Requirements:

- Stable unique name.
- Description says exactly when to use the tool.
- JSON Schema parameters are explicit.
- Required fields are listed.
- Schema avoids unnecessary options and long prose.
- Tool count is minimized to protect prompt speed.

Completion criterion: the model can infer when to call each tool without reading external docs.

### 6. Handler gate

Tool handlers must follow this contract:

```python
def handler(args: dict, **kwargs) -> str:
    ...
```

Handlers must:

- return JSON strings, including errors
- catch exceptions
- validate inputs
- accept `**kwargs`
- avoid printing secrets
- use timeouts for network calls
- keep outputs compact

Completion criterion: success and failure paths produce valid JSON strings and no expected bad input raises uncaught exceptions.

### 7. Hook and command gate

Hooks must be fast, bounded, and forward-compatible:

- accept `**kwargs`
- avoid slow inline work
- catch/log errors or let Hermes isolate them safely
- return only documented directive shapes

Slash commands must:

- avoid built-in command name conflicts
- accept raw string args
- return user-readable output or `None`
- use `ctx.dispatch_tool()` for tool orchestration

Completion criterion: every hook/command has a clear purpose and can fail without breaking the agent.

### 8. Config and credential gate

- Secrets go in env/setup flows, not source files.
- Non-secret behavior goes in `config.yaml` or plugin config docs.
- Provider/model override for `ctx.llm` requires explicit `plugins.entries.<plugin>.llm.*` trust config.
- Built-in tool override requires explicit `plugins.entries.<plugin>.allow_tool_override: true` for non-bundled plugins.

Completion criterion: no secret or trust boundary is implicit.

### 9. Performance gate

A fast plugin must:

- avoid heavy imports at module import time
- avoid network calls during import/register
- avoid client construction during import/register
- lazy-load optional dependencies
- use thread-safe lazy singletons for expensive clients
- set HTTP/API timeouts
- cache stable metadata
- avoid repeated LLM calls
- keep schemas and injected context small

Completion criterion: `register(ctx)` only registers capabilities and cheap checks; real work happens lazily at call time.

### 10. Validation gate

Before declaring the plugin ready, plan and execute validation appropriate to the plugin:

```bash
HERMES_PLUGINS_DEBUG=1 hermes plugins list
hermes plugins enable <plugin-name>
hermes plugins list
hermes chat -q "Use <plugin capability> for a simple test."
hermes chat -q "/<plugin-command> status"     # if slash command exists
hermes <plugin-cli-command> status             # if CLI command exists
```

Also validate:

- handler unit tests
- missing-env behavior
- bad-input behavior
- JSON output parsing
- logs have no plugin load errors
- no writes occurred outside approved surfaces

Completion criterion: objective command/test output proves discovery, load, capability behavior, and error handling.

## Fast Collaboration Loop

Use this loop after every user reply until the final agreement is ready.

1. **Prompt-enhance the reply.** Apply the prompt-enhancer extraction, goal extraction, and safety boundaries.
2. **Update the spec.** Add confirmed facts, safe defaults, open questions, and `goals.goal_to_primitives[]` coverage.
3. **Validate in the background.** Use read-only checks against official docs, live CLI/source, existing examples, and the current spec. Do not repeat expensive checks if already current.
4. **Score against gates.** Mark each gold-standard gate as pass, fail, or unknown, including the goal coverage gate.
5. **Ask the smallest useful question set.** Ask at most three questions, only when the answer changes goal interpretation, surface, safety, target paths, credentials, outputs, or validation.
6. **Offer defaults.** For low-stakes choices, propose a default and continue unless the user objects.
7. **Stop when ready.** Once all blocking gates pass, move to the final agreement protocol.

Completion criterion: each turn either reduces unknowns, validates a gate, or reaches final agreement review.

## Question Strategy

Prefer decision prompts over open-ended questionnaires.

The first plugin-builder question should explicitly invite goals without creating a long form:

```text
What should this new Hermes plugin help you achieve? Share any goals, desired outcomes, non-goals, target workflow, external services, read/write side effects, credentials, preferred interface, and validation examples you already know. If you do not care about a category, say “default it” and I will choose safe defaults.
```

Map every answer through `prompt-enhancer` before updating the plugin spec and goal-to-plugin-primitives matrix.

Good:

```text
I can make this a general plugin with two tools and one /status command. That is faster and safer than a platform adapter because no new gateway channel is needed. Any objection before I draft the final agreement?
```

Avoid:

```text
Please describe every possible detail of your plugin.
```

Ask only about:

- desired outcome/user workflow
- external service/API involved
- whether actions are read-only or can write/publish/delete
- credentials/env vars required
- target interface: tool, slash command, CLI command, hook, provider, platform
- output format and validation examples
- final agreement before writing plugin files

Completion criterion: the user never has to answer a question that Hermes can safely infer or validate itself.

## Final Agreement Protocol

Before creating plugin files, present a compact final agreement:

```markdown
## Final Plugin Agreement

Plugin name: ...
Owning plugin profile: `<first-name>-plugins` | `non-<first-name>-plugins` | other explicitly approved target
Privacy/routing class: user-specific/private | reusable/non-user-specific
Extension surface: ...
Goal: ...
Goals and desired outcomes:
- Goal: ...
  - Desired outcome / success measure: ...
  - Primitive coverage: `identity=...`, `extension_surface=...`, `capabilities=...`, `inputs_outputs=...`, `config_and_secrets=...`, `safety=...`, `performance=...`, `implementation=...`, `validation=...`, `final_agreement=...`, `manifest=...`, `registration=...`, `runtime_contracts=...`, `enablement_distribution=...`
  - Not applicable / skipped primitives: ...
  - Status: `mapped|skipped|blocked`
Non-goals / intentionally skipped outcomes: ...
Goal coverage status: every goal has every plugin primitive category mapped, marked not applicable/skipped, or blocked; no unmapped primitives remain.
Capabilities:
- Tools: ...
- Hooks: ...
- Slash commands: ...
- CLI commands: ...
Files to create:
- `$HERMES_HOME/plugins/.../plugin.yaml`
- `$HERMES_HOME/plugins/.../__init__.py`
- ...
Config/secrets:
- Required env: ...
- Config keys: ...
Safety:
- Allowed writes: ...
- Prohibited writes: ...
Performance plan:
- ...
Validation plan:
- ...

Please reply `I agree` to create this plugin, or describe what to change.
```

Rules:

- Do not create the plugin before explicit agreement.
- Do not create the plugin while any stated goal has unmapped primitive categories unless those primitives are explicitly blocked and accepted by the user.
- If the user agrees, execute the creation plan immediately and validate it.
- If the user changes anything or does not agree, return to the fast collaboration loop.
- Treat agreement as scoped only to the listed files/actions.

Completion criterion: the user explicitly agrees to a concrete file/action/config list.

## Creation Protocol After Agreement

After agreement:

1. Create only the agreed files under the allowed plugin path.
2. Use direct file tools for plugin files or exact commands only when necessary.
3. Enable the plugin only if the agreement included enablement.
4. Run discovery/debug validation.
5. Run minimal behavior validation.
6. Validate every `goals.goal_to_primitives[]` entry with command output, test output, file inspection, or a clearly stated blocker.
7. Fix failures inside the agreed scope.
8. Report final paths, commands run, objective results, and goal coverage evidence.

Completion criterion: plugin exists, loads, performs the agreed capability, and passes the agreed validation threshold.

## Common Pitfalls

1. **Skipping prompt-enhancer after the first turn.** Every user reply can change safety or scope; re-run the prompt-enhancer extraction each time.

2. **Building before agreement.** The final agreement is mandatory because plugins can run arbitrary Python inside Hermes.

3. **Choosing a plugin when a skill or MCP server is better.** Always pass the surface-fit gate first.

4. **Loading heavy SDKs at import time.** Keep imports and client construction lazy so Hermes startup stays fast.

5. **Returning Python dicts from handlers.** Tool handlers must return JSON strings.

6. **Using vague tool descriptions.** The description is how the model decides whether to call the tool; vague schemas create wrong calls and wasted tokens.

7. **Hardcoding secrets.** Declare secrets with `requires_env` and use setup/auth/config flows.

8. **Writing to Hermes core.** User/team plugins belong under `$HERMES_HOME/plugins/` or trusted project `.hermes/plugins/`, not the Hermes source tree.

9. **Over-asking.** Ask only when the answer changes safety, target, implementation, or validation.

10. **No objective finish line.** Every plugin needs concrete validation commands and expected results before build.

11. **Treating goals as chat context instead of plugin design inputs.** Every stated goal must become a compact `goals` entry and map across the plugin primitive set or be explicitly skipped/blocked.

12. **Dumping all goals into the one-sentence plugin goal.** The identity goal is only one primitive. Goals usually also imply extension surface, capabilities, inputs/outputs, config/secrets, safety, performance, implementation, validation, manifest, registration, runtime contracts, and enablement choices.

13. **Letting default Hermes behavior carry the goal.** If the user wants the new plugin to achieve an outcome, the final agreement must include the plugin primitive or explicit dependency that carries that behavior.

14. **Leaving not-applicable primitives implicit.** A primitive that does not apply still needs a short reason, otherwise the goal coverage matrix cannot prove the category was considered.

## Verification Checklist

Before final agreement:

- [ ] Latest user reply passed through prompt-enhancer extraction.
- [ ] Plugin spec is current and compact.
- [ ] User goals, desired outcomes, success measures, and non-goals are captured in the plugin spec.
- [ ] Every user goal maps across the Hermes plugin primitive set or each primitive is explicitly `not_applicable`, `skipped`, or `blocked`.
- [ ] The spec explains why the new plugin, not default Hermes behavior or a lighter primitive, is responsible for the stated outcomes.
- [ ] Final agreement preview includes goal coverage and has no unmapped primitive categories.
- [ ] Correct extension surface chosen and justified.
- [ ] Exact write paths listed.
- [ ] Prohibited write paths listed.
- [ ] Manifest fields planned.
- [ ] Registration APIs selected.
- [ ] Tool schemas drafted, if any.
- [ ] Handler JSON/error contract planned, if any.
- [ ] Hooks/commands/provider APIs planned, if any.
- [ ] Env vars and config keys listed.
- [ ] Performance plan avoids import/register-time work.
- [ ] Validation plan has objective commands/tests.
- [ ] User has seen the final plugin agreement.
- [ ] User explicitly agreed before file creation.

After creation:

- [ ] Plugin files exist only in agreed paths.
- [ ] `HERMES_PLUGINS_DEBUG=1 hermes plugins list` shows expected discovery/load state.
- [ ] Plugin is enabled only if agreed.
- [ ] Tool/command/provider behavior was exercised.
- [ ] Bad-input/missing-env behavior is graceful.
- [ ] Logs show no plugin load errors.
- [ ] Post-creation validation reports each goal mapping with evidence or a blocker.
- [ ] Final response reports actual validation evidence.
