# Export Pipeline Plan Audit Checklist

Use this for plans that refresh a public artifact repository from dirty/private local sources.

## Evidence boundary

- Inspect pinned repository objects with `git show <rev>:<path>` and `git ls-tree`; do not read dirty worktree files as evidence of committed HEAD.
- Hash the authoritative plan before and after the audit.
- Hash newline-delimited `git status --porcelain=v1` when comparing with a supplied status digest. The `-z` form has different bytes and therefore a different digest.
- Record HEAD, pinned remote-tracking ref, status path count/kinds, and final status digest. Recheck at the end.
- If a pinned dependency contract matters, inspect the dependency's exact Git object, not its current dirty checkout or installed working tree.

## Architecture checks

Prefer five narrow layers:

1. pure common helpers for hashing, path containment, text decoding, deterministic serialization, and sanitization;
2. pure candidate/provenance policy returning structured decisions;
3. staged-package checks, with real-runtime probes isolated in subprocesses and temporary homes;
4. validate-before-mutation export transactions with explicit recovery semantics;
5. thin CLI, installer, inventory, and publication orchestration.

Reuse existing pure helpers, but do not carry forward helpers that write policy state, sweep uncontrolled directories, or enumerate arbitrary untracked files.

## Contradiction checks

### Last-known-good versus new universal gates

A plan cannot both preserve a legacy package byte-for-byte and require every retained package to pass newly introduced file-size, construct-size, no-test-double, or current-runtime gates when the legacy package already fails those gates. Require one explicit policy:

- grandfather unchanged legacy packages and apply new gates prospectively to candidate replacements; or
- migrate every legacy package and abandon byte-for-byte retention.

Distinguish `accepted-current`, `retained-last-known-good`, `rejected`, and `blocked` in reports and final manifest semantics.

### Touched-only versus whole-tree scans

If prose limits structure/style gates to created or modified files, CI must not scan the entire legacy artifact tree unless baseline violations are explicitly migrated or excluded.

### Linked worktree policy paths

In a linked Git worktree, `.git` is a file, so `<worktree>/.git/info/...` is not a valid worktree-local policy directory. `git rev-parse --git-path info` generally resolves common repository metadata, which is shared rather than isolated. Prefer an explicit external `--policy-dir` or deliberately documented common-Git storage.

### Atomic package replacement

Python's portable `os.replace()` cannot atomically replace an existing non-empty directory. Do not claim strict portable atomicity. Choose and test one of:

- recoverable backup/rename/install/rollback with crash residue reconciliation;
- versioned immutable directories plus an atomically replaced pointer;
- a platform-specific directory exchange primitive with an explicit portability constraint.

Validation failure can still guarantee zero destination mutation even when accepted replacement is only recoverable rather than strictly atomic.

### Publication path

A reviewed-PR architecture is incompatible with a publisher that commits and pushes whichever branch is checked out. Require candidate-branch creation/update plus PR creation, or make the automation stop after producing a reviewed change packet. Never leave branch choice implicit.

### NUL pathspec staging

Use one exhaustive NUL-delimited change list for accepted package roots and deterministic inventories. Stage with Git pathspec-file support; do not state both “only listed paths” and “listed paths plus inventories.”

### Self-referential manifests

A manifest cannot contain a conventional SHA-256 of itself. Define payload hashes over all package files excluding the manifest, then hash the completed manifest separately in the repository-level inventory.

### Negative fixtures and forbidden-token gates

Tests that prove detection of mocks, fakes, TODOs, placeholders, or `pass` need representations of prohibited cases. Scope payload scanners to candidate packages, not validator source or negative fixtures, and prefer semantic/AST checks over raw substring bans.

### Real manager introspection

A real manager may expose only capability counts, not exact registered names. Before promising manifest/name parity, inspect the pinned manager API. If exact names require private state, either pin that private contract in an isolated compatibility adapter, compare a real global registry in a single-plugin subprocess, or weaken the criterion explicitly.

## Withdrawal, inventory, and exact-object checks

- Treat artifact withdrawal as a first-class publish operation. An exporter that merely retains unallowlisted destinations plus a stager that skips nonexistent paths cannot remove an invalid package. Require deletion entries in the NUL change list and stage them through an exact, index-aware pathspec operation; test that package, manifest, and fingerprint removals land together.
- Derive source fingerprints from the exact intended tracked/index set, not `rglob('*')` or a tracked-plus-untracked safety-scan helper. Otherwise editor/tool metadata can leak into public inventories and newly committed files can be omitted when fingerprints were generated before the final commit.
- Verify fingerprints against committed blobs (`git ls-tree -r --name-only <rev>` plus `git show <rev>:<path>` or `git cat-file`), not the mutable worktree. Report missing keys, extra keys, and wrong hashes separately.
- Regenerate fingerprints only after every artifact, test, documentation, installer, and CI edit is final. A plan that regenerates during an artifact task and edits tracked docs in the next task is inconsistent unless it regenerates again at the end.
- Keep manifest membership distinct from validity. Including every directory with `manifest.json` and stamping `sanitized: true` can enumerate an invalid tree while falsely asserting acceptance. Require validation-derived membership or an independent exact manifest/package gate.
- If withdrawal empties an artifact class, update tutorial/package-specific validators, installer tests, README examples, and CI commands instead of retaining invalid packages to keep hard-coded tests green. Manifest-driven tests should accept an explicitly empty class.

## Publisher recovery and gate checks

- Trace failure after export. If earlier packages or inventories were mutated and there is no rollback, the next clean-start gate wedges automation. Tests must assert byte-identical clean status after exporter, validator, repository-test, commit, and push failures—not merely “no commit/no push.”
- Visibility proof must fail closed for unsupported or unrecognized remote types; returning success for every non-GitHub origin is not a visibility check.
- If publication requires an exact repository identity, test rejection of a different nonempty identity. Presence-only checks do not enforce authorship provenance.
- Confirm runtime tests are portable to CI. Pinning a package is insufficient when probe code hardcodes a developer checkout and private virtualenv layout; discover/import the pinned installed runtime through a documented contract.
- Audit installer replacement semantics. Overlay copy can retain files removed from a newer package; prefer recoverable directory replacement or exact manifest reconciliation.

## Current-candidate refresh versus publisher operability

Keep two verdicts separate:

1. **Bounded artifact refresh:** A paused publisher, clean exact base, explicit allowlists, in-memory sanitized staging preflight, transactional exporter, exact-path staging, and manual branch/PR flow may be enough to refresh currently passing artifacts without changing exporter code.
2. **Publisher operability:** Do not recommend resuming automation merely because the bounded refresh is safe. Inspect whether scan mode actually emits an exhaustive candidate matrix, rejected candidates are isolated rather than aborting accepted peers, last-known-good retention and withdrawal are first-class decisions, publication targets a review branch rather than `main`, and branch protection/rulesets enforce the claimed PR gate.

A stale local candidate report is historical evidence, not current classification. Pin its generation time, source hashes, worktree HEAD, and automation-state fields; compare them with current source hashes and actual scheduler state. Treat fields such as `publisher_resumed` as historical when current scheduler storage says paused.

For skill-only preflight without writes, reproduce export inclusion rules in memory: include `SKILL.md` plus allowed support roots, apply the real deterministic sanitizer, validate the sanitized frontmatter/body, resolve support references against the staged file map, reject binary/non-UTF-8 payloads and surviving secret patterns, and compare the staged byte map with the public destination. Label this **static staging eligibility**, not full publishability; old green CI covers only the committed public tree, not newly changed private-source bytes.

When a report says “latest passing,” verify the implementation actually supports `accepted-current`, `retained-last-known-good`, `rejected`, and `withdraw`. An exporter that aborts the whole batch on one rejected selected source, or merely reports stale destinations while retaining them, does not implement that contract even if hand-maintained reports use those labels.

## Inventory and enforcement gaps

Distinguish generator tests from committed-tree enforcement. Unit tests for an inventory writer do not prove that CI rejects a stale committed manifest or fingerprint file. Require an independent gate that reports missing keys, extra keys, and wrong hashes for manifest membership, package payload hashes, repository fingerprints, and withdrawal removals.

Inspect repository-host enforcement too:

- default-branch protection and rulesets;
- exact required check names;
- whether direct pushes remain possible;
- open PRs and active/recent runs;
- whether the publisher pushes `HEAD:main` despite docs claiming reviewed PR publication.

A documented recommendation to protect `main` is not enforcement. If `main` is unprotected and automation pushes directly to it, keep the publisher paused; use a bounded manual PR for current artifacts and require a separate TDD hardening PR before any resume decision.

## Plan command validation

Syntax-check operational commands in saved plans during a read-only audit. Catch invalid recovery or reconciliation commands, including options paired with Git subcommands that do not support them, and replace them in the implementation sequence with the exact valid command.

## Read-only discipline

Do not run validators that compile bytecode or create caches during a no-write audit. `py_compile.compile()` can create `__pycache__`; source inspection or in-memory `compile()`/`ast.parse()` is safer. Report tests present separately from tests executed, and confirm no writes with unchanged HEAD, plan hash, and status digest.

If concurrent edits appear after an initially clean freeze, stop using worktree files as exact-HEAD evidence. Re-run decisive equations from Git objects, record final staged/unstaged drift separately, and exclude the in-flight slice from the committed verdict.
