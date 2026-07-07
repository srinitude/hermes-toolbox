---
name: honcho-memory-provider
description: Configure and verify Honcho as Hermes Agent's external memory provider with profile-aware peer isolation.
version: 0.1.0
author: Kiren Srinivasan
license: Apache-2.0
metadata:
  hermes:
    tags: [hermes-agent, memory, honcho, profiles, configuration]
    related_skills: [hermes-agent]
---

# Honcho Memory Provider for Hermes

## When to Use

Use this skill when the user asks to enable, configure, verify, tune, or troubleshoot Honcho memory in Hermes Agent, especially when profile isolation matters.

Typical requests:

- "Use Honcho as Hermes memory provider."
- "Make Honcho memory work across profiles without bleed."
- "Set up Honcho with this API key."
- "Why is Honcho not active / not showing tools?"
- "Optimize Honcho for intelligence, correctness, determinism, speed, cost, security, or isolation."

## Safety Boundaries

- Treat Honcho API keys as secrets. Do not print them in final replies, logs, or markdown notes.
- Prefer official Hermes CLI flows over direct raw edits when possible: `hermes memory setup honcho`, `hermes honcho status`, `hermes honcho sync`.
- If direct file edits are needed, write only profile-local Hermes config surfaces:
  - `$HERMES_HOME/config.yaml`
  - `$HERMES_HOME/honcho.json`
  - `$HERMES_HOME/.env` for secrets when using env-var setup
- Do not edit Hermes source checkout files just to customize Honcho behavior.
- Do not write secrets to `/etc/hermes/.env` or other world-readable managed-scope files.

## Source of Truth

Before acting on current behavior, check first-party references:

- Official docs: `https://hermes-agent.nousresearch.com/docs/user-guide/features/honcho`
- Memory providers docs: `https://hermes-agent.nousresearch.com/docs/user-guide/features/memory-providers`
- Profiles docs: `https://hermes-agent.nousresearch.com/docs/user-guide/profiles`
- Live CLI: `hermes memory --help`, `hermes memory status`, `hermes honcho --help` after activation

See `references/honcho-profile-isolation.md` for a condensed setup and verification pattern from a successful session.

## Operational Setup Pattern

1. Verify docs and live CLI surface.
   - `hermes memory status`
   - `hermes memory setup --help`
   - `hermes memory setup honcho` for direct provider setup.
2. Run setup through the official wizard when possible.
   - Cloud/API-key path can be piped non-interactively if the user explicitly provides a key.
   - The setup command auto-installs `honcho-ai` when needed.
3. Choose conservative defaults unless the user says otherwise:
   - `recallMode: hybrid` for auto context plus tools.
   - `writeFrequency: async` for speed and low blocking cost.
   - `sessionStrategy: per-session` for deterministic clean sessions with cross-session context via Honcho.
   - `contextTokens: 1200` as a bounded context budget.
   - `dialecticCadence: 2` to avoid an LLM call every turn while preserving good recall.
   - `dialecticReasoningLevel: low`, `reasoningLevelCap: high`, heuristic enabled.
   - `observationMode: directional` for full user/AI peer modeling.
4. After setup, verify activation:
   - `hermes memory status` should show provider `honcho` and status available.
   - `hermes honcho status` should show connection `OK`, masked auth, workspace, user peer, AI peer, recall, cadence, budget, observation, and write frequency.
5. For existing profiles, run:
   - `hermes honcho sync`
   - `hermes honcho status --all`
   - `hermes honcho peers`
6. Tell the user to start a new Hermes session for Honcho context/tools to be injected into the runtime.

## Profile Isolation Contract

Hermes profiles are isolated by `HERMES_HOME`; each profile has its own config, `.env`, memory, sessions, skills, cron, logs, and state.

Honcho's intended multi-profile model is:

- Shared workspace and user peer for the same human.
- Dedicated AI peer per Hermes profile.
- Separate peer representations/cards so one profile's AI identity does not bleed into another profile.

Important nuance:

- Existing profiles can be backfilled with `hermes honcho sync`.
- New profiles created with `--clone` or `--clone-all` inherit Honcho configuration and get a dedicated Honcho host/AI peer.
- Plain blank profiles created with `hermes profile create NAME` are not automatically hard-enforced by ordinary user-local config. If the user wants all future blank profiles to use Honcho, clarify whether they want managed scope, source-code changes, or a wrapper/procedure.

## Validation Checklist

A Honcho setup is complete only when:

- `hermes memory status` reports provider `honcho` and available status.
- `hermes honcho status` connects successfully without exposing the full secret.
- `$HERMES_HOME/config.yaml`, `$HERMES_HOME/honcho.json`, and `$HERMES_HOME/.env` are mode `0600` when present.
- `hermes honcho status --all` shows every existing profile that should be configured.
- The final response explains the future-profile boundary accurately: cloned profiles inherit; blank profiles require an explicit enforcement mechanism if desired.

## Pitfalls

- Do not rely only on `hermes memory status`; also run `hermes honcho status` because it exercises the provider-specific config and connection.
- `hermes honcho` subcommands may not appear until `memory.provider: honcho` is active.
- Some Honcho status fields may read root-level config while setup writes host-level values; if cadence or liveness tuning appears inconsistent, verify effective config via the provider's resolver or mirror key tuning at both root and host levels.
- Avoid broad promises like "every profile that will ever be created" unless you know how the profile will be created. Blank future profiles are different from cloned profiles.
- Never include the user's Honcho API key in a skill, memory, reference file, or final answer.