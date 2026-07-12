# Public Hermes Primitive Candidate Classification

Use this reference for read-only publication-readiness audits covering standalone plugins, native profile distributions, and custom personality primitives.

## Decision vocabulary

Apply status precedence consistently:

1. **accepted** — every applicable source, package, sanitization, runtime, and approval gate passes.
2. **rejected** — at least one hard technical or safety gate fails. Rejection takes precedence over a simultaneously missing allowlist approval.
3. **approval-required** — every technical/safety gate passes and the only remaining blocker is explicit allowlisting or human publication approval.

Do not label a technically broken candidate `approval-required` merely because its allowlist is empty.

## Inventory boundary

- Plugins: enumerate manifests only from the configured reusable/public plugin-source profile; record exact source root and require `kind: standalone` when that is the requested class.
- Profiles: enumerate profile roots containing `distribution.yaml`; do not treat ordinary runtime profiles as distributions.
- Personalities: enumerate local custom `agent.personalities` values, then distinguish custom overlays from first-party built-ins. Built-in duplicates are not distinct toolbox candidates.
- Read untracked local allowlists and deny terms as policy evidence, but never publish those private policy files.
- Treat historical candidate reports as evidence, not current authority. Recompute static findings against live source and call out report/source drift.

## Static plugin audit

For each candidate, report:

- manifest identity, kind, required env, declared tools/hooks/commands/CLI commands/skills;
- required source skeleton (`README.md`, `plugin.yaml`, `__init__.py`);
- presence of `tests/test_*.py`;
- TODO/FIXME, placeholder body, test-double, skip/xfail findings;
- 200-line file, 30-line construct, and depth-3 nesting findings;
- bundled skill path existence;
- symlinks, binary/non-UTF-8 files, generated caches, runtime/private paths, and credential-like assignments;
- runtime/external dependencies derived from manifests, README, and actual call sites.

A public `manifest.json` may be exporter-generated; do not misclassify its absence in protected source as a source-package defect when the exporter contract creates it.

Generated `__pycache__`/`.pyc` files are hygiene findings, not blockers when the exporter demonstrably excludes them. Symlinks and non-excluded binary files remain blockers.

## Logical profile staging audit

Evaluate the package the exporter would create, not the entire live profile home:

1. Parse `distribution.yaml` and validate `distribution_owned` paths.
2. Model the exporter’s reusable config allowlist and generated files.
3. Scan only logically included files for binaries, absolute local paths, TODOs, test doubles, skips, and identity/private data.
4. Separately verify the full source root has no symlink, because source safety may reject before file selection.
5. Record dependency closure: model/provider auth, MCP servers, enabled plugins, required CLIs, external services, and cooperating profiles.
6. Detect manifest/config drift, such as `env_requires` describing a provider different from the configured runtime route.

A profile can satisfy Hermes’s minimal native manifest parser while still failing the toolbox’s stricter reusable-package contract.

## Personality audit

- Compare the candidate prompt value byte-for-byte with the live custom overlay when a public package already exists.
- Verify the package manifest declares `type: personality`, `sanitized: true`, a contained config file, and all required excluded categories.
- Reject local entries that merely duplicate current first-party built-ins as non-distinct candidates.
- Require disposable installation/config merge and fresh-session `/personality <name>` activation before claiming runtime acceptance.

## Real validation requirements

Static success is not runtime success. After technical remediation and approval:

### Plugins

Use a disposable Hermes home and the real `PluginManager` in separate disabled and enabled processes. Prove:

- disabled baseline registers nothing;
- enabled discovery succeeds;
- declared/registered tools, slash commands, and bundled skills match;
- handlers return valid JSON for success and bad input;
- hooks, CLI commands, toolset visibility, and external-service behavior are exercised separately because a basic parity helper may not cover them.

Use real external services/binaries where the plugin contract depends on them. Missing credentials or paid-call approval is a blocker, not permission to substitute a fake.

### Profiles

Install the sanitized package with real `hermes profile install` into a disposable Hermes home, then run profile info, config check, and enabled-only skill discovery. Exercise the profile’s actual collaboration/dependency flow, not only installation.

### Atomic suites

If repository validation defines an all-or-nothing suite, classify every member individually but also report the suite-level dependency. A technically repaired member is still not publishable while a required companion profile/package is absent.

## Reporting shape

Return:

1. counts by class and status;
2. exact source and policy gates;
3. a per-candidate or explicitly enumerated grouped matrix;
4. package completeness findings with compact category counts;
5. runtime/external dependencies;
6. sanitization blockers versus deterministic rewrites;
7. exact real-install/probe requirements;
8. current repository validation and clean-worktree evidence;
9. an explicit statement that no writes/imports/installs/external calls were performed when the audit was constrained to read-only.
