# Portfolio + Channel Kanban Separation for Profile Builds

Use this reference when a profile-building request involves a business, creator operation, product portfolio, or brand that may spawn multiple distinct operating units over time (for example, a faceless YouTube business with multiple decided channels).

## Core pattern

Use a two-level board model:

1. **Portfolio / business board** — manages the entity at large: intake, ideation, research, validation, strategy, approval gates, plugin roadmap, and cross-unit rollups.
2. **Unit / channel / product boards** — one isolated board per decided operating unit: execution, production, delivery, analytics, team/vendor operations, and unit-specific improvement loops.

For Obscurine-style creator businesses:

- `obscurine` = portfolio board for Obscurine management, channel ideation, niche research, competitor research, validation, channel thesis work, go/no-go approvals, plugin planning, and cross-channel rollups.
- `obscurine-channel-<channel-slug>` = one board per approved/decided channel for channel operations: topic bank, packaging, script, originality, voiceover, editing, production QC, upload-readiness, analytics, and team ops.

## Why this split is justified

Hermes Kanban docs state that boards separate unrelated streams of work such as projects, repos, or domains. Boards are the hard isolation boundary: each non-default board has its own SQLite DB, workspaces, logs, and worker env pinning via `HERMES_KANBAN_BOARD`; workers spawned on one board see only that board. Cross-board task links are not allowed.

General product/portfolio practice supports the same separation:

- Keep shared ideation, prioritization, validation, and portfolio rollups together when the work is interrelated.
- Split into separate workspaces/boards when products/channels have distinct audiences, prioritization, workflows, or operating cadence.
- Use a portfolio board to prevent loss of global visibility, track blocked/wait states, and detect scatter across multiple execution boards.

## Profile spec rules

When this pattern applies, include all of these in the final profile specification:

- A primary portfolio Project and portfolio board.
- A naming pattern for unit Projects and unit boards.
- A workspace pattern for each unit.
- A board-routing rule that says which work stays at portfolio level and which work moves to a unit board.
- A cross-board coordination rule: no cross-board links; use free-text references, rollup cards, and summary packets.
- The orchestrator profile used on every board.
- The default worker profile used on every board.
- Approval gates for creating new unit Projects/boards.
- Validation commands for portfolio board existence, Project binding, board naming, and dry-run routing.

## Recommended naming patterns

```yaml
portfolio_project:
  name: <Business Name>
  slug: <profile-or-business-slug>
  bound_board: <business-slug>

unit_project_pattern:
  name: "<Business Name> — <Unit Name>"
  slug: "<business-slug>-<unit-type>-<unit-slug>"
  primary_folder: "<business-workspace>/<unit-type-plural>/<unit-slug>"
  bound_board: "<business-slug>-<unit-type>-<unit-slug>"

unit_board_pattern:
  board: "<business-slug>-<unit-type>-<unit-slug>"
  display_name: "<Business Name> <Unit Type> — <Unit Name>"
```

For Obscurine:

```yaml
portfolio_project:
  name: Obscurine
  slug: <first-name>-obscurine
  bound_board: obscurine

channel_project_pattern:
  name: "Obscurine — <Channel Name>"
  slug: "obscurine-channel-<channel-slug>"
  primary_folder: "<private-term>/hermes-profiles/<private-term>/<first-name>-obscurine/channels/<channel-slug>"
  bound_board: "obscurine-channel-<channel-slug>"
```

## Plugin primitive implications

When the profile spec defines many autonomous work lines, de-dupe plugins by business primitive rather than creating one plugin per sentence. Add class-level private plugins such as:

- `<business>-board-router` — choose portfolio vs unit board and validate Project/board binding.
- `<business>-unit-portfolio` — manage ideation, validation, and portfolio decision flow.
- `<business>-unit-board-factory` — create approved unit Project/board/workspace scaffolds via official Hermes surfaces.
- `<business>-cross-board-rollup` — collect status and flow signals across unit boards without cross-board DB links.
- `<business>-unit-operations` — manage day-to-day work on one decided unit board.

These are plugin specs until approved through plugin-builder. Do not install or enable them as part of profile creation unless the final spec explicitly approves that plugin work.

## Validation prompts and commands

Use live Hermes docs/CLI/source checks when making claims about board mechanics:

- `hermes project --help`
- `hermes project bind-board --help`
- `hermes kanban boards --help`
- `hermes kanban create --help`
- official Kanban docs for board isolation and worker lanes
- local source snippets only to validate installed behavior, not as a substitute for user-facing docs

Add smoke tests:

1. Portfolio work routes to the portfolio board.
2. Decided-channel operational work routes to the channel board pattern.
3. Channel Project/board creation is approval-gated.
4. Cross-board dependencies are represented as rollups/free-text refs, not task links.
5. The orchestrator profile is used on every board and the worker profile exists.

## Pitfalls

- Do not use one giant board for all channel operations once channels are discrete; it mixes execution workflows and hides channel-specific cadence.
- Do not create channel boards during profile creation unless a channel has already been decided and approved.
- Do not attempt cross-board `kanban_link`; Hermes boards intentionally disallow it.
- Do not let the portfolio board become the execution board for every channel. It should retain ideation, validation, governance, and rollup responsibility.
- Do not invent future worker profile names. Use existing profile names or mark specialist workers as future approval-gated work.
