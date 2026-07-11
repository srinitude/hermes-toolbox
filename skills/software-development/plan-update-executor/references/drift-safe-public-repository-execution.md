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

Install every published artifact class into a disposable <repo-author-name> home. Prove dry-run writes nothing, installed package trees are byte-exact, <repo-author-name> discovers the expected count, personality installation does not imply activation, and `hermes config check` passes. Rich tables may truncate long names; use the CLI summary count or a structured/internal discovery surface rather than substring matching rendered cells.

## Publication and reconciliation

Do not equate local green tests with completion. Completion also requires reviewed PR checks, merge, exact remote-main manifest/fingerprint verification, original-checkout reconciliation against the preserved backup, and an explicit publisher paused/resumed decision. Keep the publisher paused until two idempotent hardened-pipeline passes and all remote gates are green.
