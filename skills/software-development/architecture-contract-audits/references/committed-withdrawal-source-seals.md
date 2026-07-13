# Committed Withdrawal and Protected-Source Seals

Use this for a strict read-only final seal after a public-package withdrawal has already been committed, while the authoritative local source remains outside the repository.

## Evidence packet

Freeze and recheck these independently:

1. literal commit, single parent/base, branch, tree, clean status, and absent index lock;
2. exact producer digest, normally `git diff <literal-base> <literal-commit> | sha256sum`, plus changed-path and A/D/M counts;
3. live remote base with `git ls-remote` (do not rely only on the local remote-tracking ref);
4. protected source `tree_sha` at the start and end, latest source-file mtime, and quiet-window duration;
5. publisher scheduler state from its static job record and active exporter/publisher process absence;
6. exact public inventory/package-root equations and byte-level manifest/fingerprint verification.

A missing remote topic branch is expected for a pre-publication seal; report it separately from base equality rather than treating it as a blocker.

## Fresh projection without writes

Reproduce sanitizer defects in memory with the production inclusion predicate and sanitizer:

- use an intentionally nonexistent repository path so `.git/info` denylist files are absent;
- preserve the real private-prefix and public-plugin-profile arguments;
- derive author metadata exactly as the exporter does;
- include only files accepted by the production skill inclusion predicate;
- count the exact malformed output and record package-relative locations.

Do not infer a delimiter defect merely from repeated sanitized tokens. Require the exact malformed delimiter shape and inspect the projected line directly; token count alone is not a correctness oracle.

Also inspect the existing public package at the literal base commit. Fresh-source projection failure and base-package failure can have different malformed placeholders while supporting the same withdrawal disposition.

## Static committed-tree equations

For the literal commit, prove:

- tracked skill roots equal manifest skill roots;
- tracked plugin/profile/personality roots equal corresponding manifest roots;
- every approved withdrawal root is absent;
- every manifest digest equals the referenced committed blob bytes;
- the source-fingerprint key set equals all tracked paths except the fingerprint file itself;
- every fingerprint digest equals committed blob bytes.

Use `git show <literal-commit>:<path>` and `git ls-tree` so the proof does not depend on the live worktree.

## Byte and scope quality checks

For the exact commit range, additionally prove:

- every deletion is confined to an explicitly approved withdrawal root, and every required root includes its deleted `SKILL.md`;
- every surviving changed path belongs to the exact allowed documentation, inventory, policy, test, or retained-package surface;
- retained package-local references resolve and discovery/dependency metadata does not advertise withdrawn skills;
- changed text blobs are UTF-8, LF-only, final-newline terminated, non-symlink files with no unexpected mode changes;
- named support modules remain byte-identical when the change is supposed to update only callers/tests;
- added lines contain no high-confidence credential assignments, shell/SQL injection patterns, unsafe evaluation/deserialization, private home paths, or non-example email identities.

Residual withdrawn names in historical or optional prose are not automatically dependency failures. Classify each occurrence as discovery metadata, executable instruction, mandatory dependency, or non-operative context.

## Canonical source hashing

Use the repository's actual `tree_sha` implementation rather than a hand-written approximation. Relative-path ordering, separators, whether file bytes are pre-hashed, and the trailing NUL after each file all affect the digest. Verify both volatile source trees in one bounded start packet and again in one end packet; any mismatch blocks the seal.

## Test reporting and strict no-write tooling

Under a strict no-write boundary, do not rerun suites that create temporary homes, caches, installs, or runtime records. Label prior postcommit suites as supplied evidence. Independently run only static/in-memory equations that cannot mutate the repository or protected source. Set `PYTHONDONTWRITEBYTECODE=1` for Python validators.

Avoid broad `session_search` during a strict no-write seal: large responses may automatically spool under `/tmp/hermes-results/`. Prefer the named source artifacts and exact commit objects. If a managed tool creates a cache/spool anyway, disclose its exact path and whether it remains; report it separately from repository or protected-source mutation, and do not silently delete it when deletion is outside scope.

## Final response

Lead with `PASS` or `BLOCK`. Report exact commit/base/diff digest/path count, scope equations, start/end source hashes and quiet window, live remote equality, publisher paused/process state, whether tests were supplied or rerun, and repository/protected-source modification status.
