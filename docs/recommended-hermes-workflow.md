# Recommended Hermes Workflow

This workflow keeps Hermes work explicit, compartmentalized, and verifiable.

1. Install the `validator` personality primitive if needed, then begin each session with `/personality validator`.
2. Use `/hermes-config-audits` for configuration checks.
3. Use `/honcho-memory-provider` for memory-provider guidance.
4. Use `/first-party-integration-audits` for cross-product integration claims.
5. Validate with live tool output and source-of-truth documentation.

## Profile layout conventions

Person-specific profiles should use a `<first-name>-<role-or-use-case>`
prefix and keep workspaces under `~/hermes-profiles/<first-name>/...`.

Reusable role or use-case profiles should use a generic name and keep
workspaces under `~/hermes-profiles/<role-use-case-category-or-responsibility>`.
Only reusable profiles may be exported as public packages, only through an
explicit allowlist, and only after environment files, auth stores, memory,
sessions, logs, caches, state databases, pairing state, and runtime data are
stripped and the sanitized native distribution passes a real
`hermes profile install` into a disposable home.

## Plugin layout conventions

Plugins intended for public release should be created inside a configured
public-plugin-source profile. Public exports are allowlisted explicitly and
must be sanitized, reusable, manifest-backed, complete, and free of
credentials, runtime data, and private state; a candidate that fails any gate
leaves the existing public package unchanged.
