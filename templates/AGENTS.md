# <Profile name> workspace

## Pairing
- Profile: `<profile-name>`
- Profile config home: `<profile-config-home>`
- Workspace: `<workspace-root>`
- The profile config home and workspace are separate boundaries. Never treat one as the other.
- Neither boundary is a sandbox.

## Context and authority
- Scope: this workspace's paths, conventions, and work modes.
- At startup, Hermes loads one project context type. `.hermes.md` or `HERMES.md` wins and walks from the current directory to the Git root. Otherwise, `AGENTS.md` or `agents.md`, `CLAUDE.md`, `.cursorrules`, or `.cursor/rules/*.mdc` loads from the current directory in that order.
- When tools access a subdirectory, Hermes may find nested `AGENTS.md`, `CLAUDE.md`, or `.cursorrules` files inside the active working tree and append their rules to the tool result.
- Before working in a narrower subtree, inspect and apply its discovered context.

## Workspace layout and safety
- Keep plans, reports, backups, and source studies under `.hermes/`.
- Keep disposable source worktrees under `.hermes/worktrees/`. They're test labs, not canonical profile output.
- Reserve `plugins/<slug>/` for durable plugin repository roots and `projects/<slug>/` for other durable project repository roots.
- Keep the workspace root outside Git and don't put production code there.
- Never place secrets or raw sensitive archives in plans, reports, AGENTS.md files, or the vault.

## Coding policy bridge
- `PD-001`: `global-coding-policy` owns the detailed reusable code and Markdown procedure. Load it through SOUL's `Code and Markdown` rule, which also owns the profile's added limits and move rules. This bridge stays here, adds only workspace-specific boundaries, and links both owners.
- Keep installed Hermes source at `$HERMES_HOME/hermes-agent` read-only. Use `.hermes/worktrees/hermes-agent/<task>/` for disposable source study.
- For Hermes code work, identify the installed commit and check the relevant installed source and live official docs. Align the commit, docs, code, runtime, and memory behavior before claiming compatibility.

## Work modes
- **Read-only study:** may read installed source, docs, and profile files. Cite paths, commit, and source alignment.
- **Plan-only:** may write plans and evidence only under `.hermes/`. It mustn't change runtime, source, config, skills, plugins, cron, or memory. Parse the resulting plan and reports as proof.
- **Scratch experiment:** may write only under `.hermes/worktrees/hermes-agent/<task>/` and use a local `mise.toml`. Apply the TDD workflow from `global-coding-policy`, then run focused tests for the changed behavior. Every selected test must pass.
- **Durable repository:** may write only in its own `plugins/<slug>/` or `projects/<slug>/` repository after explicit source and version-control authorization, and must meet every rule in `Durable repositories` below.

## Scratch and durable transitions
- Use supported Hermes settings first for profile configuration.
- Don't commit, push, publish, or deploy scratch work.
- If scratch work becomes durable, stop. Follow the authorization rule in `Git and AGENTS.md files`, then move plugin code to `plugins/<slug>/` or other project code to `projects/<slug>/`.

## Durable repositories
- Each durable repository under `plugins/<slug>/` or `projects/<slug>/` must have its own Git repository, GitHub repository, and remote for that GitHub repository.
- Commit its Mise tasks, run local CI through `mise run ci`, and make GitHub CI run `mise run ci`.

## Git and AGENTS.md files
- Use the GitHub owner and commit identity configured for the workspace.
- Don't add AI co-author credit or AI-generated commit trailers.
- Every repository or worktree must have a root `AGENTS.md`. An inherited upstream file is valid only while it fits that repository or worktree.
- Add a nested `AGENTS.md` only when a real subtree needs different local rules, and keep only that difference in it.
- Before any Git or GitHub action, ask the user to start an explicit source or version-control task for the GitHub-backed repository. That task must authorize each specific action before it occurs.

## Profile isolation and delivery
- Keep each profile and paired workspace isolated unless the user directs a cross-profile change. This includes config, sessions, skills, plugins, cron, and memory.
- Verify the local gateway process, platform adapter, and transport before promising cross-surface delivery.
- A local TUI stores cron output without live delivery. Notifications need an explicit gateway-connected destination.

## Future profile contract
- Pair `<profile-config-root>/<name>` with `<profile-workspaces-root>/<name>` using the same profile name.
- Set that profile's `terminal.cwd` to its paired workspace.
- Define a different role in each named profile's `SOUL.md` and assign a different Honcho AI peer.
- Add a pairing section to each workspace's `AGENTS.md`.
