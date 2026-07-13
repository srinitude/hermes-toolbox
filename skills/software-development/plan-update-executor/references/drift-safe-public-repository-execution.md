# Drift-Safe Public Repository Plan Execution

Use this reference when a long-running saved plan publishes sanitized artifacts from mutable local sources into a public repository.

## Candidate and source drift

- Hash each candidate package tree, not only its main manifest file. Exclude known runtime caches deterministically.
- Record classification evidence in local-only Git metadata (`git rev-parse --git-path info`), never in tracked public files when rejected names or private reasons may leak.
- Recheck candidate hashes immediately before export and again before commit. If an accepted candidate changes, reclassify and re-export that candidate; if a rejected candidate changes, reclassify it and update only the local report.
- Keep the original failed/dirty checkout byte-for-byte preserved before cleanup. Work from a clean branch/worktree based on current remote main.
- A report helper must be called with the exact root/relative-path contract it expects. Validate the report itself against the tracked manifest before relying on its counts.

## Transaction boundaries

Per-package atomic replacement is insufficient for a multi-candidate batch. Candidate A can succeed before candidate B fails.

Wrap all selected destinations and deterministic inventories in a whole-batch transaction:

1. Snapshot existing selected destinations and inventory files.
2. Export candidates using per-package staging.
3. Regenerate inventories.
4. Run safety, identity, completeness, optional-suite, and real-runtime gates inside the batch boundary.
5. Write the NUL-delimited accepted change list only after every gate passes.
6. On any exception, restore snapshots byte-for-byte, remove newly created destinations, remove staging/last-known-good residue, and emit no change list.

Test candidate-one-success/candidate-two-failure, newly created destinations, late validator failure, complete tree restoration, and absence of transaction residue or change-list output.

## Symlinks and fingerprints

- Reject candidate source symlinks before staging. Include nested symlink files/directories; treat ancestor symlinks and scan/copy TOCTOU as residual local-host risks.
- Do not fingerprint `repo.rglob('*')`: it can ingest editor/MCP caches and unrelated untracked files.
- Fingerprint exactly existing tracked files plus newly exported files beneath manifest-listed package roots. Exclude the fingerprint file itself and private/runtime/cache paths.
- In non-Git fixture repositories, use a visible-file safe-walk fallback and test it explicitly.

## Privacy review

Machine scans need a local identity denylist containing private names in every relevant case/spelling. The exporter should deterministically replace denylisted terms in public copies, while the validator rejects any residue.

Before push, run an independent read-only adversarial review of the full diff. Require exact file/line evidence for privacy leaks, path/symlink issues, rollback gaps, installer side effects, inventory drift, and publisher preconditions. Fix blockers, then run a targeted independent remediation review.

## Idempotence and disposable installation

After every code or public-artifact mutation that changes fingerprint inputs:

1. Regenerate inventories.
2. Commit the change.
3. Run the complete exporter twice.
4. Require empty change lists, stable accepted-source hash, stable tracked-tree hash, and a clean worktree.

Install every published artifact class into a disposable Hermes home. Prove dry-run writes nothing, installed package trees are byte-exact, Hermes discovers the expected count, personality installation does not imply activation, and `hermes config check` passes. Rich tables may truncate long names; use the CLI summary count or a structured/internal discovery surface rather than substring matching rendered cells.

## Withdrawal closure and verifier hygiene

A withdrawal changes the dependency graph, not only the manifest count:

1. Classify exact public bytes separately from mutable source bytes.
2. After choosing withdrawals, scan every retained package for imperative peer loads (`load`, `skill_view`, required marker/version language), not only frontmatter `related_skills`.
3. Treat a mandatory load of an absent peer as a broken standalone contract even when the retained package paraphrases some peer guidance.
4. Run a focused semantic verifier against the pre-change tree to witness RED, then against the projected final tree to prove GREEN before the broad suite.
5. If this changes the previously approved final manifest, return to an exact user scope decision before deleting the newly implicated dependent package.

Place NUL change lists, captured logs, and verifier outputs outside the repository root. Repository-wide text validators can correctly classify NUL files as forbidden binary public content; that is a fixture-placement bug, not a product failure. For `git archive` fixtures, remember there is no `.git` metadata: use a clone when testing tracked-file behavior, or label the safe-walk fallback explicitly.

## Repository-wide withdrawal references and exact review snapshots

Package removal is incomplete while tracked control-plane or example surfaces can reintroduce the withdrawn package:

- Audit tracked default/fallback candidate lists, example YAML/TOML/JSON configs, installer selections, docs, generated inventories, and tests—not only package trees and Markdown listings.
- Bind tracked default candidate lists to the public manifest with a focused contract test. A clean clone has no local `.git/info` override, so the tracked fallback must never select an absent or withdrawn package.
- Validate public config examples against the current first-party schema. Removing a package name is insufficient when the surrounding key itself is obsolete (for example, an old allow/enable list replaced by a disable list).
- Witness focused RED before changing a fallback or example contract, then regenerate every fingerprint inventory that includes the changed code/test/config bytes.
- Inspect tests for withdrawn names used as “other package” sentinels. Once that package is deleted, an absence assertion can pass vacuously. Replace the sentinel with a different retained manifest package and verify both sentinel names are distinct, manifest-listed, and actually present in the all-packages fixture.
- Distinguish hard dependencies from ecosystem prose. Mandatory `load`, `skill_view`, install, marker, or runtime requirements must close within the final manifest/bundled surface. Advisory `related_skills` metadata and neutral prose about optional external/custom workflows may remain, but classify that intent explicitly in the plan and review brief so it is not mistaken for a dangling operational dependency.
- Decide whether “withdraw” means current-repository removal or permanent reintroduction denial. For permanent withdrawal, add a tracked tombstone/deny policy with tests covering CLI, environment, local allowlist, and publisher paths. If future explicit manual selection remains supported, state that boundary and keep automated publication paused rather than implying a tombstone exists.

Independent review applies to an immutable candidate snapshot:

1. Stage every intended path first, including newly created support files and deletions.
2. Prove there are no unstaged or untracked paths, record the staged path count, and hash `git diff --cached --binary`.
3. Give reviewers the exact base SHA, branch, final manifest, withdrawal set, staged path count, and staged diff digest.
4. Treat any later staged mutation—even a reviewer remediation—as invalidating the verdict; rerun local gates and dispatch fresh reviewers against the new staged digest.
5. Ignore or classify late async verdicts by their reviewed digest and scope rather than assuming the newest-arriving result covers the current tree.

When an execution environment cannot recognize a canonical test command, create a focused ad-hoc verifier with an OS-safe `tempfile` path prefixed `hermes-verify-`. Exercise the changed behavior directly, label the result explicitly as ad-hoc rather than suite-green, remove temporary files when possible, and prove the repository gained no unstaged/untracked residue.

## Publication and reconciliation

Do not equate local green tests with completion. Completion also requires reviewed PR checks, merge, exact remote-main manifest/fingerprint verification, original-checkout reconciliation against the preserved backup, and an explicit publisher paused/resumed decision. Keep the publisher paused until two idempotent hardened-pipeline passes and all remote gates are green.
