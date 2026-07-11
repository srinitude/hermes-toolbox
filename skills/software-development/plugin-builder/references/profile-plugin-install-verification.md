# Profile-local plugin install and verification

Use this when the user asks to install an existing Hermes plugin into a named profile, especially from a local plugin workshop/export rather than a Git URL.

## Safe target model

- A named profile's plugin home is `$HERMES_HOME/plugins/<plugin-name>/`, where `$HERMES_HOME` is usually `~/.hermes/profiles/<profile>`.
- Installing into another profile's `plugins/` tree is allowed only when the user explicitly names that target profile.
- Prefer the official CLI for enablement: `hermes -p <profile> plugins enable <plugin-name> --no-allow-tool-override` unless tool override was explicitly approved.
- Do not edit Hermes source checkout plugins or bundled repo plugins for user/profile installs.

## Local staged-copy pattern

When the plugin already exists as a reviewed local package, copy source files into a sibling staging directory, validate the stage, then atomically replace the target. Do not `rmtree()` an existing installation before a valid replacement and rollback copy exist.

Before copying:

1. Freeze an explicit user-approved consumer allowlist; do not dynamically install into every discovered profile.
2. Run the source-workshop automation preflight in `plugin-source-automation-preflight.md` so source creation does not trigger unapproved export/publication.
3. Record the previous plugin directory and `plugins.enabled` / `plugins.disabled` / `plugins.entries` state.
4. If the existing target differs, back it up with the same runtime/secret exclusions used for the install package.

Copy only source files. Exclude `__pycache__`, `.pytest_cache`, bytecode, `.git`, `.env`, auth/token stores, logs, sessions, caches, runtime databases, pairing state, backups, and checkpoints. Validate the staged manifest, syntax, bundled skill paths, and source-file hash manifest before renaming it into place. Keep the old target as a sibling rollback until enablement and fresh-process validation pass; restore it on failure.

Enable through the official CLI after the atomic replace:

```bash
hermes -p <profile> plugins enable <plugin-name> --no-allow-tool-override
```

If using `hermes plugins install <git-url-or-owner/repo> --enable`, select the target profile with the global option before the subcommand, for example `hermes -p <profile> plugins install <git-url-or-owner/repo> --enable`.

## Verification threshold

Minimum proof before reporting success:

1. Profile exists: `hermes profile show <profile>`.
2. Plugin files exist in `~/.hermes/profiles/<profile>/plugins/<plugin-name>/`, including `plugin.yaml` and the registration module.
3. Syntax/import sanity passes for plugin Python files. If using `python3 -m py_compile`, run it before the final package hygiene scan: explicit compilation creates `__pycache__`/`.pyc` even when `PYTHONDONTWRITEBYTECODE=1`, so remove those artifacts afterward or use `compile()` without writing bytecode.
4. Enablement is visible in `hermes -p <profile> plugins list --json`; parse the entry and require `status: enabled` rather than relying on human table formatting.
5. `config.yaml` contains the plugin in `plugins.enabled`, and `plugins.entries.<plugin-name>.allow_tool_override` is absent or `false` unless override was explicitly approved.
6. A fast fake-`ctx` verifier may prove handler unit behavior, but release proof requires a fresh-process real `PluginManager`/`PluginContext` discovery load. For bundled skills, assert `ctx.register_skill` receives a `pathlib.Path` to the actual `SKILL.md`.
7. If the plugin registers model tools, `hermes -p <profile> tools list` shows its custom toolset enabled. Plugin enablement alone is insufficient evidence of model visibility.
8. The target source-file hash manifest equals the reviewed source manifest after generated caches are removed.
9. The workshop/source profile remains disabled when it is source-only, and excluded profiles have no consumer copy.
10. A fresh session—or an explicitly approved long-running gateway restart—loads the final package before claiming it is live in that process.
11. Check external runtime requirements declared by the plugin README/manifest only when they are part of the plugin's normal operation.

## Pitfalls

- `hermes <plugin-cli> --help` only works for plugins that register CLI commands via `ctx.register_cli_command`; slash commands registered with `ctx.register_command` will not appear as top-level CLI subcommands.
- `hermes plugins enable` takes effect on the next session/gateway restart; report that restart/new-session requirement.
- Do not use missing optional tools such as `pytest` as a hard failure when a focused ad-hoc verifier can prove discovery/registration and runtime requirements instead.
