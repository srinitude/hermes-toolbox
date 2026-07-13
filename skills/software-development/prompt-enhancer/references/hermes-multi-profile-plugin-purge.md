# Multi-Profile Hermes Plugin Purge

Use this procedure when a user asks to remove a Hermes plugin completely from one or more live profiles. It covers installed code, registration, runtime state, scheduled maintenance, and automatic reinstall paths without deleting repository/archive sources unless separately approved.

## Scope gate

Before cross-profile deletion, inventory read-only and distinguish:

1. **Live profile installation** — `$HERMES_HOME/plugins/<plugin>/`.
2. **Live registration** — `plugins.enabled`, `plugins.disabled`, and `plugins.entries.<plugin>` in each profile config.
3. **Operational state** — profile-private directories, plugin-specific virtualenvs, refresh scripts, cron jobs, services, or timers.
4. **Automatic reinstall policy** — profile-builder/plugin-builder skill clauses, bootstrap lists, templates, or scripts that copy/enable the plugin.
5. **Source/archive copies** — toolbox repos, readable backups, exports, and development worktrees.

If “entirely” discovers multiple live profiles or source/archive copies, ask the user to choose the boundary before crossing profile/repository scopes. Treat an explicit all-profile choice as approval for those live profile homes, not automatically for repositories, backups, or published packages.

## Safe execution sequence

1. Load the `hermes-agent` operating guidance and validate current plugin commands against live `hermes plugins --help` and official docs.
2. Preflight active processes, gateway/cron state, source and target paths, and idempotence. Do not restart a gateway or terminate a profile process when its cgroup/process tree contains unrelated work without explicit approval.
3. Create a temporary rollback archive containing only affected live files when practical. Keep it outside active Hermes homes and delete it after validation so a requested purge does not leave a hidden plugin copy.
4. Run the profile-scoped official uninstall first:
   - default: `hermes plugins remove <plugin>`
   - named: `hermes -p <profile> plugins remove <plugin>`
5. Verify the plugin directory is absent. Do not assume uninstall cleaned config.
6. Remove exact stale config values from:
   - `plugins.enabled`
   - `plugins.disabled`
   - `plugins.entries.<plugin>`
7. Remove plugin-specific cron jobs through `hermes -p <profile> cron list --all` followed by `cron remove <id>`. Never infer or guess job IDs.
8. Remove exact live operational state only after path guards: plugin-private directories, plugin-specific venvs, refresh scripts, services, and timers. Avoid credential inspection; delete the approved state path without printing secret contents.
9. Remove automatic reinstall/bootstrap clauses from every live copy of the governing user-authored skill. Preserve adjacent sections, frontmatter, numbering, code fences, and unrelated plugin policies. Remove now-unused plugin-specific support files only when source-authoring material is also in scope.
10. Leave source repos, readable backups, exports, cron history, and published packages untouched unless the user separately selected those surfaces.

## Config-cleanup pitfall

Current `hermes plugins remove` may delete only the plugin directory and leave allow-list/entry keys behind. Also, `hermes config set` is scalar-oriented: passing JSON-looking list/map text can produce quoted YAML strings such as `'["plugin"]'` or `'{}'`, disabling unrelated plugins or corrupting expected types.

For list/map cleanup:

- Prefer a first-party unset/list-aware command when one exists.
- Otherwise use a focused, atomic YAML mutation that parses the existing mapping, removes only the exact plugin values/entry, preserves unrelated keys, reparses the rendered YAML, and keeps file permissions.
- Immediately verify raw YAML types and run `hermes plugins list`; repair unrelated enablement before continuing.

## Validation threshold

The purge is complete only when all selected live profiles pass:

1. Plugin and plugin-private paths are absent.
2. Config parses and contains no plugin registration.
3. `hermes [ -p <profile> ] plugins list --plain --no-bundled` contains no plugin.
4. A fresh-process `PluginManager`/registry probe finds neither the plugin nor its tool names.
5. Plugin-specific cron/service/timer registrations and refresh scripts are absent.
6. Governing profile-builder/bootstrap skills contain no reinstall rule, retain valid frontmatter, and have balanced Markdown fences.
7. No plugin process remains.
8. Temporary rollback/verifier artifacts are deleted.

A running conversation retains its original tool schema for prompt-cache stability. After disk/config validation, tell the user to start a fresh session or run `/reset`; do not claim the tools disappeared from the already-running session.

## Gateway restart decision

Restart only when the gateway actually loaded the plugin and the restart is safe. Check startup time, plugin installation timing, logs, and current processes. If the gateway predates the installation and has no plugin load evidence, a restart may be unnecessary. If its cgroup contains unrelated in-flight work, preserve that work and report the fresh-session requirement instead of restarting blindly.
