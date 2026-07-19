# Hermes Toolbox

Hermes Toolbox is a public Hermes profile distribution. It packages the identity, behavior settings, workspace policy template, and reviewed skills used by the default profile, without personal data or LLM choices.

## Included

- `SOUL.md`: installable identity and universal operating policy
- `config.yaml`: portable behavior settings only
- `skills/`: ten reviewed skills for coding policy, planning, review, skill lifecycle, Honcho tuning, and Hermes maintenance
- `templates/AGENTS.md`: workspace guidance with generic paths and identity placeholders
- `distribution.yaml`: native Hermes profile distribution metadata
- Repository policy, CI, tests, and validation tooling: inert support files that travel with the profile and validate the exact distribution source

No plugins are included.

## Excluded

- Credentials, auth files, API keys, tokens, and private URLs
- Memories, user profiles, sessions, logs, databases, caches, plans, and local state
- LLM model names, provider choices, auxiliary model settings, and fallback chains
- Local working directories, personal IDs, email addresses, and private notes
- The Herdr agent-state plugin and the failed goal-related plugin
- Claude Code-specific skills
- Unfinished profile-builder work and skills changed as part of that work
- Model-provider plugins maintained in separate repositories

## Requirements

- Hermes Agent 0.18.2 or newer
- Git
- A model and credentials selected locally after installation
- `crit` only when using the `crit` or `crit-cli` skills
- Honcho only when using `honcho-profile-tuning`

## Install

Install from the repository's default branch and create the `hermes-toolbox` wrapper:

```bash
hermes profile install github.com/srinitude/hermes-toolbox --alias --yes
```

The public config intentionally has no LLM model or provider. Select your own model inside the new profile, then start it:

```bash
hermes-toolbox model
hermes-toolbox
```

If the wrapper directory isn't on `PATH`, use:

```bash
hermes --profile hermes-toolbox model
hermes --profile hermes-toolbox
```

Run `hermes-toolbox setup` if the chosen provider still needs local authentication.

## Security settings to review

This public distribution uses a safer approval default than the source profile:

- `approvals.mode: smart`
- `skills.write_approval: false`
- `memory.write_approval: false`

The terminal backend is local, not sandboxed. Smart mode lets Hermes request approval for commands it judges dangerous, while the deny list blocks a small set of destructive shell patterns. Review `config.yaml` before installation. Use approval mode `off` only as an explicit opt-in on a trusted machine.

## Updates and remote HEAD

Hermes records the Git source during installation. This command re-clones the repository at its current remote HEAD and updates the profile:

```bash
hermes profile update hermes-toolbox --yes
```

Hermes preserves the installed `config.yaml` by default, so your local model and provider choices survive updates. Use `--force-config` only when you intend to replace the whole config with the public copy. After that flag, select a local model again.

Hermes 0.18.2 copies every repository root entry during install and update. This distribution therefore declares its policy, CI, tests, and validation tooling as owned support files alongside `SOUL.md`, `skills/`, and `templates/`. Updates replace every declared path except the preserved `config.yaml`. Keep profile-local additions outside those paths or maintain them in a separate profile.

## Workspace AGENTS template

`AGENTS.md` is workspace-scoped in Hermes, so a profile distribution can't choose the right workspace root for you. Copy the template into the root of a dedicated profile workspace:

```bash
cp ~/.hermes/profiles/hermes-toolbox/templates/AGENTS.md /path/to/profile-workspace/AGENTS.md
```

Replace every angle-bracket placeholder and remove any rule that doesn't match the workspace. The template expects a non-Git workspace root with durable repositories under `projects/` or `plugins/`. Each nested repository still needs its own root `AGENTS.md`.

## Validate a checkout

```bash
mise run ci
```

The CI contract checks the distribution manifest, public config boundary, expected skill set, frontmatter, size limits, privacy patterns, and explicit exclusions.

## Repository maintenance

The repository follows the remote default branch rather than a hard-coded branch name. New releases amend the public history to one root commit only when the repository owner intentionally performs a history reset. Normal users should update with `hermes profile update`, not by force-resetting an installed profile.
