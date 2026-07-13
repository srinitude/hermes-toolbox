# Hermes profile specification validation pattern

Use this when reconciling or producing a complete Hermes profile specification, especially when the user asks to use current web tooling or to offset model cutoff.

## Read-only validation targets

Prefer first-party/current sources before writing the final artifact:

- Hermes Agent docs:
  - CLI commands reference for `hermes profile`, `hermes project`, `hermes kanban`, `hermes plugins`, `hermes hooks`.
  - Profiles guide for clone semantics and profile isolation.
  - Kanban guide and worker-lanes guide for board isolation, worker assignees, board env vars, lifecycle terminators, and cross-board restrictions.
  - Plugins and Event Hooks guides for plugin discovery, opt-in behavior, supported hook names, and hook return contracts.
- Live Hermes CLI output:
  - `hermes profile list` / `hermes profile show <name>` for installed worker profiles.
  - `hermes project --help` and `hermes kanban boards --help` for command shape on this install.
  - Direct config inspection for current model/provider/reasoning/personality keys without printing secrets.
  - Path preflight for target profile home, workspace, wrapper, and cloned repo target.
- External product first-party docs:
  - YouTube Help and Google Developers docs for YouTube policy, Analytics, title/thumbnail tests, upload/schedule/API behavior.
- Current model data:
  - OpenRouter model details, benchmarks, task classifications, and endpoint/ranking data when the spec makes model choices.

## Hermes profile spec reconciliation checklist

1. Preserve the user's desired final artifact format. If they ask for the entire canonical spec with no updates/changes language, return only the integrated specification, not a changelog.
2. Validate live Hermes capabilities instead of assuming CLI flags, hook names, model slugs, or Kanban behavior from memory.
3. For plugin-heavy specs, verify the supported hook list from current docs/source and remove invented or obsolete hook names. Typical current plugin hooks include `pre_tool_call`, `post_tool_call`, `pre_llm_call`, `post_llm_call`, `pre_verify`, session lifecycle hooks, `subagent_start`, `subagent_stop`, `pre_gateway_dispatch`, approval hooks, transform hooks, and Kanban lifecycle hooks.
4. Separate supported plugin hooks from gateway event hooks and shell hooks. Do not describe gateway-only events as general plugin hooks.
5. For Kanban specs, explicitly preserve board isolation: non-default boards have separate DB/workspaces/logs; `HERMES_KANBAN_BOARD` pins workers; cross-board task links are not allowed, so use rollups and free-text references.
6. For profile creation specs, preflight that target paths do not already exist and that required worker profiles are installed.
7. For public/private posture, apply the deployment's configured private-profile prefix and keep matching profiles out of public toolbox packages.
8. For YouTube/media business specs, ground policy and upload claims in YouTube/Google first-party docs. Treat social/X/current creator discourse as market signal, not policy truth.
9. Keep initial profile creation free of side-effecting automation unless explicitly approved: no channel board creation, plugin creation/enabling, cron/gateway/webhook activation, YouTube upload/schedule, paid spend, or outbound messages.
10. Validation threshold should include direct config checks, Project/board checks, repo commit checks, skill file checks, wrapper cwd smoke test, autonomy/approval smoke test, and dry-run routing checks.

## Output discipline

When the user asks for a reconciled whole artifact, avoid headings or prose such as "changes", "updates", "revisions", "what changed", or "I updated". The final response should read as the canonical artifact itself.
