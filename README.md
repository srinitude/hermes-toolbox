
# Hermes Toolbox

Public, reusable building blocks for Hermes Agent users: skills, scripts, sanitized profile packages, sanitized plugin packages, validation checks, installable primitives, and documented operating patterns.

Repository: https://github.com/srinitude/hermes-toolbox/

## What is included

- Public-safe skills under `skills/`.
- Sanitized reusable profile packages under `profiles/`.
- Sanitized reusable plugin packages under `plugins/`.
- Public validation scripts under `scripts/`.
- Deterministic workflow documentation and installable primitives under `docs/` and `primitives/`.
- The `validator` custom `/personality` preset under `primitives/personalities/validator/`.
- A guided Hermes tutorial profile package and tutorial plugin suite for learning Hermes Agent from setup through mastery.

## Recommended Hermes workflow

1. Start each session with `/personality validator`.
2. Run user requests through `/prompt-enhancer [prompt]` before execution.
3. Use `/profile-builder [goal]` for separate role, use-case, category, or responsibility profiles.
4. Use `/plugin-builder [goal]` when a reusable integration or automation surface needs a plugin.
5. Validate outputs against explicit source-of-truth checks before handoff.

## Installation

### Prerequisites

- Hermes Agent installed and working: `hermes --version`.
- Git installed.
- A target Hermes home or profile selected. By default, commands below use `${HERMES_HOME:-$HOME/.hermes}`.

### Dry-run the installer

```bash
git clone https://github.com/srinitude/hermes-toolbox.git "$HOME/hermes-toolbox"
cd "$HOME/hermes-toolbox"
./scripts/install-toolbox.sh
```

### Install skills, plugins, and the validator personality

```bash
cd "$HOME/hermes-toolbox"
./scripts/install-toolbox.sh --apply --plugins --personalities --activate-validator --target "${HERMES_HOME:-$HOME/.hermes}"
```

What this does:

- Copies public skills into the target Hermes home.
- Copies sanitized plugin packages into the target Hermes home when `--plugins` is supplied.
- Installs the public `validator` personality preset when `--personalities` is supplied.
- Activates the `validator` personality when `--activate-validator` is supplied.
- Does not copy credentials, memories, sessions, logs, caches, state databases, pairing state, or runtime progress.

Plugin installation is explicit. After copying plugins, enable only the plugins you want in the target Hermes profile:

```bash
hermes plugins list
hermes plugins enable hermes-tutorial-compass
hermes plugins enable hermes-concept-glossary
```

To enable every sanitized plugin package after review:

```bash
for plugin_path in "$HOME/hermes-toolbox/plugins"/*; do
  [ -d "$plugin_path" ] || continue
  hermes plugins enable "$(basename "$plugin_path")"
done
hermes plugins list
```

Profile packages under `profiles/` are public-safe distribution material, not raw live profile copies. Review their `README.md`, `PROFILE.md`, `SOUL.md`, `config.public.yaml`, `distribution.yaml`, and `manifest.json` before adapting them into a live profile.

## Comprehensive Hermes Agent install prompt

Give this prompt to a Hermes Agent instance when you want it to install and validate the entire toolbox for you:

```markdown
You are Hermes Agent operating in execute mode.

## Objective
Install and validate the full public Hermes Toolbox from https://github.com/srinitude/hermes-toolbox/ into the target Hermes home or profile, including public skills, sanitized plugin packages, public personality primitives, and profile package documentation.

## Context
- Repository: https://github.com/srinitude/hermes-toolbox/
- Target: use `${HERMES_HOME:-$HOME/.hermes}` unless I specify a named profile or a different target path.
- Continue any existing installation work in this session; do not start over unless I explicitly ask.
- Treat public profile packages as sanitized templates, not as raw live profile state.

## Scope
Allowed actions:
- Clone or update the repository under `$HOME/hermes-toolbox`.
- Run repository validators before installing.
- Run `./scripts/install-toolbox.sh --apply --plugins --personalities --activate-validator --target "${HERMES_HOME:-$HOME/.hermes}"` after validation.
- Enable sanitized plugins only after listing them and confirming they are from this repository.
- Run Hermes CLI checks that prove skills, plugins, and the validator personality are available.

Not in scope:
- Reading or printing secrets.
- Copying private memory, sessions, logs, caches, state databases, pairing state, backups, or runtime progress.
- Editing Hermes Agent source code.
- Installing untrusted project-local plugins outside this repository.

## Write Safety
Allowed write surfaces:
- `$HOME/hermes-toolbox/` for the repository checkout.
- `${HERMES_HOME:-$HOME/.hermes}/skills/` for public skills.
- `${HERMES_HOME:-$HOME/.hermes}/plugins/` for sanitized plugin packages.
- `${HERMES_HOME:-$HOME/.hermes}/config.yaml` via `hermes config` for the validator personality.

Prohibited or clarification-required write surfaces:
- Credential and token stores such as `.env`, `auth.json`, OAuth files, and `mcp-tokens/` unless an official setup/auth command asks me to complete user-controlled setup.
- Runtime stores such as `sessions/`, `logs/`, `cache/`, `state.db*`, `pairing/`, checkpoints, backups, and runtime progress files.
- Another named profile's `skills/`, `plugins/`, `cron/`, or `memories/` unless I explicitly target that profile.
- Hermes Agent core source files.

## Source-of-Truth Checks
- Use `https://hermes-agent.nousresearch.com/docs/` for current Hermes behavior.
- Use live CLI output from `hermes --help`, `hermes skills list`, `hermes plugins list`, and `hermes config check`.
- Use this repository's validators: `scripts/validate-public-safety.py`, `scripts/validate-identity-neutrality.py`, and any package-specific validators.

## Execution Rules
- Convert unknowns into safe assumptions unless they change the target path, profile, credentials, or write safety.
- Do not fabricate outputs.
- If validation fails, fix only within the repository or report the blocker.
- Stop once the validation threshold is met.

## Validation Threshold
The installation is complete only when:
1. The repository is cloned or updated from https://github.com/srinitude/hermes-toolbox/.
2. Public-safety and identity-neutrality validators pass before installation.
3. The installer finishes successfully with skills, plugins, and validator personality requested.
4. `hermes skills list` shows installed toolbox skills.
5. `hermes plugins list` shows copied and enabled plugins selected for this target.
6. `hermes config check` reports no required missing configuration for normal chat use, or any missing user-controlled credentials are listed as blockers.

## Required Output
Return the commands run, the final target path/profile, enabled plugins, validator output, and any blockers that require user action.
```

## Tutorial quick start

After installing and enabling the tutorial plugins:

```text
/personality validator
/tutorial map
/what-is profile
/setup-coach
```

The tutorial suite is intentionally public-safe. It teaches concepts, procedures, and validation patterns without shipping credentials or private runtime state.

## Validation

Before publishing or installing from a checkout, run:

```bash
# If your checkout has approved public skill author metadata, export the
# repository-specific approved author line in your local shell before running
# the public validators. Do not hardcode private/local identity terms in public
# docs or scripts.
python3 scripts/validate-public-safety.py
python3 scripts/validate-identity-neutrality.py
python3 scripts/validate-tutorial-suite.py
```

## Safety model

This repository is intentionally public. It must not contain credentials, raw memory, sessions, logs, state databases, private profile content, private plugin state, runtime caches, pairing data, or user-specific paths. Profile and plugin packages are shareable only after sanitization and manifest checks.

See:

- `docs/recommended-hermes-workflow.md`
- `docs/public-safety-policy.md`
- `docs/identity-neutrality.md`
- `docs/deterministic-workflow-primitives.md`
- `docs/publishing-criteria.md`
