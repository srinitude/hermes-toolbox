---
name: profile-builder
description: Use when the user wants to design, validate, and create a customized Hermes profile through a collaborative back-and-forth process. Routes each user reply through prompt-enhancer discipline, captures goals/outcomes, maps them across Hermes profile primitives, confirms the final profile spec, then creates the profile only after explicit user agreement.
version: 0.1.0
author: Kiren Srinivasan
license: Apache-2.0
metadata:
  hermes:
    tags: [hermes-agent, profiles, configuration, prompt-enhancer, setup, validation]
    related_skills: [hermes-agent, prompt-enhancer, plugin-builder, openrouter-mcp-server]
---

# Profile Builder

## Overview

Use this skill to collaboratively design and create a fully customized Hermes Agent profile. The process is a tight consultation loop: clarify only what matters, convert low-risk unknowns into explicit assumptions, capture the user's goals and desired outcomes for the profile, validate continuously against the gold-standard profile criteria, and move to profile creation as soon as the spec is complete and the user approves.

The builder must treat goals as first-class design inputs. When the user describes what they want to accomplish, why they need a dedicated profile, or what outcomes the profile should produce, preserve those goals in the running spec and map each one across the Hermes profile primitive set: profile identity and purpose, SOUL/identity, model, configuration, terminal/backend, capabilities/tools/skills/MCP/plugins, memory, automation, security, performance, validation, and portability. The result should be a profile designed to achieve the user's stated goals through the new profile itself, not by relying on behavior or state that only exists in the default profile. If a primitive is not relevant to a goal, mark it not applicable, skipped, or blocked with a reason; do not silently omit any primitive category from goal coverage.

When profile goals imply custom capabilities, the builder should also review existing plugins that were generated through `/plugin-builder`. Treat those plugins as candidate profile primitives, not automatic inclusions: inspect their manifests and lightweight docs read-only, evaluate whether any are a good fit for the prospective profile's goals, then ask the user whether to include one or more recommended plugins. Never include, copy, install, enable, or trust a plugin in the new profile unless the user approves it in the final profile spec.

This skill also acts as a **configuration builder** for profile `config.yaml`: it helps the user set every relevant Hermes configuration value through presets, guided category questions, or a full typed config matrix. The builder must never dump hundreds of raw keys at the user by default. Instead, it should translate intent into a `configuration_manifest` where every proposed key has a value, value type, source, setter method, safety note, and validation command.

This skill is for **normal profile customization**, not Hermes core development. Use profile-safe surfaces such as `hermes profile`, `hermes config`, `hermes tools`, `hermes model`, profile `SOUL.md`, profile-local skills, profile cron jobs, MCP config, and official setup/auth flows. Do not edit Hermes source checkout files for ordinary customization.

## When to Use

Use this skill when the user asks to:

- create a new Hermes profile
- rename, migrate, or propagate the name/path of an existing Hermes profile
- design a specialized Hermes assistant, worker, bot, researcher, coder, reviewer, or automation profile
- configure a profile for correctness, speed, tool access, safety, gateway use, cron, MCP, skills, memory, or portability
- turn a rough profile idea into a validated profile spec and then create it
- compare possible profile configurations and pick the fastest safe path

Do not use this skill for:

- editing Hermes Agent core code or upstream bundled skills
- one-off factual questions about profiles where no profile will be designed
- direct secret entry, raw credential-file inspection, or unsafe credential handling
- creating a profile before the user has agreed to the final spec

## Required Supporting Skill

Before starting the profile-builder loop, load `prompt-enhancer` with `skill_view(name="prompt-enhancer")` unless it is already loaded in the current conversation.

Every user reply during the profile-builder process must be processed through the prompt-enhancer discipline before updating the profile spec:

1. Extract user outcome, context, action type, write scope, validation, profile goals, desired outcomes, success measures, non-goals, and any reason the outcome belongs in a dedicated profile instead of the default profile.
2. Convert low-risk ambiguity into labeled assumptions.
3. Ask only when ambiguity changes the profile target, goal interpretation, write safety, cost, credentials, gateway delivery, or validation threshold.
4. Apply Hermes write-safety boundaries.
5. Update the profile spec, `goals` section, goal-to-primitives coverage matrix, and validation ledger.
6. Continue toward the shortest path that satisfies the gold-standard criteria and accounts for every stated goal as `mapped`, `skipped`, or `blocked`.

When a user reply includes a goal or desired outcome, do not leave it as conversational context only. Convert it into a compact `goals.stated[]` or `goals.desired_outcomes[]` entry, then map it across the full profile primitive set. If a primitive does not apply to the goal, mark that primitive as `not_applicable` or `skipped` with the reason. If the goal requires user-controlled credentials, external services, missing tools, or unsafe writes, mark it as `blocked` with the exact blocker and user action needed.

Do not literally require the user to type `/prompt-enhancer` on every turn. The agent running this skill is responsible for applying the prompt-enhancer procedure internally to every user reply.

<!-- coding-contract-propagation:start -->
## Coding Contract Propagation

Whenever a proposed profile can create, modify, refactor, review, or validate code, inherit the exact Universal Coding Contract for Code Work from `prompt-enhancer`. Treat it as a required profile primitive, not optional style guidance, and carry it through intake, goal mapping, the working spec, the final approval preview, creation, and post-creation validation.

```yaml
coding_contract:
  applies_when: profile_can_create_modify_refactor_review_or_validate_code
  max_file_physical_lines: 200
  max_construct_physical_lines: 30
  max_nesting_depth: 3
  test_nesting_baseline: test_declaration
  tdd_sequence: [BOOTSTRAP, RED, GREEN, REFACTOR]
  real_tests_only: true
  prohibited_test_doubles: [mocks, stubs, fakes, spies, placeholders]
  test_targets: [user-facing situations, public contracts, APIs, integration boundaries, interfaces]
  status: mapped
```

For code-capable profiles, the final approval preview must show this `coding_contract`, the real-service test path, the command that will witness RED before production code, and the language-aware validation commands for file length, construct length, and nesting. A non-coding profile may set `status: not_applicable` only with an explicit reason.

During creation, execute each behavior as a vertical `BOOTSTRAP → RED → GREEN → REFACTOR` slice. Do not create or approve source/tests that use TODOs, mocks, stubs, fakes, spies, placeholders, synthetic success responses, skipped/xfail placeholders, implementation-detail assertions, or tests written for testing’s sake. Missing credentials, paid-call approval, or a real service are blockers, not permission to simulate.

Before declaring profile creation complete, validate that the copied profile-local `prompt-enhancer/SKILL.md` contains exactly one `universal-coding-contract` marker pair and all hard rules. The gold-standard ledger and final verification checklist must record the contract as `mapped`, `not_applicable`, or `blocked`; silent omission fails validation.
<!-- coding-contract-propagation:end -->

## Repository, Authorship, and Public-Documentation Defaults

Every profile/config distribution created through this skill should carry the repository owner's durable authorship preferences unless the user explicitly overrides them in the final approval spec:

- Git author identity: `<repo-author-name> <<private-term>>`.
- Commit message policy: never add `Co-authored-by`, AI co-authoring trailers, or AI-attribution lines.
- New repository-author-authored skills: `version: 0.1.0`, `author: <repo-author-name>`, and `license: Apache-2.0`.
- Public config repositories and READMEs should document the generic customization system and future-update process without naming sensitive or exact profile contexts unless the user explicitly approves those names for publication.

When a profile/config repo is part of the request, include these as explicit config/repo-governance items in the plan or final spec: `.gitconfig`/local git config setup, README maintenance rules, skill frontmatter conventions, and validation commands that prove no AI co-author trailers or disallowed profile names were introduced. See `references/repository-governance.md` for the reusable checklist and validation snippets.

Completion criterion: every generated plan/final spec for a profile/config repository either includes these defaults or states the user-approved override.

## Profile-Builder Bootstrap Skills

Every profile created through this skill must be able to use the builder workflow that produced it. Treat these as mandatory **profile-builder bootstrap skills** and include them in the new profile unless the user explicitly opts out and accepts that the new profile may not be able to run those workflows:

| Skill | Source relative to the validated canonical bootstrap home's `skills/` | Target relative to new profile `skills/` | Why it is required |
| --- | --- | --- | --- |
| `profile-builder` | `hermes-agent/profile-builder` | `hermes-agent/profile-builder` | Makes the workflow that created the profile available inside the new profile; omitting it makes the stated self-bootstrap guarantee false. |
| `prompt-enhancer` | `software-development/prompt-enhancer` | `software-development/prompt-enhancer` | Normalizes profile/plugin prompts, write safety, and validation thresholds. |
| `plugin-builder` | `software-development/plugin-builder` | `software-development/plugin-builder` | Lets the new profile design and create approved Hermes plugins. |
| `openrouter-mcp-server` | `autonomous-ai-agents/openrouter-mcp-server` | `autonomous-ai-agents/openrouter-mcp-server` | Lets the new profile perform OpenRouter MCP-backed subagent model routing when configured. |

Do not blindly use the active named profile as the bootstrap source: profile-local builder copies can lag or carry profile-specific references. Resolve a canonical bootstrap home first (normally the default Hermes home), compare any active-profile copy against it, and merge intentional profile-specific support files instead of replacing them.

These skills are **not** `/plugin-builder` generated plugins. They do not count as approved generated plugins, do not bypass the generated-plugin approval gate, and do not authorize copying any plugin code, plugin secrets, MCP credentials, or runtime state.

### Bootstrap skill copy rules

1. Resolve the active profile home from `$HERMES_HOME` when set, otherwise `~/.hermes`.
2. Resolve and validate the canonical bootstrap home. In a standard multi-profile install this is `~/.hermes`, not `~/.hermes/profiles/<active-name>`. If a nonstandard home is intentional, record the chosen source and compare its builder trees before copying.
3. Resolve the new profile home from the profile creation result, `hermes profile show <profile-name>`, or the approved target path `~/.hermes/profiles/<profile-name>`.
4. For each required bootstrap skill, verify the source directory contains `SKILL.md` and the frontmatter `name` matches the expected skill name.
5. Copy only `SKILL.md` and allowed support directories: `references/`, `templates/`, `scripts/`, and `assets/`.
6. Do not copy `.env`, auth stores, token files, logs, cache, state databases, sessions, backups, checkpoints, plugin directories, or arbitrary hidden/runtime files.
7. If a required source skill is missing, stop and mark the profile creation as blocked until the user installs/restores the missing skill or explicitly approves proceeding without it.
8. If the profile was created with `--clone`, `--clone-all`, or `--clone-from`, still validate all four skills in the target profile and repair any missing/stale copies from the validated canonical source.
9. When a target builder tree has profile-specific references, merge the canonical core files and preserve intentional extras; do not blindly replace the whole directory.
10. Show the bootstrap skill copy in the final profile spec under both `Skills` and `Writes that will occur` before asking for approval.

A safe copy helper may be used after the profile exists. Replace `<profile-name>` and `<profile-home>` with the approved values:

```bash
TARGET_PROFILE_HOME="<profile-home>" python3 - <<'PY'
from pathlib import Path
import os, re, shutil

active_home = Path(os.environ.get('HERMES_HOME') or Path.home() / '.hermes').expanduser()
default_home = (Path.home() / '.hermes').expanduser()
source_home = default_home if (default_home / 'skills').is_dir() else active_home
target_home = Path(os.environ['TARGET_PROFILE_HOME']).expanduser()

required = {
    'profile-builder': Path('hermes-agent/profile-builder'),
    'prompt-enhancer': Path('software-development/prompt-enhancer'),
    'plugin-builder': Path('software-development/plugin-builder'),
    'openrouter-mcp-server': Path('autonomous-ai-agents/openrouter-mcp-server'),
}
allowed_dirs = {'references', 'templates', 'scripts', 'assets'}


def frontmatter_name(skill_md: Path) -> str | None:
    text = skill_md.read_text(encoding='utf-8')
    match = re.search(r'^---\s*\n(.*?)\n---\s*\n', text, re.S)
    if not match:
        return None
    for line in match.group(1).splitlines():
        if line.startswith('name:'):
            return line.split(':', 1)[1].strip().strip('"').strip("'")
    return None


def copy_allowed_skill_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / 'SKILL.md', dst / 'SKILL.md')
    for dirname in allowed_dirs:
        child = src / dirname
        if child.exists():
            if not child.is_dir():
                raise SystemExit(f'blocked: {child} exists but is not a directory')
            shutil.copytree(child, dst / dirname, dirs_exist_ok=True)

for expected_name, rel in required.items():
    src = source_home / 'skills' / rel
    dst = target_home / 'skills' / rel
    skill_md = src / 'SKILL.md'
    if not skill_md.exists():
        raise SystemExit(f'blocked: missing source skill {expected_name}: {skill_md}')
    actual_name = frontmatter_name(skill_md)
    if actual_name != expected_name:
        raise SystemExit(f'blocked: {skill_md} declares name={actual_name!r}, expected {expected_name!r}')
    if dst.exists() and not dst.is_dir():
        raise SystemExit(f'blocked: target path exists but is not a directory: {dst}')
    copy_allowed_skill_tree(src, dst)
    copied_name = frontmatter_name(dst / 'SKILL.md')
    if copied_name != expected_name:
        raise SystemExit(f'blocked: copied skill validation failed for {expected_name}')
    print(f'copied {expected_name}: {src} -> {dst}')
PY
```

Completion criterion: all four required bootstrap skills are copied or validated in the new profile-local `skills/` tree from the validated canonical source, and any blocker or intentional profile-specific merge is reported before declaring profile creation complete.

## Profile-Builder Bootstrap Kanban Workflow Control-Plane Plugin

Every normal profile created through this skill that should interact with Hermes Projects, Kanban boards/tasks, worker lanes, or Kanban workflow primitives should receive the reusable `kanban-workflow-control-plane` plugin by default, unless the user explicitly opts out or the target profile is excluded. Generated profiles and existing consumer profiles must assume many Projects and many boards. `/kanban-workflow` is the normal user-facing path for seeing scope, choosing a Project or board, starting work, routing tasks through the required lifecycle, and recording the strict design-gate exception only when no design-sensitive surface is in the blast radius.

Treat `kanban-workflow-control-plane` as a reusable **bootstrap workflow plugin**, distinct from generated plugin recommendations, optional user-selected plugins, and skills.

### Default source and target

- Source plugin: `~/.hermes/profiles/non-<first-name>-plugins/plugins/kanban-workflow-control-plane/`
- Named profile target: `~/.hermes/profiles/<profile-name>/plugins/kanban-workflow-control-plane/`
- Default profile target: `~/.hermes/plugins/kanban-workflow-control-plane/`

### Exclusions

Do not install or enable this plugin by default in:

- `<first-name>-plugins`
- `non-<first-name>-plugins`
- any profile matching `kanban-workflow-*`

The `non-<first-name>-plugins` path above is the source package, not a consumer installation.

### Human UX and workflow policy

Generated profiles should describe `/kanban-workflow` as the normal Projects/Kanban path. The plugin binds to the host-provided active profile and rejects caller-supplied cross-profile targeting. Users select Projects by name or slug, boards by name or slug, and tasks by title or visible label. Internal IDs, work keys, run handles, context bundles, and raw JSON are implementation details unless a developer explicitly asks for diagnostics. Ambiguous labels require a short visible choice list before any mutation.

Every task created or phase-routed through the control plane enters through `kanban-workflow-orchestrator` and follows:

`kanban-workflow-brainstorm` → `kanban-workflow-design` → `kanban-workflow-plan` → `kanban-workflow-test` → `kanban-workflow-build` → `kanban-workflow-document` → `kanban-workflow-review` → `kanban-workflow-deploy` → `kanban-workflow-maintain`.

The design phase is required unless the orchestrator records 100% certainty and evidence that no direct or indirect UI, UX, copy, accessibility, responsive, media, visual, interaction, design-system, prototype, or handoff surface is touched, and a human confirms that exact route. Missing evidence or uncertain downstream consumers require `kanban-workflow-design`.

A profile-local plugin can govern its own routes and observable agent tool calls. It cannot intercept a person running `hermes kanban` from an external shell, so `/kanban`, the dashboard, and external CLI use remain advanced operator surfaces; report violations as observable drift rather than claiming universal enforcement. Model-callable route/action tools are permanently dry-run-only. Human slash-command mutations require a two-step preview and a short-lived, single-use confirmation token bound to the active profile, canonical board, resolved task, operation, and arguments.

### Copy policy

Copy plugin source files only. Exclude `__pycache__/`, `.pytest_cache/`, `*.pyc`, `*.pyo`, `.env`, auth/token stores, logs, sessions, caches, `state.db*`, `kanban.db*`, pairing state, backups, checkpoints, and other runtime/private data.

If the target plugin directory already exists and differs from the source, create a timestamped backup before refreshing it.

### Enable command

Enable without built-in tool override:

```bash
hermes -p <profile-name> plugins enable kanban-workflow-control-plane --no-allow-tool-override
```

For the default profile:

```bash
hermes -p default plugins enable kanban-workflow-control-plane --no-allow-tool-override
```

Do not grant tool override unless the user explicitly approves that exception in the final profile spec.

### Validation

After copy and enablement, validate:

1. `plugin.yaml`, `__init__.py`, and the bundled `SKILL.md` exist under the profile-local plugin tree.
2. `hermes -p <profile-name> plugins list --json` shows the plugin enabled.
3. A fresh-process registration probe sees `kanban_workflow_status`, `kanban_workflow_route`, `kanban_workflow_action`, `/kanban-workflow`, `pre_tool_call`, and the bundled skill.
4. `/kanban-workflow` help/status mention many-Project/many-board scope and do not require internal handles or raw JSON.
5. No caches, secrets, runtime state, logs, sessions, `state.db*`, `kanban.db*`, auth stores, or pairing data were copied.
6. `plugins.entries.kanban-workflow-control-plane.allow_tool_override` is absent or false.
7. The profile starts a fresh session—or an explicitly approved long-running gateway restart occurs—before claiming the newly enabled plugin is live in that process.

Show this bootstrap workflow plugin separately from generated plugin recommendations in the final profile approval spec. Its default use is approved for eligible normal profiles, but it must still respect exclusions and safe copy/enable rules.

## Profile-Builder Bootstrap Personality Overlay

By default, every profile created through this skill should also receive the active profile's custom `/personality validator` overlay when it exists, unless the user explicitly opts out. This is a **configuration overlay**, not a `SOUL.md` clone:

- `SOUL.md` must still be freshly customized for the new profile's purpose.
- The `validator` personality overlay is copied as reusable validation posture: adversarial review, documentation-grounded answers, minimum sufficient work, and objective validation thresholds.
- Copying `/personality validator` does not authorize copying any other personality, raw secrets, session state, memories, logs, caches, plugins, or runtime files.

### Validator personality copy rules

1. Resolve the active profile home from `$HERMES_HOME` when set, otherwise `~/.hermes`.
2. Read only non-secret config fields from the active profile `config.yaml`: `agent.personalities.validator` and `agent.system_prompt`.
3. If `agent.personalities.validator` is present, include it in the new profile's config manifest as `agent.personalities.validator`.
4. If the active `agent.system_prompt` exactly matches the resolved validator personality prompt, or the user explicitly asked to copy `/personality validator`, include `agent.system_prompt` set to that validator prompt in the new profile's config manifest unless an explicit approved `agent.system_prompt` entry already exists; in that case preserve the explicit prompt and copy only the validator definition.
5. If the validator personality is missing in the source profile, mark the validator overlay as `blocked` and ask whether to proceed without it or provide/create one. Do not invent a validator prompt.
6. If the profile was created with `--clone`, `--clone-all`, or `--clone-from`, still validate that the target profile has `agent.personalities.validator` and that `agent.system_prompt` is either the resolved validator prompt or the explicit approved `agent.system_prompt` default; repair missing/stale values from the active source config only within the approved manifest.
7. Show the validator overlay copy separately from `SOUL.md`, bootstrap skills, optional skills, and generated plugins in the final approval spec and in `Writes that will occur`.

Completion criterion: the target profile's config contains the approved `agent.personalities.validator` definition and the approved `agent.system_prompt` overlay, or the final report lists an explicit blocker. The target profile's `SOUL.md` remains profile-specific and is not copied wholesale from the source profile.

## Kanban Workflow Profile Orchestration

When a profile-building request involves phase-gated work, named worker profiles, durable multi-agent coordination, context handoffs, human review gates, or Hermes Kanban, load `references/kanban-workflow-profile-orchestration.md` before drafting the final profile spec. Treat each phase as a first-class profile primitive: identity, model, config, toolsets, memory, automation, security, performance, validation, and portability must all be mapped or explicitly skipped/blocked. Prefer official profile distributions and `hermes profile install` over manual profile directory copying.

When the profile represents a business, creator operation, product portfolio, or brand that may spawn multiple distinct operating units, also load `references/portfolio-channel-kanban-separation.md`. Use a portfolio/business Project + board for entity-wide management, ideation, validation, and rollups, and separate unit/channel/product Projects + boards for decided operating units. Validate the split against official Hermes Kanban board isolation semantics, live `hermes project`/`hermes kanban` CLI output, and any relevant external product/portfolio operating best practices before presenting the final spec.

## Operating Mode

Run in two phases:

1. **Collaboration mode** — gather requirements, propose assumptions/defaults, validate spec completeness, and refine with the user.
2. **Creation mode** — only after explicit final user agreement, create/configure the profile and run objective validation commands.

If the user disagrees with the final spec, stay in collaboration mode, update the spec, and repeat the final confirmation step.

## Profile Spec Schema

Maintain a running profile spec in the conversation. Keep it concise but complete:

```yaml
profile:
  name: ""
  description: ""
  creation_method: blank | clone | clone_all | clone_from | distribution_install
  clone_source: null
  no_bundled_skills: false
  intended_surfaces: [cli]        # cli, tui, desktop, gateway, cron, acp, dashboard
  primary_use_cases: []
  dedicated_profile_rationale: "" # why this should be a new profile instead of relying on default

goals:
  stated: []                      # user's own words, preserved as compact goal statements
  desired_outcomes: []            # observable outcomes the profile should help achieve
  non_goals: []                   # explicitly out-of-scope outcomes
  success_measures: []            # how the user will know the profile is working
  assumptions: []                 # inferred goals/defaults not explicitly stated
  goal_to_primitives:
    - goal: ""
      desired_outcome: ""
      primitive_coverage:
        profile: []               # name, description, creation method, surfaces, use cases
        identity: []              # SOUL/personality/tone/avoid rules
        model: []                 # provider/model/reasoning/fallbacks
        configuration: []         # config manifest keys or default decisions
        terminal: []              # backend/cwd/home/sandbox choices
        capabilities: []          # toolsets, skills, MCP servers, approved plugins, and reviewed plugin candidates
        memory: []                # durable memory/user profile/external provider choices
        automation: []            # gateway, cron, webhooks
        security: []              # approvals, sandboxing, credential policy, redaction
        performance: []           # speed/cost/quality/compression choices
        validation: []            # commands/smoke tests proving the goal is represented
        portability: []           # export/distribution/env requirements
      not_applicable: []          # primitive names that were considered and intentionally skipped
      unmapped_primitives: []     # must be empty before final approval unless blocked
      status: pending | mapped | skipped | blocked
      notes: ""

identity:
  soul_summary: ""
  tone: ""
  communication_defaults: []
  avoid: []
  personality_overlay:
    name: validator
    default_copy: true
    source: active_profile_config
    config_keys:
      - agent.personalities.validator
      - agent.system_prompt
    status: pending | copied | already_present | skipped | blocked
    notes: "SOUL.md remains unique to the new profile; this is a reusable /personality overlay only."

model:
  provider: ""
  model: ""
  auth_method: oauth | api_key | existing | custom_endpoint | unknown
  fallback_providers: []
  reasoning_effort: "medium"

configuration:
  mode: preset                  # preset | guided | full_matrix | import_existing
  source_profile: null          # existing profile name when importing/cloning settings
  presets: []                   # e.g. coder, reviewer, researcher, bot, minimal, power-user
  values:
    set: []                     # list of approved config entries to apply
    leave_default: []           # keys intentionally left at DEFAULT_CONFIG/current value
    skip: []                    # keys intentionally skipped with reason
    blocked: []                 # keys blocked by missing auth, unsafe writes, or user decision
  manifest_entry_shape:
    key: "section.path"
    value: null
    value_type: string | boolean | integer | float | list | map | null | duration | secret_ref
    source: user | default | preset | cloned_profile | inferred | docs | current_config
    setter: hermes_config | hermes_model | hermes_auth | hermes_tools | hermes_mcp | hermes_gateway | hermes_cron | skill_write | manual_user_action
    requires_secret: false
    secret_handling: "none | env_or_auth_flow | user_action_required"
    restart_required: false
    validation: "command or observation that proves this setting is active"
    notes: ""

terminal:
  backend: local                  # local, docker, ssh, modal, daytona, singularity
  cwd: ""
  home_mode: auto                 # auto, real, profile
  sandbox_required: false

capabilities:
  toolsets_enabled: []
  toolsets_disabled: []
  skills: []                   # user-selected profile skills beyond mandatory builder bootstrap skills
  profile_builder_bootstrap_skills:
    required:
      - name: profile-builder
        source_relative_path: hermes-agent/profile-builder
        target_relative_path: hermes-agent/profile-builder
        status: pending | copied | already_present | merged | blocked
      - name: prompt-enhancer
        source_relative_path: software-development/prompt-enhancer
        target_relative_path: software-development/prompt-enhancer
        status: pending | copied | already_present | blocked
      - name: plugin-builder
        source_relative_path: software-development/plugin-builder
        target_relative_path: software-development/plugin-builder
        status: pending | copied | already_present | blocked
      - name: openrouter-mcp-server
        source_relative_path: autonomous-ai-agents/openrouter-mcp-server
        target_relative_path: autonomous-ai-agents/openrouter-mcp-server
        status: pending | copied | already_present | blocked
    source_home: validated_canonical_bootstrap_home
    active_profile_comparison: required_for_builder_tree_drift
    target_home: "~/.hermes/profiles/<profile-name>"
    copy_policy: copy SKILL.md plus references/templates/scripts/assets only; merge intentional profile-specific support files
  profile_builder_bootstrap_plugins:
    required:
      - name: kanban-workflow-control-plane
        source_preference:
          - ~/.hermes/profiles/non-<first-name>-plugins/plugins/kanban-workflow-control-plane
        target_relative_path: plugins/kanban-workflow-control-plane
        enable_command: hermes -p <profile-name> plugins enable kanban-workflow-control-plane --no-allow-tool-override
        exclusions: [<first-name>-plugins, non-<first-name>-plugins, kanban-workflow-*]
        status: pending | copied | already_present | enabled | skipped_excluded | blocked
        ux_contract: one default path, many Projects, many boards, human labels, hidden internal handles, orchestrator-led ordered phase gates
    copy_policy: source files only; exclude secrets, caches, sessions, logs, runtime databases, pairing state, backups, and checkpoints
    tool_override_allowed: false
  mcp_servers: []

  plugins: []                  # additional approved plugins to include in the profile
  plugin_candidates:
    scan_required: true         # true once profile goals/capability needs are known
    scan_paths: []              # plugin roots inspected read-only
    generated_by_plugin_builder: []
    recommended_for_profile: []
    rejected_or_not_relevant: []
    user_decisions:
      - plugin_name: ""
        decision: pending | include | skip | blocked
        include_method: install | copy_profile_local | enable_existing | manual_user_action | not_applicable
        source_path: ""
        target_path: ""
        reason: ""

memory:
  built_in_memory: true
  user_profile: true
  external_provider: null
  write_approval: false

automation:
  gateway_platforms: []
  cron_jobs: []
  webhooks: []

security:
  approvals_mode: off             # manual, smart, off; user-requested default bypasses approval prompts
  yolo_default: false
  pii_redaction: false
  secret_handling_notes: []
  allowed_write_surfaces: []
  prohibited_write_surfaces: []

performance:
  prompt_size_target: "small enough for chosen model and workload"
  auxiliary_models: {}
  compression_enabled: true
  speed_priorities: []

validation:
  required_commands: []
  success_criteria: []
  blockers: []

portability:
  export_needed: false
  distribution_needed: false
  env_requires: []
```

### Plugin Candidate Entry Shape

When reviewing `/plugin-builder` generated plugins, keep each candidate compact:

```yaml
plugin_candidate:
  plugin_name: ""
  source_path: ""
  manifest_path: ""
  provenance: plugin_builder | unknown | other
  provenance_evidence: "manifest metadata | README text | user statement | unknown"
  manifest_kind: standalone | backend | exclusive | platform | model-provider | unknown
  description: ""
  provides:
    tools: []
    hooks: []
    slash_commands: []
    cli_commands: []
    skills: []
    providers: []
  requires_env: []
  config_keys: []
  external_side_effects: []
  safety_notes: []
  performance_notes: []
  profile_fit:
    score: 0                    # 0-5; recommend only 4-5 by default
    matched_goals: []
    matched_profile_primitives: []
    reasons_to_include: []
    reasons_to_skip: []
    blockers: []
  recommendation: include | consider | skip | blocked
```

## External Repository Context Protocol

When the user says an external repository should guide a new profile's conversations, identity, workspace, or future plugins, treat the repo as a first-class profile primitive instead of vague background context. If the user asks to read all content, verify the exact revision and read every tracked file before finalizing the spec. Use `references/external-repo-context-profile-customization.md` for the byte-for-byte manifest pattern, repo-to-primitive mapping, approved write shape (`workspace clone` + concise `.hermes.md` + profile-local class skill/reference), and pitfalls such as internal corpus mismatches.

Completion criterion: the final approval preview records the repo URL/revision, file-count/read validation, known corpus caveats, intended workspace location, and how the repo context is represented without dumping raw content into `SOUL.md`.

## Humanized Writing / Detector-Loop Profiles

When a profile is for humanized writing, release-readiness checks, AI-detection/plagiarism loops, or self-updating writing rules, load `references/humanized-writing-profile-pattern.md` before drafting the final spec. Treat the starting rules, labeled writing corpus, detector APIs, future plugin-builder workflow, and rule-learning surface as separate primitives. If the user's `starting-rules` are truncated or summarized by the UI, block exact merging and ask whether to proceed with reconstructed rules or wait for the full source text.

## Generated Plugin Discovery Protocol

Use this protocol after the profile's goals, desired outcomes, and capability needs are known, and before presenting the final profile spec.

1. **Run read-only inventory.** Inspect available plugin metadata without importing plugin Python modules or executing plugin code.
2. **Use safe roots only.** Consider:
   - current `$HERMES_HOME/plugins/**`,
   - `~/.hermes/plugins/**` for the active profile home,
   - `~/.hermes/profiles/<source-profile>/plugins/**` only when the source profile is explicitly in scope,
   - trusted project-local `.hermes/plugins/**` only when the user explicitly identifies that project/workspace as trusted.
3. **Prefer manifests.** Read `plugin.yaml`, `plugin.yml`, `README.md`, and small docs files. Do not read raw credential files, runtime databases, logs, or caches.
4. **Use provenance carefully.** Mark a plugin as `/plugin-builder` generated only when manifest/docs/user context provide evidence such as `generated_by: plugin-builder`, `created_by: plugin-builder`, `metadata.hermes.generated_by: plugin-builder`, or an explicit user statement. Otherwise use `provenance: unknown`.
5. **Score fit against the profile spec.** Compare plugin capabilities, required env/config, side effects, performance, validation burden, and portability against `goals.goal_to_primitives[]` and `capabilities` needs.
6. **Recommend sparingly.** Recommend only plugins that clearly advance the profile's stated goals with acceptable safety/performance/cost tradeoffs. Put weak matches under `rejected_or_not_relevant[]` or `consider`.
7. **Ask before inclusion.** Present recommended plugins with reasons and ask whether to include any. Do not include plugins silently.

Useful read-only checks during a profile-building session:

```bash
hermes plugins list
hermes -p <source-profile> plugins list
```

Useful file-tool pattern:

```python
# Use Hermes file/search tools, not shell mutation.
# Find manifests under approved plugin roots, then read only plugin.yaml/plugin.yml/README.md.
search_files("plugin.y*ml", target="files", path="<private-term>/.hermes/plugins")
read_file("<private-term>/.hermes/plugins/<plugin>/plugin.yaml")
```

Completion criterion: every generated plugin candidate is recorded as `include`, `consider`, `skip`, or `blocked`, with provenance evidence and a fit reason.

## Plugin Fit Scoring Rules

Score each `/plugin-builder` generated plugin from 0-5 for the prospective profile:

| Score | Meaning | Default action |
| --- | --- | --- |
| 5 | Directly satisfies one or more stated goals with low risk and clear validation | Recommend include |
| 4 | Strongly supports stated goals but has minor setup, env, or validation requirements | Recommend include or consider |
| 3 | Plausibly useful but not necessary for the core profile goals | Mention as optional |
| 2 | Weak fit, duplicates built-in tools/MCP/skills, or adds avoidable complexity | Skip by default |
| 1 | Misaligned with goals or likely to degrade safety/performance | Skip |
| 0 | Unsafe, broken, uninspectable, or requires prohibited writes/secrets | Block |

A plugin is a good fit only when:

- it maps to at least one stated profile goal or desired outcome,
- the same goal is not better served by a simpler built-in toolset, skill, MCP server, or config setting,
- required env/config/secrets are explicit and safe to ask the user to set through official flows,
- safety/write side effects are compatible with the profile's security posture,
- import/runtime performance is acceptable for the profile,
- validation can prove the plugin loads and exposes the expected capability in the new profile.

When recommending a plugin, say why it fits and which profile primitive it would satisfy, for example:

```text
I found `calendar-briefing` in your plugin-builder-generated plugins. I think it is a good fit for this research-assistant profile because it supports your “daily planning brief” goal, provides one model-callable tool and one `/calendar-brief` command, and its only blocker is `GOOGLE_CALENDAR_TOKEN` setup. Would you like this plugin included in the new profile?
```

Completion criterion: recommendations are evidence-backed and user-approved, not automatic.

### Configuration Manifest Rules

- Every non-default config change must become one `configuration.values.set[]` manifest entry.
- Every high-impact default that the user explicitly accepts should be listed in `configuration.values.leave_default[]` with a short reason.
- Secret-bearing values must use `secret_ref` or `manual_user_action`; never place raw API keys, OAuth tokens, passwords, or bearer tokens in the manifest.
- For every new profile, include `agent.system_prompt` as a non-secret manifest entry set exactly to: `You are a Hermes Agent expert focused on ideating, executing, and validating the correct answer. Don't write/edit any files within directories that users of Hermes Agent aren't allowed to touch. Use adversarial review to define an objective validation threshold that proves correctness beyond doubt. Pinpoint the essence of the user's request, convert all unknowns into knowns, and enumerate every problem to solve. Start open-minded across all available tools, then narrow to those you're medium-to-high confident are relevant. Don't continue working down a line of thought or action if you know that it is objectively and provably wrong. Validate your work against official documentation, codebases and first-party sources. Do the minimum work and use the fewest tokens needed to hit the validation threshold. Stop immediately once it's met. Only do what's necessary.` Apply it with `hermes -p <profile> config set agent.system_prompt <prompt>` and validate the target profile config directly.
- For every new profile, include `approvals.mode` as a non-secret manifest entry set to `off` unless the user explicitly requests `manual` or `smart`. Apply it with `hermes -p <profile> config set approvals.mode off`; Hermes writes this as YAML `false`, and the first-party approval runtime normalizes that value back to approval mode `off`. Validate the target profile config via runtime normalization, not by requiring a quoted string.
- For every new profile, include these non-secret paste-composer settings as default manifest entries unless the user explicitly opts into paste-token collapse/truncation: `paste_collapse_threshold=0`, `paste_collapse_threshold_fallback=0`, and `paste_collapse_char_threshold=0`. Apply them with `hermes -p <profile> config set <key> 0` and validate the target profile config directly.
- Prefer `hermes -p <profile> config set <key> <value>` for non-secret values.
- Prefer official setup/auth/model/tool/MCP/gateway/cron flows when a setting is better managed by a purpose-built command.
- If a key is dynamic or plugin-defined, record the source that proved the key exists (`skill`, plugin docs, `hermes tools`, MCP server docs, or current profile config).

### Goal-to-Primitive Mapping Rules

See `references/goal-primitive-mapping.md` for a compact example matrix and validation notes. For sensitive life-domain profiles, also see `references/sensitive-profile-design.md` for gateway-vs-transport separation, strict Honcho isolation, profile-home-vs-cwd handling, plugin-powered cron blockers, draft-to-send workflows, and validator-overlay handling. For existing-profile renames/migrations, use `references/profile-rename-migration.md` for preflight checks, official rename sequencing, cross-profile write-guard handling, Honcho validation nuance, and smoke tests.

Treat goal mapping as a compact coverage matrix, not as a prose summary. For every stated goal or desired outcome:

1. Evaluate every profile primitive category: `profile`, `identity`, `model`, `configuration`, `terminal`, `capabilities`, `memory`, `automation`, `security`, `performance`, `validation`, and `portability`.
2. Add the concrete profile choice, config key, toolset, skill, automation, validation command, or policy that represents the goal in that primitive.
3. If a primitive does not apply, add it to `not_applicable[]` with a short reason in `notes`; do not leave it silently empty.
4. If a primitive is blocked by missing auth, credentials, external setup, unsafe writes, or user decision, record it in the relevant `blocked` list and in `validation.blockers`.
5. Do not present the final approval spec while any `unmapped_primitives[]` remain unless they are explicitly blocked and surfaced to the user.

A goal is fully covered only when the new profile can carry the needed behavior through its own approved primitives or through an approved clone/import path from another profile. Do not assume the default profile will supply the behavior unless the final spec explicitly chooses clone/import and names what is inherited.

## Gold-Standard Validation Ledger

After every user reply, update a checklist mentally or visibly. Do not create the profile until every required item is satisfied, intentionally skipped, or blocked with a clear reason.

Required criteria:

- [ ] Purpose: profile has a clear role and description.
- [ ] Goals: user's stated goals, desired outcomes, success measures, and non-goals are captured or intentionally defaulted.
- [ ] Dedicated profile rationale: the spec explains why these outcomes should be achieved by the new profile rather than relying on the default profile.
- [ ] Goal mapping: every stated goal maps across the full Hermes profile primitive set or each non-applicable/blocked primitive is explicitly marked with a reason.
- [ ] Goal validation: every mapped goal has at least one validation command, smoke test, or observable success criterion.
- [ ] Coding contract: every code-capable goal maps the `coding_contract` limits, real-test path, witnessed RED command, and BOOTSTRAP/RED/GREEN/REFACTOR validation, or is explicitly not applicable/blocked.
- [ ] Isolation: profile state will live under its own `HERMES_HOME`.
- [ ] No core edits: customization uses profile/config/skills/SOUL/context surfaces only.
- [ ] Model: provider, model, and auth path are defined or a setup blocker is explicit.
- [ ] Tools: only intended toolsets/MCP tools are enabled.
- [ ] Skills: relevant reusable workflows are selected or intentionally omitted.
- [ ] Generated plugins: `/plugin-builder` generated plugins were inventoried read-only after goals were known, or the scan was intentionally skipped with a reason.
- [ ] Plugin fit: each generated plugin candidate is marked `include`, `consider`, `skip`, or `blocked` with provenance evidence and a fit reason.
- [ ] Plugin approval: every plugin selected for the new profile was explicitly approved by the user in the final spec.
- [ ] SOUL: durable identity is concise, stable, and not project-specific.
- [ ] Personality overlay: `/personality validator` is copied by default from active profile config or explicitly skipped/blocked; it is represented as config (`agent.personalities.validator`/`agent.system_prompt`), not as copied SOUL.
- [ ] Context: project rules, if any, belong in `.hermes.md`/`AGENTS.md`, not SOUL.
- [ ] Memory: compact durable facts only; no task diary or stale data.
- [ ] Security: approvals, secret handling, gateway authorization, and sandboxing are deliberate.
- [ ] Configuration UX: user chose `preset`, `guided`, `full_matrix`, or `import_existing` mode.
- [ ] Config manifest: every proposed config change has key, value, type, setter, source, safety note, and validation.
- [ ] Config coverage: all relevant static sections and dynamic families were considered through presets, guided categories, or `references/config-value-matrix.md`.
- [ ] Defaults: low-risk untouched keys are explicitly accepted as defaults or inherited from the source profile.
- [ ] Secrets: secret-bearing settings are represented as `secret_ref` or `manual_user_action`, never raw values.
- [ ] Restart/reload: keys requiring new sessions, `/reset`, gateway restart, or profile reload are called out.
- [ ] Speed: prompt size, tool schema size, skill load, auxiliary models, and compression are considered.
- [ ] Automation: cron jobs are self-contained, pinned where needed, and delivery is explicit.
- [ ] Gateway: tokens, allowlists/pairing, and session policy are configured if gateway is enabled.
- [ ] Validation: `doctor`, `status`, `config check`, `tools list`, `prompt-size`, and smoke chat are planned.
- [ ] Portability: if shared, distribution excludes secrets/runtime data and includes env requirements.
- [ ] Update safety: no Hermes source checkout customization is required.

## Super-Easy Configuration Builder Loop

When the user wants to configure profile settings, do not start by listing every key. Start with the easiest mode that can satisfy the request.

### Modes

1. **Preset mode** — user chooses a profile archetype and Hermes proposes all relevant config values.
   - Examples: `minimal-safe`, `coding-power-user`, `researcher`, `gateway-bot`, `cron-worker`, `desktop-assistant`, `voice-assistant`, `browser-operator`, `sandboxed-worker`.
2. **Guided mode** — ask category-level questions and infer individual keys.
   - Categories: model, tools, terminal/sandbox, display/UI, memory, safety/approvals, web/browser/media, gateway, cron/automation, MCP/plugins, performance/compression, privacy/security, sessions/logging, voice/STT/TTS.
3. **Full matrix mode** — only when requested, walk through every top-level config section using `references/config-value-matrix.md`.
4. **Import existing mode** — clone or import current settings, then ask only what should differ.

### Interaction Pattern

For each category:

1. Explain the category in one sentence.
2. Offer 2-4 practical choices with safe defaults.
3. Convert the choice into explicit manifest entries.
4. Mark untouched low-risk keys as `leave_default` instead of asking about them.
5. Ask follow-up only if ambiguity affects safety, credentials, cost, gateway delivery, external side effects, or validation.

### User-Facing Preview Format

Before approval, show a compact config preview:

```yaml
configuration:
  mode: guided
  changes:
    - key: approvals.mode
      value: off
      why: User requested approval prompts disabled by default for this profile family.
      setter: hermes_config
    - key: terminal.backend
      value: docker
      why: User requested sandboxing.
      setter: hermes_config
    - key: model.provider
      value: openrouter
      why: User chose OpenRouter.
      setter: hermes_model
  requires_user_action:
    - key: OPENROUTER_API_KEY
      why: API key must be added through auth/setup flow, not pasted into the profile spec.
```

## Fast Collaboration Loop

Use the fewest turns necessary. Prefer batched questions with defaults.

### Turn 1: Intake

Ask for or infer these items:

1. Profile purpose, name, and dedicated-profile rationale: why this should be a new profile instead of the default profile.
2. User goals and desired outcomes: what the user wants the profile to help achieve, what success looks like, and any explicit non-goals.
3. Main use cases.
4. Desired surfaces: CLI/TUI, desktop, gateway, cron, ACP, dashboard.
5. Model/provider preference or permission to clone/use current defaults.
6. Tool capability level: minimal, balanced, power-user, or custom.
7. Whether existing `/plugin-builder` generated plugins should be reviewed as profile capability candidates, defaulting to yes when custom capabilities may help the stated goals.
8. Security posture: local trusted, sandboxed, team/shared, or production bot.
9. Speed priority: fastest responses, best quality, cheapest, or balanced.
10. Whether the profile should be portable/shareable.

Use safe defaults when the user does not care:

```text
creation_method: clone if user wants current credentials/tools; blank if they want isolation
approvals_mode: off
agent.system_prompt: "<requested Hermes Agent expert validation prompt; exact text from Configuration Manifest Rules>"
compression_enabled: true
paste_collapse_threshold: 0              # preserve full multi-line paste text in CLI/TUI composers; no paste-token collapse
paste_collapse_threshold_fallback: 0     # same safeguard for terminals without bracketed paste support
paste_collapse_char_threshold: 0         # disable long single-line paste collapse unless the user explicitly opts in
memory: enabled but compact
home_mode: auto
terminal.backend: local unless sandbox requested
tools: balanced minimum for stated use case
skills: install/enable only relevant skills
SOUL: concise identity/personality only
```

A compact first question should explicitly invite goals without creating a long form:

```text
What should this new Hermes profile help you achieve, and why should it be a dedicated profile instead of the default one? Share any goals, desired outcomes, non-goals, surfaces, model/tool preferences, security posture, and speed/cost priorities you already know. If you do not care about a category, say “default it” and I will choose safe defaults.
```

Map every answer through `prompt-enhancer` before updating the profile spec and goal-to-primitives coverage matrix.

### Turn 2+: Refinement

For each user reply:

1. Apply prompt-enhancer extraction, including goals, desired outcomes, success measures, non-goals, and dedicated-profile rationale.
2. Update the profile spec and `goals.goal_to_primitives[]` coverage matrix.
3. If goals imply custom capabilities, run or refresh the read-only generated-plugin inventory and update `capabilities.plugin_candidates`.
4. Update the gold-standard validation ledger, including goal coverage and plugin candidate coverage.
5. Identify remaining blockers, missing choices, unmapped primitive categories, or plugin recommendations requiring user approval.
6. Ask the smallest next question, ask whether to include recommended plugins, or present a proposed final spec if complete.

Avoid asking for low-stakes details that can be defaulted safely.

## Final Confirmation Gate

Before creating anything, present a concise final spec and ask for explicit approval.

Use this format:

```markdown
## Proposed Hermes Profile

- Name: `<profile-name>`
- Purpose: ...
- Dedicated-profile rationale: ...
- Goals and desired outcomes:
  - Goal: ...
    - Desired outcome / success measure: ...
    - Primitive coverage: `profile=...`, `identity=...`, `model=...`, `configuration=...`, `terminal=...`, `capabilities=...`, `memory=...`, `automation=...`, `security=...`, `performance=...`, `validation=...`, `portability=...`
    - Not applicable / skipped primitives: ...
    - Status: `mapped|skipped|blocked`
- Non-goals / intentionally skipped outcomes: ...
- Creation method: ...
- Model/provider: ...
- Terminal/cwd/home policy: ...
- Enabled tools: ...
- Skills: ...
- Profile-builder bootstrap skills copied into the new profile:
  - `profile-builder` → `~/.hermes/profiles/<profile-name>/skills/hermes-agent/profile-builder/`
  - `prompt-enhancer` → `~/.hermes/profiles/<profile-name>/skills/software-development/prompt-enhancer/`
  - `plugin-builder` → `~/.hermes/profiles/<profile-name>/skills/software-development/plugin-builder/`
  - `openrouter-mcp-server` → `~/.hermes/profiles/<profile-name>/skills/autonomous-ai-agents/openrouter-mcp-server/`
- Profile-builder bootstrap personality overlay:
  - `/personality validator` copied from active profile config into `agent.personalities.validator`
  - `agent.system_prompt` set to the approved explicit profile prompt, or to the resolved validator prompt when no explicit prompt override exists
  - `SOUL.md` remains newly customized for this profile and is not copied wholesale

- Memory: ...
- Gateway/cron/MCP/plugins: ...
- Generated plugin review:
  - Scan paths: ...
  - Recommended plugin-builder plugins: ...
  - Skipped plugin-builder plugins: ...
  - Unknown-provenance plugins considered: ...
- Plugins approved for inclusion:
  - Plugin: ...
    - Why it fits: ...
    - Matched goals/primitives: ...
    - Source path: ...
    - Include method: install | copy_profile_local | enable_existing | manual_user_action
    - Required env/config/user actions: ...
    - Validation command: ...
- Security posture: ...
- Repository/authorship governance when a config repo or commits are involved:
  - Git author: `<repo-author-name> <<private-term>>` unless explicitly overridden
  - Commit messages: no AI co-authoring or `Co-authored-by` trailers
  - New repository-author-authored skills: `version: 0.1.0`, `author: <repo-author-name>`, `license: Apache-2.0`
  - Public docs/README: generic profile/config customization guidance, with exact sensitive profile names omitted unless explicitly approved
- Performance choices: ...
- Configuration mode: preset | guided | full_matrix | import_existing
- Config values to set:
  - `<key>` = `<value>` (`<value_type>`, setter: `<setter>`, restart: `<yes/no>`)
- Config values intentionally left at defaults: ...
- Config values skipped/blocked: ...
- Secret/user-action requirements: ...
- Validation command for each config category: ...
- Goal coverage status: every goal has every primitive category mapped, marked not applicable/skipped, or blocked; no unmapped primitives remain.
- Coding contract: mapped with the 200-line file limit, 30-line construct limit, depth-3 nesting limit, test-declaration baseline, real-service test path, witnessed RED command, and BOOTSTRAP/RED/GREEN/REFACTOR validation | not applicable with reason | blocked with exact blocker.
- Writes that will occur: ...
- Validation commands that will run: ...
- Known blockers/assumptions: ...

Do you approve creating this profile exactly as specified?
```

The user must be able to copy the final config preview and understand exactly which keys will change. If the preview is long, group it by category and include a count, but still make the full manifest available on request before approval.

The final spec must distinguish between plugins Hermes recommends and plugins the user has approved. Recommended plugins remain suggestions until the user explicitly approves them for inclusion. If no `/plugin-builder` generated plugins were found or none are a good fit, state that clearly and proceed without plugin inclusion.

The final spec must also show the mandatory profile-builder bootstrap skills separately from optional skills and generated plugins. These bootstrap skills are approved as part of profile creation, but they must never be described as plugin approvals and must never cause plugin directories, secrets, MCP OAuth tokens, logs, caches, or runtime state to be copied.


If the user says yes, approved, proceed, create it, or equivalent, enter creation mode.

If the user says no, not yet, change X, or asks a question, return to collaboration mode and revise the spec.

## Config Setter Selection Rules

When applying `configuration_manifest` entries, choose the safest setter:

1. `hermes_model` for primary provider/model selection, especially OAuth-backed providers or model catalogs.
2. `hermes_auth` for credentials, OAuth, API keys, and credential pools. Never read or write raw token stores.
3. `hermes_config` for non-secret scalar/list/map settings under `config.yaml`.
4. `hermes_tools` for enabling/disabling toolsets instead of editing `toolsets` by hand when possible.
5. `hermes_mcp` for MCP server add/remove/configure/test where possible.
6. `hermes_gateway` for messaging platform setup and restart/status flows.
7. `hermes_cron` or `cronjob` for scheduled jobs.
8. `skill_write` only for approved profile-local skills or references.
9. `manual_user_action` when a setting requires secrets, browser OAuth, a payment/billing step, or a platform admin console.

Never apply a manifest entry until it appears in the final approval spec. Never store raw secrets in `config.yaml`, `SOUL.md`, skill files, or the conversation transcript.

## Existing Profile Rename / Migration Mode

Use this mode when the user asks to rename a profile or propagate a changed profile name/path. Load and follow `references/profile-rename-migration.md`.

Minimum rules:

1. Prefer `hermes profile rename <old> <new>` for the profile home, shell alias lifecycle, active-profile pointer, gateway stop, and Honcho host-key migration.
2. Do not rename while old-profile TUI/chat/gateway processes are active. Scan for `hermes -p <old>` / `-p <old>` and ask before terminating anything.
3. Export the profile and back up any custom wrapper before mutation.
4. Treat profile home and operational cwd separately: after official rename, rename/update the workspace path only when that is in scope, then set `terminal.cwd` with `hermes -p <new> config set terminal.cwd <workspace>`.
5. Official wrapper regeneration may drop custom `cd` behavior. If a fixed workspace is required, rewrite the new wrapper to `cd <workspace>` before `exec hermes -p <new> "$@"`, then validate with a `pwd` smoke test launched from a different directory.
6. When running from another profile, edits to the target profile's skills/memories may trip the cross-profile write guard. If the user explicitly requested the migration and the plan names that target profile, retry only those target-profile edits with `cross_profile: true`.
7. Preserve strict Honcho workspace/user/AI peer IDs unless the user explicitly approves a data-identity migration. Rename host/profile labels and update current peer-card facts without printing raw `apiKey` values.
8. Exclude historical/runtime artifacts from active old-name scans: sessions, logs, caches, state DBs, `.hermes_history`, prior plans, and generated snapshots may retain historical names.

Completion criterion: the new profile shows correctly, old profile/path/wrapper are absent, `terminal.cwd` and wrapper cwd point to the new workspace, active safe surfaces have no standalone old profile name, and health/smoke checks pass or blockers are reported.

## Creation Mode Procedure

Use official Hermes commands and tools. Do not hand-edit secrets.

### 1. Create profile

Choose the command from the approved spec:

```bash
hermes profile create <profile-name>
hermes profile create <profile-name> --clone
hermes profile create <profile-name> --clone-all
hermes profile create <profile-name> --clone-from <source>
hermes profile create <profile-name> --no-skills
hermes profile create <profile-name> --description "<description>"
```

Combine compatible flags when approved, for example:

```bash
hermes profile create <profile-name> --clone --description "<description>"
```

### 2. Configure model/auth

Prefer official flows:

```bash
hermes -p <profile-name> model
hermes -p <profile-name> setup --portal
hermes -p <profile-name> auth
```

For non-secret settings, use:

```bash
hermes -p <profile-name> config set <key> <value>
```

If an API key or OAuth login is required and not already configured, stop and ask the user to complete the official setup flow. Do not ask the user to paste secrets into chat unless they explicitly choose to and the platform is appropriate.

### 2.5 Apply approved configuration manifest

For each `configuration.values.set[]` entry:

1. Confirm it was shown in the final approved spec.
2. Confirm the setter is safe for the value type.
3. Apply non-secret `hermes_config` entries with:

```bash
hermes -p <profile-name> config set <dot.path> <value>
```

4. Route secret or OAuth entries to `hermes auth`, `hermes model`, setup wizards, or `manual_user_action`.
5. Record any skipped or blocked entries in `validation.blockers`.

### 3. Configure terminal and safety

Examples:

```bash
hermes -p <profile-name> config set terminal.cwd /absolute/path
hermes -p <profile-name> config set terminal.backend local
hermes -p <profile-name> config set terminal.home_mode auto
hermes -p <profile-name> config set approvals.mode off
```

Use Docker/Modal/Daytona/Singularity/SSH when sandboxing is required.

### 4. Configure tools

Use official tool management:

```bash
hermes -p <profile-name> tools list
hermes -p <profile-name> tools enable <toolset>
hermes -p <profile-name> tools disable <toolset>
```

Disable broad or risky toolsets that the profile does not need. Filter MCP tools separately.

### 5. Configure SOUL, validator personality overlay, and profile-local skills

Write only the approved profile `SOUL.md`. Keep it focused on identity and style, not project rules. `SOUL.md` must be custom to the target profile; do not copy the source profile's `SOUL.md` wholesale just to inherit validation posture.

Then copy or validate the `/personality validator` overlay when approved or when the user has not opted out of the default:

1. Confirm the final approved spec listed `/personality validator` under the profile-builder bootstrap personality overlay.
2. Read only `agent.personalities.validator` and `agent.system_prompt` from the active profile config.
3. Apply the validator definition to the target profile config as `agent.personalities.validator`.
4. Apply `agent.system_prompt` to the approved explicit profile prompt when present; otherwise apply the resolved validator prompt when the final spec approved the overlay as active.
5. Validate the target profile config contains the validator definition and active system prompt, or report the exact blocker.

First ensure the mandatory profile-builder bootstrap skills are present in the new profile:

1. Confirm the final approved spec listed `profile-builder`, `prompt-enhancer`, `plugin-builder`, and `openrouter-mcp-server` under profile-builder bootstrap skills.
2. Run the bootstrap skill copy protocol from the **Profile-Builder Bootstrap Skills** section.
3. Mark each bootstrap skill status as `copied`, `already_present`, or `blocked` in `capabilities.profile_builder_bootstrap_skills.required[]`.
4. If any bootstrap skill is blocked, stop profile creation validation and report the exact missing source or target-path blocker.

Then configure any additional approved user-selected skills. Use `skill_manage` for profile-local skill creation or `hermes -p <profile-name> skills install ...` for known hub skills. Do not edit bundled repo skills for normal customization.


### 6. Configure memory, gateway, cron, MCP, and additional plugins only if approved

Use official commands:

```bash
hermes -p <profile-name> memory setup
hermes -p <profile-name> gateway setup
hermes -p <profile-name> mcp list
hermes -p <profile-name> mcp install <name>
hermes -p <profile-name> cron list
```

Cron prompts must be self-contained. Gateway delivery and authorization must be explicit.

For approved `/plugin-builder` generated plugins:

1. Confirm the plugin appears in `capabilities.plugin_candidates.user_decisions[]` with `decision: include`.
2. Prefer official `hermes -p <profile-name> plugins install <source>` when the plugin has an installable Git/source URL.
3. For local generated plugins without an install source, copy only the approved plugin directory into `~/.hermes/profiles/<profile-name>/plugins/<plugin-name>/` or another approved profile-local plugin path. Do not copy logs, caches, runtime databases, credentials, `.env` files, auth stores, or unrelated project files.
4. Enable the plugin only if enablement appeared in the final approved spec.
5. Record required env/config values as `manual_user_action` or `secret_ref`, never raw secret values.

## Post-Creation Validation

Run the approved validation suite. Minimum:

```bash
hermes -p <profile-name> profile show <profile-name>
hermes -p <profile-name> doctor
hermes -p <profile-name> status --all
hermes -p <profile-name> config check
hermes -p <profile-name> tools list
hermes -p <profile-name> skills list
hermes -p <profile-name> prompt-size --json
hermes -p <profile-name> chat -q "Reply with OK and the active profile name."
```

For profile-builder bootstrap skills, also validate the target `SKILL.md` files directly:

```bash
python3 - <<'PY'
from pathlib import Path
profile_home = Path('~/.hermes/profiles/<profile-name>').expanduser()
expected = {
    'profile-builder': Path('hermes-agent/profile-builder'),
    'prompt-enhancer': Path('software-development/prompt-enhancer'),
    'plugin-builder': Path('software-development/plugin-builder'),
    'openrouter-mcp-server': Path('autonomous-ai-agents/openrouter-mcp-server'),
}
for name, rel in expected.items():
    path = profile_home / 'skills' / rel / 'SKILL.md'
    assert path.exists(), f'missing {name}: {path}'
    text = path.read_text(encoding='utf-8')
    assert f'name: {name}' in text, f'{path} does not declare name: {name}'
    print(f'OK {name}: {path}')
PY
```

Completion criterion: `hermes -p <profile-name> skills list` and direct file validation both show `profile-builder`, `prompt-enhancer`, `plugin-builder`, and `openrouter-mcp-server`, or the final report lists an explicit blocker.


For the profile-builder bootstrap personality overlay, validate the target config directly without printing unrelated config or secrets:

```bash
python3 - <<'PY'
from pathlib import Path
import yaml
profile_home = Path('~/.hermes/profiles/<profile-name>').expanduser()
cfg = yaml.safe_load((profile_home / 'config.yaml').read_text(encoding='utf-8')) or {}
agent = cfg.get('agent') or {}
validator = (agent.get('personalities') or {}).get('validator')
assert validator, 'missing agent.personalities.validator'
resolved = validator.get('system_prompt', '') if isinstance(validator, dict) else str(validator)
approved_explicit = "You are a Hermes Agent expert focused on ideating, executing, and validating the correct answer. Don't write/edit any files within directories that users of Hermes Agent aren't allowed to touch. Use adversarial review to define an objective validation threshold that proves correctness beyond doubt. Pinpoint the essence of the user's request, convert all unknowns into knowns, and enumerate every problem to solve. Start open-minded across all available tools, then narrow to those you're medium-to-high confident are relevant. Don't continue working down a line of thought or action if you know that it is objectively and provably wrong. Validate your work against official documentation, codebases and first-party sources. Do the minimum work and use the fewest tokens needed to hit the validation threshold. Stop immediately once it's met. Only do what's necessary."
active = agent.get('system_prompt')
assert resolved, 'validator personality resolves to empty prompt'
assert active in {resolved, approved_explicit}, 'agent.system_prompt is neither the validator prompt nor the approved explicit default prompt'
print('OK /personality validator definition present and active system prompt validated')
PY
```

Completion criterion: the validator personality definition and active overlay are present in the target profile config, or the final report lists an explicit blocker. This does not replace the requirement that `SOUL.md` be unique to the new profile.

If gateway, cron, MCP, or dashboard were configured, also run the relevant checks:

```bash
hermes -p <profile-name> gateway status
hermes -p <profile-name> cron list
hermes -p <profile-name> mcp list
hermes -p <profile-name> dashboard --no-open
```

If generated plugins were approved for inclusion, also run:

```bash
hermes -p <profile-name> plugins list
HERMES_PLUGINS_DEBUG=1 hermes -p <profile-name> plugins list
```

For every approved plugin, validate:

1. The plugin exists only under the approved profile-local plugin path or was installed through the approved official source.
2. `hermes -p <profile-name> plugins list` shows the expected enabled/disabled state.
3. Required env/config values are represented as user action blockers or secret references, never raw secrets.
4. The plugin exposes the expected tools/hooks/commands/providers if applicable.
5. The profile smoke test or manual validation prompt exercises the profile goal that justified including the plugin.

For configuration-manifest validation:

1. Run `hermes -p <profile-name> config show` and compare non-secret values against the approved manifest.
2. Run `hermes -p <profile-name> config check` and resolve or report all blockers.
3. Run `hermes -p <profile-name> tools list` if any toolset/platform tool values changed.
4. Run `hermes -p <profile-name> mcp list` and `mcp test <name>` for approved MCP servers.
5. Run gateway/cron/dashboard/platform checks for approved platform or automation entries.
6. Report every manifest entry as one of: `applied`, `left_default`, `skipped`, `blocked_user_action`, or `failed_validation`.
7. Report every `goals.goal_to_primitives[]` entry as one of: `mapped`, `skipped`, `blocked`, or `failed_validation`, and include the command output or observation that proves each mapped primitive is present in the new profile.

The config portion is complete only when every approved manifest entry is accounted for and the final report maps each changed category back to actual command output or a clearly stated blocker.

The profile is complete only when:

1. The profile exists and reports the expected path/name.
2. A smoke chat succeeds or the only blocker is missing user-controlled auth.
3. Tool list output matches the approved spec.
4. The profile-builder bootstrap skills `profile-builder`, `prompt-enhancer`, `plugin-builder`, and `openrouter-mcp-server` are present under the new profile's `skills/` tree and visible to `hermes -p <profile-name> skills list`, or a missing source/auth/setup blocker is explicitly reported.
5. Prompt-size output is reviewed and not obviously bloated for the intended model.
6. `doctor`/`config check` have no unhandled blockers.
7. Any enabled gateway/cron/MCP features have matching validation evidence.
8. Every user goal and desired outcome is represented by validated profile primitives across the full primitive set, or each non-applicable/blocked primitive is explicitly marked with the reason and user action needed.
9. Every approved generated plugin is validated as installed/enabled/skipped/blocked, with evidence from plugin-list output or a clear blocker.
10. Final report maps results back to the gold-standard validation ledger.

## Write Safety

Allowed profile-builder write surfaces after approval:

- `~/.hermes/profiles/<profile-name>/config.yaml` through `hermes config` where possible
- `~/.hermes/profiles/<profile-name>/.env` through setup/auth/config flows for secrets only
- `~/.hermes/profiles/<profile-name>/SOUL.md`
- `~/.hermes/profiles/<profile-name>/skills/**` through `skill_manage` or `hermes skills`
- `~/.hermes/profiles/<profile-name>/cron/**` through `cronjob` or `hermes cron`
- `~/.hermes/profiles/<profile-name>/plugins/**` only when explicitly approved in the final profile spec
- Project-local `.hermes.md`/`AGENTS.md` only when the user explicitly wants project context files

Prohibited or clarification-required surfaces:

- Hermes source checkout files such as `~/.hermes/hermes-agent/**`
- Core source directories/files: `agent/`, `tools/`, `toolsets.py`, `run_agent.py`, `model_tools.py`, `cli.py`, `hermes_cli/`, `gateway/`, `cron/`
- Repo `skills/`, `optional-skills/`, and `plugins/` for personal customization
- Another profile's `skills/`, `plugins/`, `cron/`, or `memories/` unless explicitly targeted
- Raw credential/token stores: `auth.json`, `.anthropic_oauth.json`, `mcp-tokens/**`, raw `.env` reads, project `.env*`
- Runtime stores: `state.db*`, `sessions/**`, `logs/**`, `cache/**`, backups, checkpoints, venvs, managed Node/uv

## Common Pitfalls

1. **Creating before approval.** The final profile spec must be shown and explicitly accepted first.
2. **Asking too many questions.** Batch high-impact choices and default the rest safely.
3. **Skipping prompt-enhancer.** Every user reply in the builder loop must be normalized through prompt-enhancer's intent/safety/validation procedure.
4. **Treating SOUL as project context.** Keep SOUL to identity and voice; put project rules in `AGENTS.md` or `.hermes.md`.
5. **Over-enabling tools.** Fast profiles keep toolsets and MCP tools minimal.
6. **Editing core Hermes files.** Normal profiles are customized through `HERMES_HOME`, not the source checkout.
7. **Ignoring credentials.** Use official auth/setup flows and stop when user action is required.
8. **Declaring success without validation.** Always run objective Hermes commands or report blockers.
9. **Forgetting current-session skill cache.** New or changed skills may need `/reload-skills` or a fresh session.
10. **Assuming profile equals sandbox.** Profiles isolate Hermes state, not the whole filesystem.
11. **Config firehose.** Do not dump every config key unless the user asks for full-matrix mode. Use category cards and presets first.
12. **Raw secret manifest values.** Store only placeholders like `secret_ref:OPENROUTER_API_KEY`; use auth/setup flows for actual secrets.
13. **Wrong setter.** Do not hand-edit toolsets, MCP, gateway, cron, or model credentials when official commands exist.
14. **Unvalidated dynamic keys.** Plugin/MCP/provider-specific keys must be verified against docs, plugin schema, live CLI output, or current config before use.
15. **Missing restart guidance.** Tell the user when `/reset`, new CLI session, gateway restart, or dashboard refresh is required.
16. **Treating goals as chat context instead of profile design inputs.** Every stated goal must become a compact `goals` entry and map across the profile primitive set or be explicitly skipped/blocked.
17. **Dumping all goals into SOUL.** SOUL is only one primitive. Goals usually also imply model, tools, skills, memory, automation, safety, performance, validation, and portability choices.
18. **Letting the default profile carry the goal.** If the user wants the new profile to achieve an outcome, the spec must include the profile-local primitive or approved clone/import path that carries that capability into the new profile.
19. **Silently including generated plugins.** `/plugin-builder` generated plugins are candidates, not defaults. Recommend them with reasons, then wait for explicit user approval.
20. **Executing plugin code during discovery.** Inspect manifests/docs read-only. Do not import plugin modules or run plugin handlers just to decide whether they fit a profile.
21. **Claiming provenance without evidence.** If a plugin lacks a plugin-builder provenance marker or user confirmation, mark provenance as `unknown` and do not claim it was generated by `/plugin-builder`.
22. **Copying plugin secrets or runtime state.** Plugin inclusion must never copy `.env`, auth stores, logs, caches, state databases, or credentials into a new profile.
23. **Recommending plugins that duplicate simpler primitives.** If a built-in toolset, MCP server, skill, or config setting satisfies the goal more simply, prefer the simpler primitive and skip the plugin.
24. **Conflating a gateway with a task transport.** A gateway surface (Telegram, Slack, Discord, etc.) may be only the user's control/review/reminder channel. Do not assume it is also the outbound transport for domain actions (family messages, customer emails, social posts, work notifications). When the user distinguishes them, model the gateway as an approval/control primitive and mark domain delivery as blocked until an approved sender plugin/tool exists.
25. **Treating standard Honcho profile-awareness as strict privacy isolation.** Standard Honcho multi-profile setup shares a workspace/user peer and gives each profile its own AI peer. For sensitive profiles (family, health, legal, finance), explicitly ask whether the user wants strict isolation: separate Honcho workspace, user peer, and AI peer in the target profile-local `honcho.json`, then validate those exact values with `hermes -p <profile> honcho status`.
26. **Forgetting profile-builder bootstrap skills.** Blank profiles and `--no-skills` profiles may not receive local helper skills automatically. Always copy or validate `profile-builder`, `prompt-enhancer`, `plugin-builder`, and `openrouter-mcp-server` into the new profile-local `skills/` tree before declaring profile creation complete.
27. **Copying SOUL to preserve validator behavior.** `/personality validator` is a config overlay (`agent.personalities.validator` plus `agent.system_prompt`), not the profile's durable identity. Copy the validator overlay by default, but write a fresh profile-specific `SOUL.md` every time.
28. **Assuming `terminal.cwd` forces local CLI tool cwd.** For the local terminal backend, Hermes CLI intentionally uses the process launch directory (`os.getcwd()`); `terminal.cwd` is still useful for config display/gateway/cron bridging, but `hermes -p <profile> chat` launched from another directory may run terminal tools there. If a profile needs an alias with a fixed operational workspace, patch or recreate the generated wrapper so it `cd <workspace>` before `exec hermes -p <profile> "$@"`, then validate with a `pwd` smoke test.
29. **Using one board for a portfolio plus all decided units.** When a profile manages a business or creator portfolio that will spawn distinct channels/products/units, keep the portfolio board for ideation, validation, governance, and rollups; create separate approval-gated boards for decided units. Hermes boards are hard isolation boundaries and do not support cross-board links, so specify rollup/context-reference behavior instead of pretending dependencies can link across boards.

30. **Weak model-route locks in specialized profiles.** When the user names an exact provider/model route such as `openai-codex/gpt-5.5`, treat that as a runtime invariant, not just prose. Set both `model.provider` and `model.default`, add the invariant to SOUL/context/skill references when those are in scope, validate `config.yaml` directly, and make smoke commands pass the explicit provider/model flags where supported. Also scan generated profile-local artifacts for forbidden aliases named by the user (for example OpenRouter or slash-style model IDs) so docs, plugins, scripts, and validation prompts cannot drift back to the wrong route.

31. **Assuming pasted secrets became configured secrets.** If the user includes a raw token while approving profile creation, treat it as secret material and never echo or write it into specs, skills, SOUL, reports, or plugin code. Validate only key presence by name through official env/auth/setup surfaces. If the target profile runtime cannot see the secret afterward, report it as a setup blocker (`secret_ref:<NAME>` still needs configuration) rather than claiming external workflows such as HF Jobs or detector calls are ready.

## Verification Checklist

- [ ] `prompt-enhancer` loaded or already present before profile-builder loop begins.
- [ ] Running profile spec maintained and updated after each user reply.
- [ ] Code-capable profiles include the complete `coding_contract` in the working spec and final approval preview; non-coding profiles mark it not applicable with a reason.
- [ ] The copied profile-local `prompt-enhancer` contains exactly one universal coding-contract marker pair and every hard rule before profile completion is claimed.
- [ ] Real behavior/service tests witness RED before production code and target user-facing situations, public contracts, APIs, integration boundaries, or interfaces without test doubles or implementation-detail assertions.
- [ ] User goals, desired outcomes, success measures, and non-goals are captured in the running spec.
- [ ] Every user goal is mapped across the Hermes profile primitive set or each primitive is explicitly `not_applicable`, `skipped`, or `blocked`.
- [ ] The spec explains why the new profile, not the default profile, is responsible for the stated outcomes.
- [ ] `/plugin-builder` generated plugins were inventoried read-only after profile goals were known, or plugin review was intentionally skipped with a reason.
- [ ] Candidate plugins have provenance evidence, fit score, matched goals/primitives, safety notes, and include/skip/block recommendation.
- [ ] User explicitly approved every plugin included in the final profile spec.
- [ ] No plugin code was imported/executed during discovery.
- [ ] No plugin secrets/runtime files were copied into the profile.
- [ ] Final approval preview listed the mandatory profile-builder bootstrap skills separately from optional skills and generated plugins.
- [ ] Final approval preview listed the `/personality validator` overlay separately from SOUL, skills, generated plugins, and optional profile behavior.
- [ ] `profile-builder`, `prompt-enhancer`, `plugin-builder`, and `openrouter-mcp-server` were copied or verified under the new profile's `skills/` tree.
- [ ] `/personality validator` was copied or verified in profile-local config as `agent.personalities.validator` and active `agent.system_prompt`, or a blocker/explicit skip was reported.
- [ ] Bootstrap skill copy copied only `SKILL.md` and allowed support directories, not secrets, plugins, logs, caches, sessions, or runtime state.
- [ ] `hermes -p <profile-name> skills list` or direct `SKILL.md` validation proves all three bootstrap skills are available in the new profile, or blockers are reported honestly.
- [ ] Gold-standard validation ledger checked after each user reply.
- [ ] Final spec presented before any writes.
- [ ] Final approval preview includes goal coverage and has no unmapped primitive categories.
- [ ] User explicitly approved final spec before profile creation.
- [ ] Profile creation used `hermes profile` or `hermes profile install`, not manual directory copying.
- [ ] Config changes used `hermes config` or official setup/auth tools where possible.
- [ ] Configuration mode and manifest were shown before profile creation.
- [ ] Every config manifest entry has an explicit final status: `applied`, `left_default`, `skipped`, `blocked_user_action`, or `failed_validation`.
- [ ] Dynamic provider/plugin/MCP keys were validated against docs, live CLI output, or current profile config before use.
- [ ] Secrets were not read or written directly by the agent.
- [ ] Toolsets/MCP tools match the approved spec.
- [ ] `SOUL.md` is concise and profile-level.
- [ ] Project context files are used only for project-specific rules.
- [ ] Post-creation validation commands ran or blockers are stated honestly.
- [ ] Post-creation validation reports each goal mapping with evidence or a blocker.
- [ ] Final response includes validation evidence mapped to the gold-standard criteria.
