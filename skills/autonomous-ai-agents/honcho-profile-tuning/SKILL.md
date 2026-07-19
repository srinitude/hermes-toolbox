---
name: honcho-profile-tuning
description: "Use when tuning Honcho for a Hermes profile."
version: 1.0.0
author: Kiren Srinivasan
metadata:
  hermes:
    tags: [Honcho, Memory, Profiles, Config, Recall, Session-Strategy]
    related_skills: [honcho, hermes-agent, obsidian]
    created_with_hermes_commit: unknown
    compatibility_reviewed_with_hermes_commit: 5988fe6cd5547d3620df1de889ac6007f5463b4d
---

# Honcho profile tuning

Class procedure for changing Honcho settings so they match a Hermes profile's memory ownership model. Load hub `honcho` for install, CLI catalog, and tool semantics. Use this skill when the question is what this profile should send, inject, and isolate.

## When to use

- User asks to update, audit, or retune Honcho for a profile
- Stale Honcho context is competing with SOUL, AGENTS, live sources, or the current request
- Unrelated tasks share one Honcho session summary
- Profile policy wants reviewed durable facts only, not bulk turn upload
- Creating or cloning profiles that need different AI peers but shared user modeling

## Preconditions

1. Confirm active profile and config path (`$HERMES_HOME/honcho.json` or profile home).
2. Load hub `honcho` if tool or CLI details are unclear.
3. Read live nonsecret config, `hermes honcho status`, user card, recent conclusions, and AI peer representation.
4. Read the profile memory-stack note if the vault has one.
5. Back up `honcho.json` and any mirrored vault notes before edits (dir `0700`, files `0600`).

## Ownership rules

| Layer | Owns | Must not own |
|-------|------|--------------|
| SOUL / live sources | Identity and current truth | Hosted guesses |
| Native memory | Always-on outage-safe constraints | Task residue |
| `state.db` / `session_search` | Exact wording and chronology | Always-injected profile fluff |
| Honcho | Revisable user model and reviewed semantic facts | Secrets, raw archives, agent identity contract |
| Vault | Curated long-form decisions and runbooks | Automatic turn dumps |

Never put credentials in `honcho.json` or vault mirrors. Auth stays in env.

## Audit before changing settings

Collect evidence, then choose settings from evidence:

1. Resolved session key from `hermes honcho status`
2. User peer card quality (stable identity and preferences vs empty)
3. Recent conclusions (durable facts vs temporary task state)
4. AI peer representation (fresh profile facts vs stale models, tools, completed work)
5. Current `recallMode`, `saveMessages`, `sessionStrategy`, observation object
6. Whether the workspace is non-Git, multi-task shared, or one coherent repo

## Choose the profile pattern

### Reviewed-only tools pattern

Use when SOUL and live sources must outrank inferred context, and Honcho should not auto-shape every prompt:

| Setting | Value |
|---------|-------|
| `recallMode` | `tools` |
| `saveMessages` | `false` |
| `sessionStrategy` | `per-session` if one shared cwd or non-Git root would mix work |
| `observation` | user `observeMe: true`, `observeOthers: false`; AI `observeMe: false`, `observeOthers: true` |
| `pinUserPeer` | `false` unless every surface is the same human |
| `userPeerAliases` | empty unless each alias is reviewed |
| `dialecticDepth` | `2` for explicit audit-then-synthesis |
| `reasoningHeuristic` | `true` |
| `reasoningLevelCap` | `medium` |
| `dialecticReasoningLevel` | `low` |
| `dialecticDynamic` | `true` so explicit tool calls may request higher |
| budgets | keep a bounded fallback (`contextTokens`, cadences, `dialecticMaxChars`) under the host block |

Ordinary turns stay local. Explicit `honcho_search`, `honcho_reasoning`, and `honcho_conclude` still send their selected query or fact. Do not put secrets in those calls.

### Hybrid capture pattern

Use only when automatic continuity is worth the risk and conclusions stay clean:

| Setting | Value |
|---------|-------|
| `recallMode` | `hybrid` or `context` |
| `saveMessages` | `true` |
| `sessionStrategy` | fine-grained enough that the resolved key matches one workstream |
| cadences | raise if overhead is high before abandoning hybrid |

If measured overhead is high, raise context and dialectic cadence first. If stale residue is the failure mode, switch to the reviewed-only tools pattern rather than only shrinking budgets.

## Session strategy selection

Pick from the resolved key, not the label:

1. Many unrelated tasks, one key → strategy too coarse
2. One Git root per coherent project stream → `per-repo` can work
3. Different folders are different workstreams → `per-directory`
4. Shared non-Git workspace or mixed monorepo profile work → prefer `per-session`
5. Intentionally one continuous Honcho session everywhere → `global`

`per-repo` on a non-Git workspace often collapses to one host or workspace key and builds one stale mixed summary.

## Config shape rules

1. Put settings under `hosts.<host>` for the profile. Do not leave cadence keys only at the file root when multi-profile isolation matters.
2. Prefer the granular `observation` object over shorthand when documenting intent.
3. Keep `writeFrequency: async` as the engine fallback even when `saveMessages` is false.
4. `dialecticMaxChars` bounds automatic dialectic injection text. Explicit `honcho_reasoning` answers are not limited by that cap.
5. Host-scoped empty aliases and `runtimePeerPrefix: ""` prevent silent identity collapse.

## Agent tool use under tools-only recall

1. Nothing is auto-injected. Call tools only when hosted memory is needed.
2. Warm with `honcho_profile`, then `honcho_search` or `honcho_context`.
3. Use `honcho_reasoning` only when synthesis is worth an LLM call. Broad queries on thin or stale peers often return little.
4. `honcho_conclude` only durable revisable facts. Never conclude active requests, completed goals, abandoned plans, PR numbers, SHAs, or phase status.
5. AI peer must not replace SOUL. Prefer user-peer modeling unless the task is explicit AI self-knowledge.

## Apply and document

1. Write the host block in `honcho.json`.
2. Update vault memory-stack and Honcho notes in the same change when they claim to mirror live config.
3. Do not bulk-delete cloud history as a shortcut. Delete individual conclusion IDs only for PII or clearly wrong durable facts.

## Verify

```bash
hermes honcho mode
hermes honcho strategy
hermes honcho tokens
hermes honcho status
hermes -z 'Reply exactly OK'   # fresh process when available
```

Proof bar:

- Expected mode, strategy, budgets, observation flags
- Connection OK
- No credential fields in `honcho.json`
- Mirrored notes match live nonsecret settings
- User told that the current TUI may keep the old provider object until a new session or restart

## Pitfalls

- Treating hub `honcho` defaults as this profile's policy
- Leaving `saveMessages: true` while claiming reviewed-only writes
- Using `per-repo` because it sounds project-aware when status shows one mixed key
- Pinning or aliasing gateway users into the main peer without review
- Assuming `dialecticMaxChars` truncates explicit tool reasoning results
- Calling broad `honcho_reasoning` on every tune or every turn
- Capturing env-only probe failures (missing `uv`, etc.) as durable Honcho rules
- Writing task progress or one-off IDs into skills or conclusions

## References

- `references/reviewed-only-template.md` — portable host template for the reviewed-only pattern
