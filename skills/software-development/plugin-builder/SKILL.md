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

<!-- coding-contract-propagation:start -->
## Coding Contract Propagation

Every plugin design and build inherits the exact Universal Coding Contract for Code Work from `prompt-enhancer`. It is a mandatory gate across the working spec, final agreement, implementation, and validation—not optional style guidance.

```yaml
coding_contract:
  max_file_physical_lines: 200
  max_construct_physical_lines: 30
  max_nesting_depth: 3
  test_nesting_baseline: test_declaration
  tdd_sequence: [BOOTSTRAP, RED, GREEN, REFACTOR]
  real_tests_only: true
  prohibited_test_doubles: [mocks, stubs, fakes, spies, placeholders]
  test_targets: [user-facing situations, public contracts, APIs, integration boundaries, interfaces]
```

Before final agreement, list the real-service test path, the exact command that will witness RED before production code, and language-aware validation commands for file length, construct length, and nesting. Missing credentials, paid-call approval, or a real service are blockers, not permission to simulate.

After agreement, build one vertical behavior slice at a time as `BOOTSTRAP → RED → GREEN → REFACTOR`. Do not create or approve source/tests containing TODOs, mocks, stubs, fakes, spies, placeholders, synthetic success responses, skipped/xfail placeholders, implementation-detail assertions, or tests written for testing’s sake.

Plugin completion fails if any created or modified source/test file exceeds 200 physical lines, any named construct exceeds 30 physical lines, semantic nesting exceeds three, RED was not witnessed first, or behavior evidence comes from a test double instead of real functionality and integration paths.
<!-- coding-contract-propagation:end -->

## Working Plugin Specification

Maintain this spec throughout the conversation. Use it as the single source of truth.

For the local Hermes environment, also apply the plugin-profile routing convention in `references/plugin-profile-routing.md` before choosing a target plugin path: user-specific plugins belong to `<first-name>-plugins` and must start with `<first-name>-`; reusable/non-user-specific plugins belong to `non-<first-name>-plugins` and must remain identity-neutral.

Before writing into any workshop, distribution, or public-source profile, load `references/plugin-source-automation-preflight.md`. Check cron jobs, watchers, and export scripts that may consume every new plugin directory. Local source creation, consumer installation, candidate export, and publication are separate approvals; pause only the relevant downstream publisher when unapproved automation would otherwise act, and do not resume it without an explicit decision or package opt-out.

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
    coding_contract:
      max_file_physical_lines: 200
      max_construct_physical_lines: 30
      max_nesting_depth: 3
      test_nesting_baseline: test_declaration
      tdd_sequence: [BOOTSTRAP, RED, GREEN, REFACTOR]
      real_tests_only: true
      prohibited_test_doubles: [mocks, stubs, fakes, spies, placeholders]
      test_targets: [user-facing situations, public contracts, APIs, integration boundaries, interfaces]
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

## Kanban Workflow Plugin Extensions

When a plugin request mentions Kanban, phase workers, multi-profile workflows, approval gates, context bundles, board automation, or side-effecting workflow actions, load `references/kanban-workflow-plugin-extensions.md` before choosing an extension surface. Prefer profile distributions, skills, config, MCP, cron, and existing Kanban CLI/tool surfaces before creating a plugin. If a plugin is still justified, validate native dependency and task-scoping semantics, preserve `work_key`/`work_run` and `context_bundle`, bind the active profile through `ctx.profile_name`, keep model tools preview-only, use exact-token human confirmation for side effects, and state external CLI/dashboard enforcement limits explicitly.

When the user requires universal Kanban enforcement but forbids upstream/core edits, also load `references/external-kanban-policy-brokers.md`. Distinguish semantic compatibility from unchanged direct-native mutation UX before planning. A profile plugin alone is insufficient: the strongest no-core design uses a dedicated OS-owned reference monitor, broker-backed human and worker tools, a separate user-side workspace launcher, fail-closed native surfaces, per-run worker compatibility snapshots, and exact-version compatibility holds. Treat source creation, consumer installation, privileged deployment, cutover, and publication as separate approvals.

## External Detector Feedback-Loop Plugins

When a plugin will call an external evaluator/detector API, run release-readiness checks, loop on feedback, or update reusable learnings from detector results, load `references/external-detector-feedback-loop-plugins.md` before final agreement. Treat API calls as external side effects, declare keys through `requires_env`, keep handlers lazy/time-bounded, distinguish in-progress/success/failure/timeout states, and do not claim live detector validation unless credentials and approved calls actually ran.

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
  - Pass a `pathlib.Path` pointing to the actual bundled `SKILL.md` file. Do not pass the skill directory or a string path; live `PluginContext.register_skill` calls `.exists()` on the `Path` and registers the file itself.
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

For profile-installed plugins copied from a workshop/source profile, also run a source/runtime hygiene check: remove `__pycache__/` and other generated runtime artifacts before comparing source and installed trees, then use `diff -qr` or a manifest hash check on source files only. A mismatch caused only by bytecode caches is not plugin content drift; clean it up and recheck. Run syntax compilation before the final hygiene scan: explicit `python3 -m py_compile` writes `.pyc` files even when `PYTHONDONTWRITEBYTECODE=1`, so remove the resulting cache afterward or compile a temporary copy outside the package tree.

Use a fresh-process real Hermes `PluginManager`/`PluginContext` discovery probe for registration feedback. Exercise actual registered capabilities, host dispatch, active-profile derivation, command conflicts, toolset filtering, `register_skill(Path-to-SKILL.md)`, real handlers, and approved real services; verify `hermes -p <profile> tools list` exposes the plugin toolset. If the real manager or service cannot run, report a blocker instead of substituting a fake registration context.

Before final tests, review, structural scans, or commits, establish **writer quiescence**: every delegated/background coding process that can modify the target tree must have exited or been stopped, and Git HEAD/status must remain stable across the verification window. A test run racing an active writer is only transient evidence—do not repair, commit, or report it until the writer finishes and the changed file is re-read. Treat subagent summaries as unverified claims: compare tool/schema counts, paths, commits, and side effects against the live source/tree before encoding them into contracts.

Completion criterion: objective command/test output from a quiescent tree proves discovery, load, capability behavior, source/runtime install hygiene, and error handling.

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
Coding contract: 200-line file limit; 30-line construct limit; depth-3 nesting limit; test-declaration baseline; real-service test path; witnessed RED command; BOOTSTRAP/RED/GREEN/REFACTOR validation; no test doubles or implementation-detail assertions.
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

## Creation / Installation Protocol After Agreement

For standalone directory plugins whose plugin directory is also the repository root, and for plugins tested against a live local service, follow `references/standalone-plugin-real-service-tdd.md`. It covers fresh-process real-manager probes, pytest's repository-root `__init__.py` import trap, named temporary profile isolation while retaining real-service connectivity, reversible approval-state testing, complete native-output security projections, incrementally bounded subprocess capture, fail-closed fixture cleanup across setup failures, and clean checkpoint boundaries.

When a plugin consumes a private one-time catalog and updates durable state—identity seeds, restore mappings, approval files, or similar—follow `references/one-time-private-file-consumption.md`. It defines lock-before-read ordering, exact-`0600` no-follow validation, descriptor-only same-inode consumption without any post-open pathname mutation, secure atomic ledger writes, and the required TDD race/filesystem matrix. Do not introduce random claim paths as a TOCTOU workaround.

After agreement:

When an independent security review finds dispatch, output-bounding, sanitization, caller-binding, schema, or real-test-resource defects, follow `references/security-review-remediation.md` before committing or installing. It includes the complete-operation argv gate, incremental subprocess capture pattern, all-native-string sanitation scope, virtualenv interpreter pitfall, collision-safe fixtures, and staged re-review gate.

1. BOOTSTRAP the approved real test environment, real services, structural validators, and focused test command without writing production code.
2. RED: write one user-facing/public-contract/API/integration/interface behavior test and run it to witness the expected missing-behavior failure.
3. GREEN: create only enough real production code under the allowed plugin path to pass that test, then run the focused and relevant full suites.
4. REFACTOR while green and re-run language-aware file-length, construct-length, and nesting validation.
5. Repeat the vertical cycle for each agreed behavior.
6. Enable the plugin only if the agreement included enablement.
7. Run real discovery, registration, host-dispatch, service, and error-path validation.
8. Validate every `goals.goal_to_primitives[]` entry with real command/test/file evidence or a clearly stated blocker.
9. Fix failures inside the agreed scope without weakening tests or adding test doubles.
10. Report final paths, witnessed RED/GREEN commands, structural checks, and goal coverage evidence.

When the user asks to install an already-existing plugin into a named profile, follow `references/profile-plugin-install-verification.md`: target the named profile's `$HERMES_HOME/plugins/<plugin-name>/`, enable with `hermes -p <profile> plugins enable <plugin-name> --no-allow-tool-override` unless override was explicitly approved, and verify via JSON plugin listing, config state, syntax/import sanity, and a focused registration smoke test when applicable.

When the user approves a large profile-local plugin suite or asks to execute an entire profile spec with many plugins, follow `references/profile-plugin-suite-generation.md`: preserve the profile spec's side-effect gates, validate with `HERMES_HOME` pinned to the target profile, use the global plugin manager for hook checks, prevent duplicate tool-name collisions, run with `PYTHONDONTWRITEBYTECODE=1` for hygiene scans, and account for `HERMES_KANBAN_BOARD` overriding persisted board selection.

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

15. **Substituting a fake registration context.** Do not use one. Validate registration, host state, path types, dispatch, and tool visibility through a fresh-process real plugin-manager load before installation.

16. **Letting the model self-confirm side effects.** A model-callable `confirm` boolean is not human approval. Keep model tools preview-only and bind human slash confirmation to a short-lived, single-use token for the exact canonical operation.

17. **Parsing presentation-truncated JSON.** Parse complete native output first, validate its shape, then truncate only the human-visible rendering. Never fall back from an unresolved label to treating that label as an internal ID.

18. **Confusing plugin enablement with model visibility.** `plugins list` can be green while a custom toolset is filtered out. Check `tools list` and a fresh agent process for each approved consumer profile.

19. **Ignoring native dependency semantics.** If child promotion requires a parent to reach `done`, a successful phase must complete rather than block for a later reviewer. Validate task-scoped versus orchestrator-only tools before writing worker instructions.

20. **Overclaiming hook enforcement.** `pre_tool_call` protects only processes and tool calls that load the plugin. External CLI, dashboard, cron, and scripts require first-party enforcement or must be reported as a boundary/drift source.

## Verification Checklist

Before final agreement:

- [ ] Latest user reply passed through prompt-enhancer extraction.
- [ ] `implementation.coding_contract` records the 200-line file, 30-line construct, depth-3 nesting, test-declaration baseline, and BOOTSTRAP/RED/GREEN/REFACTOR gates.
- [ ] The final agreement names the real-service test path, witnessed RED command, and parser/language-aware structural validation commands.
- [ ] Tests target user-facing situations, public contracts, APIs, integration boundaries, or interfaces without mocks, stubs, fakes, spies, placeholders, or implementation-detail assertions.
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
- [ ] A real fresh-process `PluginManager`/`PluginContext` probe validates registration contracts.
- [ ] `hermes -p <profile> tools list` shows each intended plugin toolset in every approved consumer profile.
- [ ] Active-profile binding and cross-profile rejection were tested.
- [ ] Model-callable side-effect tools cannot self-confirm; any human token is exact-operation-bound, single-use, and expiry-tested.
- [ ] Unknown flags, ambiguous labels, missing canonical board, malformed/large native output, timeouts, and nonzero command exits fail closed.
- [ ] Tool/command/provider behavior was exercised.
- [ ] Bad-input/missing-env behavior is graceful.
- [ ] Logs show no plugin load errors.
- [ ] Post-creation validation reports each goal mapping with evidence or a blocker.
- [ ] Source/install trees match after generated caches are removed.
- [ ] Native task/dependency semantics and worker tool scope were verified when Kanban is involved.
- [ ] External enforcement boundaries, fresh-session/restart needs, and any paused source-export automation are reported.
- [ ] Final response reports actual validation evidence.
