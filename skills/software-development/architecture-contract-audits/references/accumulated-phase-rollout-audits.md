# Accumulated Phase and Rollout Audit Checklist

Use this for exact-HEAD audits that span local implementation, installed plugins, privileged cutover, and recovery.

## Evidence matrix

For each phase record:

| Field | Question |
|---|---|
| Commit | What exact tracked artifact exists at the audited object? |
| Installed state | What source/consumer copy is currently installed, and does its hash match? |
| Public path | What real constructor, entrypoint, consumer, or override reaches the artifact? |
| Proof | Which test source exists, and which tests were actually executed? |
| Recovery | What happens after authority commits but sidecar finalization fails? |
| Local next artifact | What can be authored/tested entirely in the repository? |
| Approval gate | What staging, profile, privileged, restart, live-state, restore, or publication action remains blocked? |

Use `pass`, `partial`, `fail`, `blocked`, or `not started`. Historical deployment evidence can establish current state but cannot grant approval for a new generation.

## Native and override equations

Require all four inventories:

1. native callable set = ledger callables + explicit infrastructure exclusions;
2. registered native model-tool set = ledger tool registrations;
3. public protocol set = native-ledger operations + explicit broker-only operations;
4. CLI parser verb/path set = mapped broker operations + broker-only lifecycle routes + explicit non-mediated/excluded paths.

For a claimed exact override, inspect the installed plugin and selected config keys. Acceptance requires exact native names, `override=True`, trusted host override behavior, `allow_tool_override: true` where approved, deterministic broker request construction, and a real broker client. A pre-tool hook that observes terminal commands cannot establish universal mediation.

## Operability and cutover

A library `serve()` plus fixture-built runtime is not a service. Require a production runtime/config constructor, foreground executable, socket ownership and cleanup, health behavior, shutdown semantics, and at least one real consumer before service-unit work.

A free-form policy `mode` column is not shadow mode. Verify an actual shadow path that evaluates and journals would-allow/would-deny while preserving authoritative behavior. If only exact `enforce` is recognized and other values quarantine, shadow is absent.

Treat these as local artifacts until separately approved: daemon/config code, override plugin source, shadow evaluator, declarative cutover manifest, service-unit template, backup/restore tooling against temporary fixtures, and adversarial tests. Treat profile installation, override trust changes, privileged paths/UIDs, restarts, live database backup/migration, enforcement, restore, and publication as separate hard gates.

## Backup/restore acceptance

Compatibility or proposal snapshots are not deployment backup/restore. Inventory and restore all relevant surfaces:

- authoritative native databases and WAL state;
- policy, journal, approval, capability, audit, and launcher sidecars;
- broker and plugin configuration;
- service definitions and environment references without copying secrets;
- ownership, modes, ACLs, socket paths, and pinned source provenance.

Require integrity checks, an exact restore target, fail-closed service ordering, and a temporary-fixture restore drill before any live exercise.
