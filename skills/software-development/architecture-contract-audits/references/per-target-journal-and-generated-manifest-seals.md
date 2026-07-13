# Per-target journal and generated-manifest release seals

Use this reference for read-only acceptance of retained rollback journals and generated release inventories.

## Exact retained-journal schema

A digest check after coercing mapping keys is not an exact schema check. JSON keys such as `"0"`, `"00"`, `"+0"`, and `"-0"` can collapse to the same integer; duplicate raw object members can also disappear during ordinary `json.loads`. If restoration depends on the mapping, validate the raw representation before any normalization:

1. Parse objects with an `object_pairs_hook` that rejects duplicate members at every relevant level.
2. Require `targets` to be the exact ordered list expected for the retry.
3. Require `seals` to be an object whose raw key set equals `{str(i) for i in range(len(targets))}`.
4. Require every key to use canonical decimal spelling (`key == str(int(key))`) and every value to match the closed seal grammar: the explicit absent sentinel or a lowercase SHA-256 digest.
5. Only after those checks may code convert keys to integers.
6. Verify every present snapshot byte/tree against its digest and require every absent seal to have no snapshot path.
7. Complete all validation before invoking restoration or deleting any live target.

A useful disposable-fixture matrix retains a failed rollback with one present destination, one absent destination, and all implicit targets such as inventories/change lists. Preserve recognizably mutated live bytes, then probe:

- valid complete retry restores exact old bytes and removes newly created absent targets;
- missing canonical key;
- non-colliding extra key;
- wrong digest/value type;
- absent seal with a snapshot present;
- extra canonical-alias key such as `"00"` beside `"0"`;
- canonical key removed and replaced by an alias;
- duplicate raw JSON member.

Make duplicate-member probes maximally diagnostic. Exercise both levels independently:

- repeat one top-level member (prefer `targets`) with the same valid value;
- repeat the same canonical seal key with the same valid digest, leaving every other seal and target valid.

An ordinary `json.loads` will collapse either form to an apparently complete valid object, so recovery may consume the snapshot. Before cleanup, record the raw member count as two, whether entry rejected, whether restoration was invoked, and whether visible bytes changed. This distinguishes real raw-schema enforcement from a later completeness check that happens to reject a conflicting final value.

For every rejection case, prove pre-restoration rejection with three independent assertions: the restoration method call count is zero (an instance-level wrapping mock is sufficient), every live target's byte/absence state is unchanged, and the complete retained-backup tree—including journal and snapshots—is byte-identical before and after entry. Merely raising an exception or checking one destination is insufficient; a rejected journal must remain wholly unconsumed for repair or retry.

## Absent-target completeness

Derive the target universe from the production constructor, not only explicit destinations. Include automatically appended inventories, manifests, change lists, or auxiliary outputs. Require exactly one seal per final target index, including targets absent at snapshot time. Record which absent indices have no snapshot paths and exercise retained-journal recovery, not only the ordinary in-process rollback path.

## Generated inventory freshness

A green validator suite does not prove checked-in generated inventories describe the candidate. Independently reconstruct the expected map from the exact staged index and the production generator's inclusion/exclusion rules:

1. Export or reproduce the staged candidate outside the repository and prove its patch digest/path count equals the frozen candidate.
2. Invoke generator functions in memory; do not call the writer.
3. Compute expected `(path, SHA-256)` entries from the staged index plus any manifest-listed package roots.
4. Compare expected and checked-in maps exactly; report expected/actual counts and missing, extra, and mismatched counts.
5. Canonically serialize the expected map with the production JSON formatting and report both checked-in and expected file digests.

A `git checkout-index` snapshot has no `.git` directory. If the production generator falls back to a filesystem walk outside a worktree, that fallback may omit hidden-but-tracked paths such as `.github/**`, `.gitattributes`, or `.gitignore`; do not mistake that fallback result for the staged-index universe. Derive tracked entries directly from the frozen index/blob map and add manifest-root extras explicitly, or initialize a fully disposable Git repository only when reproducing Git-backed generator behavior is itself required. State which equation was used. When the exact snapshot contains only index entries and the fingerprint file excludes itself, report the transparent count equation (`snapshot entries - excluded generated files = expected fingerprints`) alongside byte mismatches.

Treat a stale generated fingerprint map as a release-integrity blocker even when public package manifests, runtime samples, and structural validators pass. Generated metadata must be part of the candidate generation that it claims to seal.

## Compact no-write verdict

For a staged candidate, a practical no-object-write freeze is to copy `.git/index` into a disposable directory, make the copy read-only, and use `GIT_INDEX_FILE=<copy>` for both the digest reproduction and `git checkout-index`. Require the copied-index digest to equal the initial live-index digest before testing. This binds the snapshot to one immutable index even if the live index changes between commands, without invoking `git write-tree`.

Run focused Python probes with `PYTHONDONTWRITEBYTECODE=1`, direct all homes/repos/build products to disposable paths, and delete those paths before the final seal. Recompute the live producer digest, status counts, index hash/stat, blob-manifest hash, and ignored-artifact manifest after cleanup—not only before it.

For exact-byte acceptance, report only blockers and compact positive evidence. Include the literal HEAD, named digest producer, digest, staged path count, zero unstaged/untracked counts, index blob-manifest hash, index-file hash/stat stability, ignored-artifact count/hash stability, exact snapshot-to-index entry count, and deletion of disposable fixtures. Keep broader supplied suites distinct from independently rerun focused probes.
