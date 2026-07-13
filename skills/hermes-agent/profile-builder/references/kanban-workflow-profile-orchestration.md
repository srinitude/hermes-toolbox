# Kanban Workflow Profile Orchestration

Use this reference when a profile-building request implies a durable multi-agent pipeline, phase-gated work, named worker profiles, human-in-the-loop review, Hermes Kanban, or a shareable multi-profile agent distribution.

## Source Pattern

The incorporated Kanban workflow package is a reusable pattern, not a file tree to copy verbatim:

- A top-level workflow document explains the overall phase sequence, board settings, installer behavior, and security expectations.
- A top-level config snippet defines Kanban board/dispatcher defaults.
- A safe installer is only an orchestration convenience. The official installation unit remains each local profile distribution installed with `hermes profile install <local-dir>`.
- Each `profiles/<phase>/` directory is a complete profile distribution with `distribution.yaml`, `SOUL.md`, `config.yaml`, `README.md`, and a bundled worker skill.
- The workflow uses `work_key`, `work_run`, and `context_bundle` to make handoffs explicit and auditable.
- Side-effecting or production-impacting phases use `review-required` gates instead of silently completing.

## Phase Catalog Pattern

A Kanban lane bundle should usually separate these responsibilities into named profiles or lanes:

| Phase / lane | Primary responsibility | Common toolset shape | Gate style |
| --- | --- | --- | --- |
| Orchestrator | Decompose, route, monitor, and keep phase order deterministic | `kanban`, `memory`, `skills`; avoid broad implementation tools | Creates/links tasks; does not implement phase work |
| Brainstorm | Explore alternatives and gather context | `kanban`, read/search tools, memory, skills | Human-in-the-loop optional |
| Design | Produce architecture/design artifacts and external design-tool outputs | `kanban`, file/terminal/web as needed, skills, approved MCP/plugin integrations | Human review before downstream work |
| Plan | Convert design into bite-sized implementation tasks | `kanban`, file/terminal, memory, skills | Completes with a structured context bundle |
| Test | Establish RED tests and validation criteria | `kanban`, file/terminal, skills | Blocks if requirements are ambiguous |
| Build | Implement GREEN/REFACTOR work | `kanban`, file/terminal, skills | Blocks on failing tests or unclear spec |
| Document | Update docs, handoff notes, and usage guidance | `kanban`, file/terminal, skills | Completes with docs evidence |
| Review | Check correctness, security, and spec compliance | `kanban`, file/terminal, memory, skills | Approves, blocks, or loops work back |
| Deploy | Prepare or run deployment only after approval | `kanban`, file/terminal, skills, approved sender/deploy tools | `review-required` before irreversible side effects |
| Maintain | Monitor, triage regressions, and create follow-up tasks | `kanban`, read/search tools, memory, skills | Creates follow-up tasks or blocks with evidence |

Treat this as an archetype. Add, remove, or rename phases only when the user's goals require it, and record the reason in the profile spec.

## Optimization Mapping

Map user optimization goals to concrete profile primitives:

- **Intelligence:** specialize each phase identity; bundle small phase-specific skills; require structured `context_bundle` outputs; keep a review loop that can route work back.
- **Determinism:** use stable `work_key` and `work_run`; define phase order; require explicit completion/block contracts; keep one source-of-truth board.
- **Correctness:** separate plan/test/build/review/deploy; require evidence in comments or context bundles; use HITL and `review-required` gates for decisions with risk.
- **Speed:** minimize each profile's toolset; avoid loading implementation tools into the orchestrator; keep bundled skills compact; use dry-run checks before live actions.
- **Cost:** pick model quality per phase; reserve expensive/high-reasoning models for brainstorm, design, and review; use cheaper or faster models for mechanical document/test/build loops when safe.
- **Security:** use `$HERMES_HOME`-aware installers, placeholders-only env docs, backups before config changes, no raw secret reads, and explicit approval for sender/deploy plugins.
- **Hermes adherence:** prefer profile distributions, `hermes profile install`, official config/tool/kanban surfaces, profile-local skills, and skill references over source-code edits.

## Builder Intake Additions

When the user's profile-building goal hints at a workflow or pipeline, ask or infer only the high-impact choices:

1. Is the target a single profile, a shareable profile distribution, or a multi-profile Kanban lane bundle?
2. What are the phases/lane responsibilities and which phases are allowed to perform side effects?
3. What must be carried through every task: `work_key`, `work_run`, `context_bundle`, artifact paths, approvals, reviewer notes, or deployment state?
4. Which phases require human-in-the-loop review or `review-required` blocking?
5. Which external services are needed, and are they better represented as MCP, a generated plugin, a profile config value, a cron job, or a manual user action?
6. What is the desired speed/cost/quality split by phase?
7. Should the bundle be portable/shareable, and what env requirements must be declared without secrets?

Default safely when the user does not care: keep the orchestrator minimal, use profile-local skills for phase rules, avoid plugins unless an extension surface is truly needed, and require approval for irreversible actions.

## Profile Spec Additions

When applicable, add a compact `kanban_workflow` section to the running profile spec:

```yaml
kanban_workflow:
  board_source_of_truth: hermes_kanban
  workflow_shape: single_profile | multi_profile_bundle | profile_distribution
  phases:
    - name: brainstorm
      role: idea generation and context gathering
      profile_name: <profile-name>
      toolsets: [kanban, web, memory, skills]
      model_policy: quality | balanced | fast | cheap
      required_inputs: [work_key, work_run]
      emits: [context_bundle]
      gates: [human_review]
  handoff_contract:
    required_fields: [work_key, work_run, phase, summary, artifacts, decisions, risks, next_phase]
    completion: kanban_complete or kanban_comment plus kanban_block for review-required work
  installer_policy:
    official_unit: profile_distribution
    command: hermes profile install <local-dir>
    dry_run_required: true
    direct_profile_copy: prohibited
  validation:
    yaml_parse: required
    skill_frontmatter_parse: required
    dry_run_installer: required
    no_secret_scan: required
```

Every phase must still map across the normal profile-builder primitive categories: profile, identity, model, configuration, terminal, capabilities, memory, automation, security, performance, validation, and portability.

## Distribution and Installer Rules

- Treat each profile directory as the profile distribution unit when it contains `distribution.yaml`.
- A top-level installer may orchestrate multiple local `hermes profile install` calls, but it should not be the only documented path.
- Installers should support dry-run, respect `$HERMES_HOME`, back up config before mutation, use official `hermes config set` for non-secret settings, and avoid direct YAML rewrites when possible.
- Do not copy profile directories manually into `$HERMES_HOME/profiles/` as the primary flow.
- Env requirements belong in `distribution.yaml` and docs as placeholders or env names only.

## Installation Execution Pattern

When the user explicitly approves installing a multi-profile Kanban bundle, keep the install path narrow and auditable:

1. Run a read-only preflight first: resolve the source path, list existing target profile names, check active Hermes/gateway processes, and run the bundle installer in `--dry-run` mode.
2. Confirm the dry-run uses `hermes profile install` and `hermes config set`, not direct profile copying or raw config rewrites.
3. If preflight is safe and the user has explicitly requested installation, run the installer once with its non-interactive approval flag.
4. Validate installation by checking:
   - all expected `$HERMES_HOME/profiles/<profile-name>/` directories exist;
   - each profile has `distribution.yaml`, `SOUL.md`, `config.yaml`, `README.md`, and bundled worker skill files;
   - every worker skill is visible via `hermes -p <profile> skills list`;
   - expected Kanban/dashboard config keys were applied;
   - a backup was created before config mutation;
   - no plugin directories were introduced unless a separate plugin approval/spec justified them.
5. Treat credentials printed as required by distributions as user setup actions, not as values to inspect or write.

## Validation Ledger for Kanban Profile Bundles

Before final approval or creation, require evidence for each applicable item:

- Source distribution manifests parse.
- Profile `SOUL.md` files are concise, phase-specific identities.
- Bundled `SKILL.md` frontmatter parses and each skill is loadable.
- Toolsets match each phase and avoid unnecessary capabilities.
- Orchestrator has routing capabilities but no implementation/deployment tools unless explicitly justified.
- Model/provider and env requirements are consistent and placeholders-only.
- `work_key`, `work_run`, and `context_bundle` handoff contracts are documented.
- HITL and `review-required` gates are explicit for side-effecting phases.
- Installer dry-run proves no live Hermes profile/config mutation will happen.
- No secrets, sessions, logs, caches, state databases, auth stores, pairing state, or runtime files are included in a distribution.

## Source Coverage Summary

This reference incorporates the reusable patterns from all source file classes in the corrected workflow package:

- top-level workflow docs and config snippets;
- safe installer behavior;
- every phase README;
- every phase `SOUL.md` identity;
- every phase `config.yaml` toolset/model pattern;
- every phase `distribution.yaml` env/manifest pattern;
- every phase bundled `kanban-workflow-guide` skill.

Do not copy the original package verbatim into a new profile. Use this reference to design a fresh profile spec, then apply the profile-builder final approval gate before any live profile writes.
