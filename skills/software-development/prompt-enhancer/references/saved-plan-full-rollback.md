# Full rollback of long saved-plan execution

Use this when a user asks to undo a multi-phase plan or an entire execution session.

## Scope before destruction

1. Anchor current time live and inspect current services, processes, task state, and the authoritative plan.
2. Immediately reverse only an unambiguous active exposure or stale mapping when its exact rollback is already approved and independently safe.
3. If “this” could mean one feature, one phase, or the whole session, ask for scope before deleting files.
4. For whole-session rollback, build a reviewed manifest before mutation. Classify each item as exact reversible state, targeted removable artifact, unrelated state to preserve, irreversible loss, or user-local residue.
5. Treat restoration of a security- or privacy-reducing prestate as an explicit consequence. Restoring `pane_history=true`, for example, is not an innocuous config rollback.

## Inventory and attribution

Prefer exact prestate evidence in this order: first-party status/config commands; rollback manifests and byte-for-byte backups; hashes plus readable changed-path inventories; session history only as secondary evidence.

Do not overwrite a shared file from an old backup when a targeted inverse is possible. Remove only the exact plan-created SSH host line, config key, Serve handler, cron entry, or registry hunk so concurrent user changes survive.

Preserve source artifacts that predated execution. Restore a canonical plan to its execution-start hash rather than deleting it unless the user explicitly asks to delete the plan itself.

## Runtime safety

- Before deleting a named Herdr session, use official session/agent commands to prove the current agent is not running there. Keep the default or other pre-existing session.
- Remove Tailscale Serve with the exact port/path command, then prove old handlers and unrelated listeners are unchanged.
- Before removing a staged SSH identity, prove whether its public key reached the remote host. If not installed, VPS-only cleanup is sufficient; if installed, include remote authorized-key removal.
- Use official config commands where possible. If an official editor is the only supported removal path, invoke it with a tiny validated noninteractive editor that performs exact-count replacements rather than reserializing the whole config.

## Cleanup discipline

Delete temporary artifacts with an explicit allowlist. Never use a broad `/tmp/hermes-verify-*` wildcard when unrelated verifier artifacts coexist. Remove rollback inventory files last, after validation.

Cancel or reset active task state only after filesystem, config, and live-service rollback passes.

## Objective validation

Require all applicable checks:

- live service configuration equals the original normalized state;
- restored files match prestate hashes;
- plan-created workspaces, sessions, keys, listeners, and temp artifacts are absent;
- unrelated handlers, listeners, cron jobs, repos, profiles, and verifier artifacts remain;
- official config validation passes;
- persistent memory removes only plan-derived entries;
- irreversible history deletion, shared logs/transcripts, and browser/download residue are reported honestly.

Never claim a complete byte-for-byte rollback when deleted contents were not backed up or local-browser residue is outside the available control surface.
