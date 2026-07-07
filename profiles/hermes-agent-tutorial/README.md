
# Hermes Agent Tutorial Profile

This is a sanitized, reusable Hermes profile package for learning Hermes Agent from first setup through advanced profile, plugin, automation, and troubleshooting workflows.

## What this package includes

- `PROFILE.md` — profile purpose, audience, and learning outcomes.
- `SOUL.md` — tutorial-focused identity text suitable for a public profile distribution.
- `config.public.yaml` — non-secret, public-safe configuration defaults.
- `distribution.yaml` — distribution metadata for people who install or adapt the package.
- `manifest.json` — public-safety manifest listing included and excluded categories.

## Install notes

This package is declarative. It does not include credentials, private memory, sessions, logs, caches, state databases, pairing state, or runtime progress. Installers must run their own Hermes setup/auth flows and decide which tutorial plugins to enable in their own profile.

## Recommended first run

1. Install Hermes Agent and complete `hermes setup` or `hermes setup --portal`.
2. Install the toolbox skills, personalities, and plugin packages from the repository root.
3. Start Hermes in the target profile and run `/personality validator`.
4. Ask `/tutorial map` or `/what-is profile` after enabling the tutorial plugin packages.
