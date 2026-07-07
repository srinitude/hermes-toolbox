# Plugin Profile Routing Convention

Use this reference when a `/plugin-builder` workflow is deciding where a generated Hermes plugin should live on the local Hermes environment.

## Routing rule

Plugins created through `/plugin-builder` belong to exactly one plugin workshop profile:

| Plugin scope | Owning profile | Workspace / `terminal.cwd` | Naming rule | Downstream consumers |
| --- | --- | --- | --- | --- |
| user-specific/private | `<first-name>-plugins` | `~/hermes-profiles/<private-term>/<first-name>-plugins` | Plugin name must start with `<first-name>-` | user-specific profiles may later draw from both `<first-name>-plugins` and `non-<first-name>-plugins` |
| Reusable/non-user-specific | `non-<first-name>-plugins` | `~/hermes-profiles/non-<first-name>-plugins` | Avoid `<first-name>-` prefix; keep docs/examples identity-neutral | Non-user-specific profiles may draw only from `non-<first-name>-plugins`, never from `<first-name>-plugins` |

## Builder workflow impact

1. During plugin intake, classify the plugin as user-specific or reusable/non-user-specific before proposing a target path.
2. If classification is ambiguous and affects privacy/publication/routing, ask the user before writing files.
3. Prefer creating/editing generated plugin files under the owning profile's `$HERMES_HOME/plugins/<plugin-name>/` by running Hermes with `-p <first-name>-plugins` or `-p non-<first-name>-plugins` as appropriate.
4. If a user-specific plugin name lacks the `<first-name>-` prefix, rename it in the final agreement before creation.
5. For reusable plugins, keep tracked docs/examples generic: placeholders such as `<user>`, `<profile>`, `$HERMES_HOME`, `$HOME`, `example.com`; no private paths, profile names, secrets, logs, cache, runtime data, or personal context.
6. Downstream profile inclusion is a later approval step. Treat generated plugins as candidates, not automatic dependencies for other profiles.

## Validation checklist

- `hermes profile list` shows the owning plugin profile.
- `hermes -p <owning-profile> config show` or direct config inspection confirms the expected `terminal.cwd`.
- The plugin final agreement lists the owning profile, target plugin path, privacy class, naming rule result, and downstream-consumer rule.
- No files were written under the wrong profile's `plugins/` tree.
