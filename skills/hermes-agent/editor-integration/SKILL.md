---
name: editor-integration
description: "Connect local editors/IDEs to remote Hermes hosts and configure safe $EDITOR/VISUAL behavior for headless servers."
version: 0.1.1
author: Kiren Srinivasan
license: Apache-2.0
metadata:
  hermes:
    tags: [hermes, editor, acp, zed, remote-development, ssh]
    related_skills: [hermes-agent, hermes-config-audits]
---

# Editor Integration

## When to Use

Use this skill when the user wants to use a local editor/IDE with Hermes running on another machine, set `$EDITOR`/`$VISUAL`, configure ACP editor integration, or connect Zed/VS Code/JetBrains to a remote Hermes profile over SSH.

## Core principles

1. **Separate the control host from the GUI host.** A VPS/headless server can run Hermes, shells, language servers, and ACP, while the editor GUI runs locally.
2. **Validate the live install before editing config.** Check the editor CLI, `hermes acp --check`, `uv`, SSH reachability, and whether `DISPLAY`/`WAYLAND_DISPLAY` exists.
3. **Do not set a GUI-only editor command blindly on headless hosts.** On servers without a display, raw `zed --wait`, `code --wait`, etc. may fail or hang. Use a wrapper that prefers the GUI command when a display exists and falls back to a terminal editor otherwise.
4. **Use official remote-development paths for local GUI editing.** For Zed, local Zed Remote Development over SSH is the supported path for editing remote files. For Hermes-as-editor-agent, use ACP (`hermes acp`) launched by the editor or over SSH.
5. **Keep secrets out of editor settings.** Zed/VS Code settings should call `hermes acp`; provider credentials remain in the remote Hermes profile (`$HERMES_HOME/.env`, OAuth stores, config) or are configured through official Hermes auth/setup flows.

## Source-of-truth checks

Before acting or finalizing, validate against current sources:

- Hermes docs for ACP/editor integration: `https://hermes-agent.nousresearch.com/docs/user-guide/features/acp`
- Hermes CLI on the target host: `hermes acp --version`, `hermes acp --check`, `hermes status` or `hermes doctor` as needed.
- Editor vendor docs for remote development and CLI behavior (for Zed: Remote Development and CLI Reference).
- Live host state: `command -v <editor>`, `<editor> --version`, `command -v uv`, SSH service/listening status, `$DISPLAY`, `$WAYLAND_DISPLAY`, `$EDITOR`, `$VISUAL`.

## Safe `$EDITOR`/`$VISUAL` setup pattern

When the requested editor is GUI-first and the target is a headless server:

1. Install the editor CLI/tooling only through its official installer/package path, user-local where possible.
2. Test the raw blocking editor command (`<editor> --wait <tmpfile>`) in a bounded way to confirm whether it works in this environment.
3. If the raw command requires a display, create a small wrapper under `~/.local/bin/` such as `zed-editor` or `gui-editor`:
   - If `DISPLAY` or `WAYLAND_DISPLAY` exists and the GUI CLI is available, exec `<editor> --wait "$@"`.
   - Otherwise, print a concise notice and exec a terminal fallback (`nano`, then `vim`, then `vi`, then `ed`).
4. Set `EDITOR` and `VISUAL` to the wrapper in shell startup files early enough for non-interactive SSH shells when needed.
5. Verify a fresh login/non-interactive shell sees the intended `EDITOR`/`VISUAL` and that the wrapper fallback exits successfully under headless conditions.

## Zed + remote Hermes pattern

Use `references/zed-remote-hermes.md` for the detailed Zed/Hermes VPS recipe.

High-level flow:

1. Install/verify Zed CLI on the remote only if the user asked for local `$EDITOR` tooling or remote server preflight; local GUI Zed remains the primary editing surface.
2. Configure `$EDITOR`/`$VISUAL` via a safe wrapper, not raw `zed --wait`, unless a GUI display exists and has been tested.
3. For file editing, connect local Zed to the remote host with Zed Remote Development over SSH and open a specific project path, not `/` or all of `$HOME`.
4. For using Hermes inside local Zed's Agent UI, verify remote ACP first:
   ```bash
   ssh <remote> /path/to/hermes --profile <profile> acp --check
   ```
5. Add a local Zed `agent_servers` custom entry that runs `ssh -T ... hermes --profile <profile> acp` only after SSH host-key/auth prompts are resolved manually.

## Herdr + remote Hermes terminal-multiplexer pattern

Use `references/herdr-remote-hermes.md` when the user wants Hermes on a VPS/headless host to communicate with a local computer through Herdr, or wants Herdr to coordinate Hermes with other terminal agents.

High-level flow:

1. Treat Herdr as the persistent terminal/orchestration substrate, not as a replacement for Hermes primitives. Hermes still owns tools, memory, skills, cron, gateway, profiles, MCP, API server, approvals, and safety policy.
2. On macOS/Linux local machines, prefer local thin-client attach to the VPS: `herdr --remote <ssh-host> --session hermes`. On Windows, native `herdr --remote` is beta-unsupported; SSH into the VPS and run `herdr --session hermes`, or use WSL2/Linux-side Herdr.
3. Install Herdr's Hermes integration only after write approval: `herdr integration install hermes`, then restart Hermes panes so the plugin loads.
4. For named Hermes profiles, validate profile support before claiming coverage: upstream Herdr currently targets `HOME/.hermes`, so profile `$HERMES_HOME` installs need an explicit profile-aware path or upstream fix.
5. Keep Hermes Desktop remote backend and Hermes gateway as separate control planes; Herdr may host/monitor their terminal processes, but clients talk to Hermes directly.

## Pitfalls

- **Remote terminal `zed file` is not the same as local Zed Remote Development.** Re-check current Zed docs before relying on remote terminal CLI forwarding. If unsupported, explain that local Zed can edit remote files via SSH remote projects, but commands inside the remote terminal should use the safe `$EDITOR` wrapper/fallback.
- **ACP stdout must remain JSON-RPC clean.** Resolve SSH host-key prompts, auth prompts, MOTD noise, and setup prompts before pointing Zed/VS Code at an SSH-launched ACP server.
- **Do not hardcode one profile unless the user asked for it.** Use `--profile <profile>` when targeting a named Hermes profile; otherwise state the active/default profile assumption.
- **Avoid opening huge remote roots.** In remote editor workflows, prefer a specific workspace/project path over `/` or a very large home directory.
- **Do not edit raw secret stores.** Use `hermes model`, `hermes auth`, `hermes acp --setup`, or approved config/env flows rather than reading or rewriting token files.

## Verification threshold

A successful setup report should include:

- Installed/available editor CLI path and version, or a clear blocker.
- Current `EDITOR`/`VISUAL` values from a fresh shell.
- Result of bounded raw GUI-command test or explanation of why it was skipped.
- `hermes acp --check` result when configuring editor-agent integration.
- SSH target/command pattern the user can run from the local computer, with placeholders for private hostnames/keys when appropriate.
