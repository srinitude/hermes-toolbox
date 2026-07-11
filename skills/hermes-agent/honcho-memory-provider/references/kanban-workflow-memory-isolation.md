# Kanban Workflow Memory Isolation with Honcho

Use this reference when a Hermes setup combines Honcho with Hermes Kanban, multi-profile worker lanes, phase-gated workflows, long-running work runs, context bundles, or profile-specific worker identities.

## Source-of-Truth Boundary

Keep the operational state boundary explicit:

- The Kanban board is the operational source of truth for task state, phase status, assignments, comments, blocks, approvals, and retries.
- Honcho is for profile-aware user/AI peer context, durable preferences, semantic recall, session summaries, and cross-session continuity.
- Do not rely on Honcho as the sole record of todo state, approvals, deploy decisions, phase completion, or review verdicts.
- Store full artifacts and full context bundles in board comments, files, repositories, or other explicit artifacts; store only durable summaries or conventions in memory.

## Peer Isolation Pattern

The standard multi-profile pattern is:

- one shared workspace for the same human and workflow family;
- one shared user peer for that human unless the domain is sensitive;
- one AI peer per Hermes profile, so each worker lane has its own AI representation and identity card.

For sensitive workflows, consider stricter isolation:

- separate Honcho workspace per sensitive workflow;
- separate user peer when the human's role/persona must not bleed across profiles;
- separate AI peer per worker profile;
- profile-local `honcho.json` and `$HERMES_HOME/.env` setup through official Hermes flows only.

After adding or installing workflow profiles, first run read-only validation with `hermes honcho status --all` and `hermes honcho peers`. If the new profiles appear with Honcho disabled or unsynced, run `hermes honcho sync` only when Honcho enrollment is in scope and the user has approved cross-profile memory configuration. Profile installation and Honcho peer enrollment are separate actions.

## What to Remember

Good Honcho candidates:

- Stable user preferences about review depth, communication style, speed/cost tradeoffs, and risk tolerance.
- Durable workflow conventions such as expected `context_bundle` fields, approval style, phase ownership, and escalation preferences.
- Profile-specific AI peer responsibilities, e.g. orchestrator routes only, reviewer challenges assumptions, deployer requires approval.
- Reusable lessons that improve future profile behavior without depending on a transient task ID.

Bad Honcho candidates:

- Raw secrets, API keys, tokens, OAuth data, or credential paths.
- Full context bundles when the board or file artifact is the source of truth.
- Ephemeral task progress, temporary todo state, deploy status, or review verdicts that belong in Kanban.
- Logs, sessions, cache, state databases, pairing state, auth stores, or runtime files.
- Large raw artifacts that should be linked from board comments instead.

## Work Metadata Policy

Use workflow metadata consistently:

- `work_key` can be remembered only as part of a durable convention or user preference, not as a long-term task diary.
- `work_run` is usually ephemeral and belongs on the board.
- `context_bundle` should be summarized only when it captures a durable workflow lesson or preference.
- Reviewer decisions and deployment approvals belong in Kanban comments/blocks or source-controlled artifacts; memory may store only the stable preference behind the decision.

## Balanced Defaults for Kanban Worker Profiles

Use the normal Honcho setup flow, then prefer bounded settings unless the user asks for deeper recall:

```json
{
  "recallMode": "hybrid",
  "writeFrequency": "async",
  "sessionStrategy": "per-session",
  "contextTokens": 1200,
  "contextCadence": 1,
  "dialecticCadence": 2,
  "dialecticDepth": 1,
  "dialecticReasoningLevel": "low",
  "reasoningHeuristic": true,
  "reasoningLevelCap": "high",
  "observationMode": "directional",
  "saveMessages": true,
  "timeout": 15
}
```

These defaults aim for speed and cost control while preserving enough context for intelligence and correctness. Increase context budget, cadence, or reasoning depth only when validation shows missing context is causing failures.

## Profile Builder Integration

When a profile-builder workflow is designing Kanban workers with Honcho:

- represent Honcho under the memory primitive for every phase;
- decide whether standard shared workspace/user peer plus one AI peer per Hermes profile is sufficient;
- record strict-isolation needs as security and memory requirements;
- keep the board as the source of truth in the validation ledger;
- mark missing Honcho API credentials as user-action blockers, never as values in docs or config text.

## Plugin Builder Integration

When a plugin-builder workflow creates a Kanban-related plugin:

- do not let the plugin persist task state to Honcho as a substitute for board updates;
- allow the plugin to use memory only for durable preferences or peer context when a public memory API/tool supports it;
- never copy Honcho config, `.env`, auth stores, sessions, logs, cache, or runtime data into a plugin or distribution;
- validate missing-env behavior without printing secrets.

## Validation

A Honcho/Kanban setup is complete only when the following checks pass or blockers are reported:

```bash
hermes memory status
hermes honcho status
hermes honcho status --all
hermes honcho peers
```

Validation expectations:

- memory provider is `honcho` and available;
- auth is masked, never printed in full;
- workspace/user/AI peer values match the approved isolation model;
- there is an AI peer per Hermes profile that participates in the workflow;
- recall mode, context budget, cadence, observation mode, and write frequency match the approved settings;
- profile-local config/honcho/env files are restrictive when present;
- no full secret or runtime data appears in docs, skills, plugins, distributions, or final reports.

## Source Coverage Summary

This reference incorporates the workflow package's memory-relevant ideas from all file classes: phase identities, toolset choices, context-bundle handoffs, review gates, safe distribution boundaries, and phase-worker skill guidance. It intentionally keeps the Kanban board as the operational state machine and Honcho as bounded, profile-aware memory.
