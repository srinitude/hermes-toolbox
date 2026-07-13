# Portfolio and Unit Kanban Separation for Profile Builds

Use this reference when a profile-building request involves a business, creator operation, product portfolio, or brand that may spawn multiple operating units over time.

## Core pattern

Use a two-level board model:

1. **Portfolio or business board** — manages entity-wide intake, ideation, research, validation, strategy, approval gates, plugin roadmap, and cross-unit rollups.
2. **Unit, channel, or product boards** — one isolated board per approved operating unit for execution, production, delivery, analytics, team/vendor operations, and unit-specific improvement loops.

For an example creator business, use `example-business` as the portfolio board and `example-business-channel-example-unit` as one approved channel board. Keep generic examples generic; use the user's real names only in the private approved profile specification.

## Why this split is justified

Hermes Kanban boards separate unrelated streams such as projects, repositories, or domains. Each non-default board is an isolation boundary with its own database, workspaces, logs, and worker environment. Workers on one board see only that board, and cross-board task links are not allowed.

General portfolio practice supports the same separation:

- Keep shared ideation, prioritization, validation, and rollups together when work is interrelated.
- Split execution when units have distinct audiences, priorities, workflows, or operating cadence.
- Preserve global visibility with rollup cards and summary packets on the portfolio board.

## Profile spec rules

When this pattern applies, include:

- a primary portfolio Project and board;
- a naming pattern for unit Projects and boards;
- a workspace pattern for each unit;
- routing rules for portfolio versus unit work;
- free-text or rollup coordination instead of cross-board links;
- orchestrator and default worker profile roles;
- approval gates for creating new unit Projects or boards;
- validation commands for Project binding, board naming, and dry-run routing.

## Generic naming example

```yaml
portfolio_project:
  name: "Example Business"
  slug: example-business
  bound_board: example-business

unit_project_example:
  name: "Example Business — Example Unit"
  slug: example-business-channel-example-unit
  primary_folder: "$HOME/hermes-workspaces/example-business/channels/example-unit"
  bound_board: example-business-channel-example-unit
```

## Plugin primitive implications

De-duplicate plugins by business primitive rather than creating one plugin per sentence. Possible approval-gated plugin specifications include:

- `example-business-board-router` — choose portfolio versus unit board and validate Project binding;
- `example-business-unit-portfolio` — manage ideation, validation, and portfolio decisions;
- `example-business-unit-board-factory` — create approved Project, board, and workspace scaffolds;
- `example-business-cross-board-rollup` — collect status without cross-board database links;
- `example-business-unit-operations` — manage day-to-day work on one approved unit board.

These remain specifications until approved through plugin-builder. Do not install or enable them during profile creation unless the final spec explicitly approves that work.

## Validation

Use current Hermes docs, CLI, and installed source for board-mechanics claims:

- `hermes project --help`
- `hermes project bind-board --help`
- `hermes kanban boards --help`
- `hermes kanban create --help`
- official Kanban documentation for isolation and worker lanes

Require smoke tests proving portfolio routing, unit routing, approval-gated unit creation, rollup-based cross-board coordination, and availability of the approved orchestrator and worker profiles.

## Pitfalls

- Do not use one giant board once units have distinct execution workflows.
- Do not create unit boards before the unit is approved.
- Do not attempt cross-board task links.
- Do not let the portfolio board absorb every unit's execution work.
- Do not invent future worker profile names; use approved roles or mark them as future work.
