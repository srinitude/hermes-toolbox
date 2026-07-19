# Hermes toolbox repository

## Scope
- This repository is a public Hermes profile distribution.
- Treat the repository as source. Don't edit an installed Hermes profile while maintaining it.
- Check the live Hermes docs and installed source before changing distribution contracts.

## Public boundary
- Never commit credentials, auth data, memories, sessions, logs, caches, local paths, user IDs, or private source material.
- Keep LLM model names, provider choices, fallback chains, and local working directories out of `config.yaml`.
- Keep the failed goal-related plugin and the Herdr plugin out of the repository.
- Keep Claude Code-specific skills and unfinished profile-builder work out of the repository.
- `author: Kiren Srinivasan` is allowed in skill frontmatter.

## Owned files
- `SOUL.md` is the installable identity and universal policy.
- `config.yaml` contains only portable behavior settings.
- `skills/` contains the reviewed public skill set.
- No plugins are currently part of the distribution.
- `templates/AGENTS.md` is an installed but inactive workspace template. Users copy and adapt it in a project.
- `distribution.yaml` defines the Hermes profile distribution.
- Repository policy, CI, tests, and validation tooling are owned support files because Hermes 0.18.2 copies every root entry during install and update.

## Changes
- Load `global-coding-policy` before writing code or Markdown.
- Keep governed code and Markdown files within that policy's limits.
- Use tests first for behavior changes.
- Keep generated evidence and backups under `.hermes/`. Never commit them.
- Don't add a file only to mirror upstream Hermes documentation.

## Verification
- Run `mise run ci` before committing.
- Treat focused checks and whole-repository validation as separate results.
- Recheck the staged tree for secrets and excluded material before any push.
