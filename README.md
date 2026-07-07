# Hermes Toolbox

Public, reusable building blocks for Hermes Agent users: skills, scripts,
sanitized profile packages, sanitized plugin packages, validation checks,
and documented operating patterns.

## What is included

- Public-safe skills under `skills/`.
- Sanitized reusable profile packages under `profiles/` when available.
- Sanitized reusable plugin packages under `plugins/` when available.
- Public validation scripts under `scripts/`.
- Deterministic workflow documentation and installable primitives under `docs/` and `primitives/`.
- The `validator` custom `/personality` preset under `primitives/personalities/validator/`.

## Recommended Hermes workflow

1. Start each session with `/personality validator`.
2. Run user requests through `/prompt-enhancer [prompt]` before execution.
3. Use `/profile-builder [goal]` for separate role, use-case, category, or responsibility profiles.
4. Use `/plugin-builder [goal]` when a reusable integration or automation surface needs a plugin.
5. Validate outputs against explicit source-of-truth checks before handoff.

## Installation

Dry-run by default:

```bash
./scripts/install-toolbox.sh
```

Apply public skills to a Hermes home:

```bash
./scripts/install-toolbox.sh --apply --target "${HERMES_HOME:-$HOME/.hermes}"
```

Install the public `validator` `/personality` preset:

```bash
./scripts/install-toolbox.sh --apply --personalities --target "${HERMES_HOME:-$HOME/.hermes}"
```

Plugin installation is explicit. Sanitized plugin packages are listed by the
installer and are copied only when the plugin flag is supplied.

## Safety model

This repository is intentionally public. It must not contain credentials,
raw memory, sessions, logs, state databases, private profile content, private
plugin state, runtime caches, or user-specific paths. Profile and plugin
packages are shareable only after sanitization and manifest checks.

See:

- `docs/recommended-hermes-workflow.md`
- `docs/public-safety-policy.md`
- `docs/identity-neutrality.md`
- `docs/deterministic-workflow-primitives.md`
- `docs/publishing-criteria.md`
