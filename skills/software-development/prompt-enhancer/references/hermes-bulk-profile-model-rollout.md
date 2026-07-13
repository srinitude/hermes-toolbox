# Bulk Hermes Profile Model Rollout

Use this workflow when a user asks to change the model/provider across every Hermes profile. Treat it as a scoped configuration rollout, not a broad search-and-replace.

## Scope

By default, update each profile's top-level `model.provider` and `model.default`. Also inspect active profile configuration for explicit runtime-routing fields (for example, a plugin-specific `runtime_model`) and cron `jobs.json` model pins that still name the superseded model. Do not alter auxiliary, fallback, delegation, distribution-source, plugin-source, documentation, session, log, cache, or historical values unless the user's wording includes them or they are clearly active runtime overrides.

## Preflight

1. Validate current syntax against first-party profile, configuration, and provider docs plus live CLI help.
2. Inventory profiles with `hermes profile list`; do not infer the set from memory or directory names alone.
3. Record gateway state, cron state, and Hermes-related processes. Check whether a running gateway owns in-flight terminal, backup, Git, or other child work that a restart would kill.
4. Read only the selected non-secret model keys from each `config.yaml`; never inspect `.env` or raw auth stores.
5. Confirm provider credential metadata with `hermes [-p <profile>] auth list <provider>` without printing tokens.
6. Establish idempotence: identify profiles already at the requested pair and skip unnecessary writes.

## Rollback Before Mutation

Create a mode-`0600` archive containing every pre-existing profile `config.yaml`, plus a manifest with its SHA-256. The manifest must explicitly list profiles whose `config.yaml` did not exist before mutation: a file archive cannot represent an absent-file pre-state, so exact rollback requires extracting the archive and removing those newly created files.

Keep rollback artifacts outside profile runtime stores unless using an official Hermes snapshot/backup command. A temporary `/tmp/hermes-model-rollback-*` artifact is suitable for a short-lived scoped rollout when its ephemeral nature is reported.

## Apply Through the Official CLI

For each discovered profile, use the profile-aware CLI rather than direct YAML edits:

```bash
hermes -p <profile> config set model.provider <provider>
hermes -p <profile> config set model.default <model>
```

For the active default profile, use an explicitly verified default-profile invocation. If the profile previously had no config, the CLI may create a minimal valid `config.yaml`; do not automatically run a broad config migration unless requested.

Update any confirmed active profile-specific runtime override through its exact config key, for example:

```bash
hermes -p <profile> config set <plugin_section>.runtime_model <provider>/<model>
```

Avoid raw global substitutions because they can mutate examples, fallbacks, historical state, or distribution metadata.

## Validation

The rollout is complete only when all of the following pass:

1. `hermes profile list` shows the requested model for every profile.
2. `hermes profile show <profile>` reports the requested `model (provider)` pair for every profile; this is the preferred live CLI/runtime view.
3. Selected-key parsing confirms the exact top-level provider/model pair in every config.
4. `hermes [-p <profile>] config check` exits successfully for every profile. Report non-fatal migration notices instead of silently broadening scope.
5. Provider credential metadata exists for every profile.
6. A focused residual scan finds no superseded model in active profile `config.yaml` files or cron `jobs.json` definitions. Investigate each hit before changing it.
7. Rollback archive permissions, checksum, entry count, and manifest validity are verified.

Do not make a paid model call merely to test configuration unless the user authorized that cost. CLI runtime resolution plus auth metadata is normally sufficient for this class of change.

## Restart Discipline

Config changes apply to new sessions; already-open chats retain the model they started with. A running gateway may require restart for process-level config changes, but never restart blindly:

- If the changed gateway is stopped, no restart is needed.
- If a running gateway's persisted config was already compliant, avoid needless disruption.
- If restart is required but the gateway owns in-flight child work, defer the restart or ask for a safe window rather than killing the work. Report the persisted configuration as complete and the runtime restart as pending.
- Re-check gateway and cron health after any restart.

## Required Final Report

Report the profile count and pass count, exact provider/model, any explicit runtime override updated, config-check warnings, gateway/restart decision, rollback paths and checksum, and confirmation that secrets and Hermes source/runtime stores were not modified.
