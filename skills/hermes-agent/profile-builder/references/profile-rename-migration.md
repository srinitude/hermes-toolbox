# Profile Rename Migration Reference

Use this when renaming an existing Hermes profile or propagating a profile name change across active surfaces.

## Core pattern

1. Treat `hermes profile rename <old> <new>` as the first-party operation for the profile home, wrapper alias lifecycle, active-profile pointer, gateway stop, and Honcho host-key migration.
2. Before rename, preflight live state:
   - `hermes profile list`
   - `hermes profile show <old>`
   - `hermes profile show <new> || true`
   - process scan for `hermes -p <old>` / `-p <old>`; do not rename while an old-profile TUI/gateway/chat process is active unless the user explicitly approves termination.
   - `hermes -p <old> gateway status || true`
   - `hermes -p <old> cron list || true`
3. Create rollback artifacts before mutation:
   - `hermes profile export <old> -o ~/.hermes/exports/<old>-pre-rename-<ts>.tar.gz`
   - copy any custom wrapper from `~/.local/bin/<old>` if it contains custom `cd` or environment setup.
4. Run the official rename:
   - `hermes profile rename <old> <new>`
5. Propagate non-automatic active surfaces:
   - operational workspace directory (e.g. `~/old` → `~/new`)
   - `terminal.cwd` via `hermes -p <new> config set terminal.cwd <new-workspace>`
   - custom wrapper behavior (`cd <new-workspace>; exec hermes -p <new> "$@"`)
   - profile-local personal skill paths/frontmatter/references
   - built-in memory facts and user profile facts
   - Honcho current peer cards/conclusions when they contain the old profile name or workspace path

## Cross-profile write guard

When operating from the default profile on a deliberately targeted named profile, Hermes file tools may block edits under `~/.hermes/profiles/<new>/skills`, `plugins`, `cron`, or `memories` with the cross-profile guard. If the user explicitly requested this migration and the saved plan names the target profile, retry targeted file edits with `cross_profile: true`; do not use it for adjacent profiles or unstated surfaces.

## Honcho validation nuance

- The official rename migrates Honcho host keys such as `hermes_<old>` / `hermes.<old>` to the new host key.
- Preserve strict-isolation data identities (workspace/user peer/AI peer) unless the user explicitly asks for a data-identity migration; changing them can strand or duplicate memories.
- `hermes honcho --target-profile <profile> status` may resolve a session key from the current cwd. If updating a target-profile peer card directly, update the relevant session key(s) observed in status, and validate from the intended cwd.
- Never print or rewrite raw `apiKey` values; validation scripts should print only host key, workspace, peer names, and masked CLI output.

## Validation threshold

A rename is complete only when:

- `hermes profile show <new>` succeeds and `hermes profile show <old>` fails.
- `~/.hermes/profiles/<new>` exists and `~/.hermes/profiles/<old>` does not.
- The new wrapper is executable, invokes `hermes -p <new>`, and preserves any required `cd <new-workspace>` behavior.
- `terminal.cwd` equals the renamed workspace path.
- The old workspace path is absent unless the user explicitly approved a compatibility symlink.
- Active safe surfaces contain no standalone old profile name, excluding histories, sessions, logs, caches, state DBs, prior plans, and generated snapshots.
- `doctor`, `config check`, `tools list`, `skills list`, `prompt-size --json`, and smoke chats pass or blockers are reported.

## Smoke tests

```bash
hermes -p <new> chat -Q -q "Reply with exactly: OK — <new>"
cd /tmp && ~/.local/bin/<new> chat -t terminal -q "Use the terminal tool to run pwd. Reply with only the path returned by the terminal tool."
```

If a non-quiet smoke chat prints the expected answer but exits with a post-output abort, retry quiet mode and report the first abort as a blocker only if the retry also fails.
