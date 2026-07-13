# Dirty schema and wheel sealing audits

Use for read-only review of an actively changing, unstaged Python candidate that claims append-only migrations, exhaustive config/wire schemas, latest-upstream compatibility, reproducible wheels, and installed-artifact proof.

## Freeze the complete dirty candidate

A tracked patch hash is insufficient when untracked files participate in the package. Record together:

- literal base/HEAD;
- `git diff --binary HEAD | sha256sum`;
- `git status --porcelain=v1 -z --untracked-files=all | sha256sum`;
- staged/index hashes and staged, unstaged, untracked counts;
- a complete manifest over the sorted union of changed tracked and untracked paths, encoding path, mode, size, bytes, symlink target, or an explicit deletion marker.

Recompute all seals at the end. If the complete manifest changes while status and tracked-diff hashes remain stable, untracked bytes drifted. Earlier wheel/test evidence does not apply. Two quick matching snapshots show only a short quiet interval, not a durable seal.

## Append-only migration proof

Compare historical migration literals against the literal base with AST/static evaluation. Separately require a repository fixture independent of the production `MIGRATIONS` collection. Tests that derive expected versions or SQL from production constants are tautological: an old migration and the collection can change together while remaining green.

The fixture should pin each accepted version's canonical statement digest. Test all of:

- historical versions remain byte/semantic identical;
- new versions are contiguous and appended only;
- explicit migration is transactional and idempotent;
- stale startup rejects before any migration path;
- legacy open rows are preserved and fail readiness rather than being guessed, deleted, or backfilled.

## Exhaustive config fixtures

Derive exact key-set equations among parser field sets, shared test fixtures, installer renderers, and service-specific renderers. Then test the equations explicitly; an audit-only AST probe is evidence, not a lasting regression gate.

For all-distinct UID/GID validation, enumerate every unordered pair. A few adjacent-role collisions do not prove the complete matrix, especially client/shared groups.

## Wire-schema parity traps

Test both acceptance and rejection parity, not a small happy-path table. High-value cases include:

- Python JSON's permissive `NaN`, `Infinity`, and `-Infinity` handling versus strict runtime finite-number checks;
- JSON Schema numeric constants/types versus Python equality: `True == 1`, so a runtime check such as `value != 1` can accept JSON `true` while `{"const": 1}` rejects it; require exact runtime type checks and explicit boolean cases for every integer/version field;
- maximum nesting, list/property counts, key/value lengths, empty strings, Unicode surrogates, and unknown fields;
- every response encoder bound: request ID, error code, error message, and non-JSON numeric results;
- outputs the encoder can emit but the published response schema rejects.

A test named “installed package namespace” is not installed-artifact proof if it imports from the checkout or can fall back to repository files. The same false green occurs when a plugin/service test copies source files or injects repository paths into `sys.path`/`PYTHONPATH`: it proves checkout behavior, not the generated archive, installed wheel, entrypoint, or packaged resources.

## Split-index package closure

For mixed staged/unstaged candidates, audit package closure twice: once against the index blob of the build metadata and once against the live worktree metadata. Parse every force-include/package-data source from each surface and require it to exist in that same snapshot. A common invalid state is an index `pyproject.toml` that still force-includes staged-deleted versioned assets while the worktree metadata points to untracked replacements; a live build may appear viable while an exact staged build cannot reproduce it. Keep staged-wheel and live-worktree conclusions separate, and do not treat a stable staged patch hash as identity for the unstaged package.

Also trace runtime-required external data such as policy registries, templates, and configuration fragments. If startup loads a configured directory but neither the wheel nor the authenticated install bundle provisions it, installed operability is incomplete unless a separate, explicit, authenticated preprovisioning contract covers that directory.

## Reproducible and installed wheel proof

Search existing artifact locations, but associate artifacts with the complete candidate digest. For each wheel:

1. hash the wheel;
2. compare all package members byte-for-byte against the immutable candidate, including force-included data/schema files;
3. report missing, unexpected, and mismatched members;
4. keep an older reproducible pair classified as evidence only for its older candidate.

For a current reproducibility claim, build twice from one immutable staged/committed snapshot with fixed `SOURCE_DATE_EPOCH` and an exact build-backend version; compare full wheel bytes. A lower-bounded build backend not represented in the lock/evidence weakens future reproducibility.

Install the exact wheel into a fresh target-interpreter environment. From outside the repository, with `PYTHONPATH` empty and isolated Python, prove metadata, console entrypoint, packaged resources, config/wire loaders without checkout fallback, and the exact pinned upstream compatibility boundary. An editable repository environment is not installed-wheel proof.

Treat gate configuration, dependency declaration, lock coverage, and executable availability as separate facts. A linter table in `pyproject.toml` does not make the linter an available reproducible gate when it is absent from declared development dependencies and the lock; likewise, a test runner does not imply security, dependency-audit, type-check, or reproducible-build gates. In a no-install preflight, report unavailable gates rather than downloading tools, and never treat stale cache directories as execution evidence.

## Latest-upstream oracle

The oracle should independently resolve first-party latest non-prerelease metadata, release version, and peeled tag commit, then compare all three with the embedded baseline. Keep the oracle inside the candidate and run it only after the candidate digest is frozen. A successful untracked script is an observation, not candidate evidence.

## Digest-associated evidence packets

A directory, log, wheel pair, or filename containing the claimed candidate digest is only an association label; it does not reproduce candidate identity. Before deep schema or wheel analysis, require the exact digest producer and run it verbatim. If the producer is absent, do not brute-force plausible manifest encodings or silently substitute an invented canonicalization. Record the independently available Git/status/index seals, classify the canonical candidate seal as unverified, and continue only when useful findings can still be tied to current bytes—for example through a byte-exact wheel/package comparison.

When a supplied full-suite log and wheel pair are keyed by one digest, keep four claims separate:

1. the log reports a source-checkout suite result;
2. the two wheels are byte-identical;
3. every wheel package member matches candidate bytes;
4. the exact wheel was installed and exercised outside the checkout.

Claims 1–3 do not imply claim 4. Look for a digest-associated fresh environment or retained proof packet, inspect `direct_url.json` when an environment exists, and reject editable installs as exact-wheel evidence. A test named “installed namespace” remains a false green when its loader has a checkout fallback or the repository is on `sys.path`.

For bounded review budgets, front-load one consolidated read-only packet: exact producer seal, migration-fixture independence, config key/collision equations, request/response adversarial parity, prohibited substitution scan, structural limits, artifact hashes, and byte-for-byte wheel manifest comparison. This surfaces invalidating evidence early and preserves enough budget for the mandatory final seal.

## Verdict discipline

Invalidate the candidate when any of these holds:

- candidate bytes drifted after evidence was produced;
- historical migrations lack an independent append-only fixture;
- config/collision or wire-schema fixtures are non-exhaustive;
- no wheel is byte-exact to the current candidate;
- reproducible builds or installed proof belong to an older digest;
- the compatibility oracle is absent from the candidate.

Report tests present separately from tests executed, and do not run builds, installs, migrations, or suites when the user requested a strict read-only/no-side-effect audit.
