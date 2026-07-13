# Saved-Plan Drift Ledger

Use this during long, multi-checkpoint plan execution when other worktrees, cron jobs, publishers, or background agents may change concurrently.

## Baseline

Before the first write, record for every protected boundary:

- repository HEAD;
- `git status --porcelain=v1` digest and the readable status;
- authoritative plan digest;
- watched publisher/exporter enabled state;
- known pre-existing dirt, with exact paths;
- the development repository HEAD and clean/dirty state.

Do not reduce drift evidence to a digest alone: keep the readable status needed to attribute a later change.

## Checkpoint discipline

After each bounded RED→GREEN slice:

1. Run focused tests, the full relevant suite, parser-based structure checks, compilation/lint, and `git diff --check`.
2. Commit the slice while the tree is green and structurally compliant.
3. Re-read protected boundaries and compare both HEAD and status digest.
4. If an external boundary changed, do not touch or normalize it. Capture the readable status, verify whether watched automation stayed paused, and classify the change as agent-induced, known pre-existing, or concurrent/unattributed.
5. Continue only inside the isolated approved repository when the plan permits; keep publication, rollout, and cutover blocked until external drift is reconciled.

## Candidate-source drift

When publication or migration reads live source trees outside the target worktree, treat those trees as protected boundaries too.

- Hash each relevant candidate package (and the accepted candidate set) before classification, excluding only documented generated/runtime files such as `__pycache__` and usage counters. A single aggregate tree hash is useful for detection but insufficient for attribution.
- Recompute candidate hashes immediately before export and after the bounded export/classification slice. Record both the aggregate and per-candidate changes in the local evidence report.
- If a source changes while a writer is exporting it, do not mix packages from different source snapshots into one acceptance claim. Finish or discard the isolated transaction, reclassify changed candidates from the new snapshot, and regenerate deterministic inventories once.
- A previously exported package may remain only under the explicit last-known-good rule and only after validating that public package itself against the current full contract. Do not silently call an earlier export “current.”
- Runtime churn under a profile root must not create false drift: define the hash include/exclude policy before the baseline and keep it identical at every checkpoint.
- Any unexplained source change is `Concurrent external drift detected`; it invalidates a requested “no drift throughout” claim even when the target branch remains clean.

## Audit reconciliation

A delegated audit is evidence only for its pinned HEAD. If implementation advances while it runs:

- map each finding to the exact pinned commit;
- mark findings superseded by later verified commits;
- independently verify still-relevant findings against current source;
- never report the old audit as current acceptance proof.

## Completion language

Use precise claims:

- `No agent-induced drift observed` only when the write set and protected-boundary comparisons support it.
- `Concurrent external drift detected` when a protected status or HEAD changed without an authorized write.
- Never claim `no drift throughout the entire run` after any unexplained boundary change, even if the target repository is clean and all tests pass.

A final report should include initial and final digests, readable changed paths, attribution, publisher state, untouched boundaries, and blocked gates.
