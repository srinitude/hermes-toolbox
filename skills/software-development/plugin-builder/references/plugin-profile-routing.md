# Plugin Profile Routing Convention

Use this reference when a `/plugin-builder` workflow must choose the configured Hermes workshop profile that owns a generated plugin.

## Routing rule

Each generated plugin belongs to exactly one configured plugin workshop profile:

| Plugin scope | Owning profile role | Workspace rule | Naming rule | Downstream consumers |
| --- | --- | --- | --- | --- |
| User-specific or private | Deployment-configured private plugin workshop | Use that profile's configured workspace and `terminal.cwd` | Apply the deployment's configured private prefix when one exists | Private consumer profiles may use explicitly approved private or reusable plugins |
| Reusable or public | Deployment-configured public plugin source workshop | Use that profile's configured workspace and `terminal.cwd` | Keep names and documentation identity-neutral | Public/reusable profiles may use only reusable plugins |

## Builder workflow impact

1. During intake, classify the plugin as user-specific/private or reusable/public before proposing a target path.
2. If classification is ambiguous and affects privacy, publication, or routing, ask the user before writing files.
3. Create and edit generated plugin files under the selected profile's `$HERMES_HOME/plugins/<plugin-name>/` by running Hermes with that configured profile.
4. Apply a private naming prefix only when the deployment has explicitly configured one.
5. For reusable plugins, keep tracked docs and examples generic: `$HERMES_HOME`, `$HOME`, `example.com`, and role-based profile language; no private paths, profile names, secrets, logs, caches, runtime data, or personal context.
6. Downstream profile inclusion is a later approval step. Treat generated plugins as candidates, not automatic dependencies for other profiles.

## Validation checklist

- `hermes profile list` shows the selected owning profile.
- `hermes -p "$PROFILE" config show` or an approved config audit confirms the expected `terminal.cwd`.
- The plugin final agreement lists the owning profile role, target plugin path, privacy class, naming-rule result, and downstream-consumer rule.
- No files were written under another profile's `plugins/` tree.
