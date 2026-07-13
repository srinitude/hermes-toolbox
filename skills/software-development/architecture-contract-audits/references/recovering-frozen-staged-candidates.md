# Recovering a frozen staged candidate after index drift

Use when a read-only staged audit began with an exact `git diff --cached --binary | sha256sum` digest, but the index changed before final verification and no full blob-map snapshot was retained.

## Recovery procedure

1. Record the final digest, `git status --short`, `git diff --cached --numstat`, and `git ls-files -s` manifest hash. Do not overwrite or restage anything.
2. Compare final `numstat` with the captured initial output. Changed counts identify some replaced paths, but unchanged counts do **not** prove unchanged content.
3. Inspect index-object mtimes and the newest unreachable blobs (`git fsck --no-reflogs --unreachable`). A newly staged replacement leaves the previous staged blob unreachable unless another ref/index entry still owns it.
4. For each suspected path, compare its current staged blob with candidate unreachable blobs using line count, first-line/module identity, size, and textual similarity. Confirm candidates by reading the complete blob with `git cat-file blob <oid>`.
5. Reconstruct the original patch entirely in memory. Start with the current `git diff --cached --binary` bytes and replace each drifted file section with a section generated from its frozen blob. For a newly added text file, the exact section is:

   ```text
   diff --git a/<path> b/<path>
   new file mode 100644
   index 0000000..<short-blob>
   --- /dev/null
   +++ b/<path>
   @@ -0,0 +1,<line-count> @@
   +<every frozen line>
   ```

   Validate the section generator first by regenerating a current file's section and requiring byte equality with Git's output.
6. Hash the reconstructed complete patch. Recovery is proven only if it exactly equals the originally captured digest.
7. Re-audit every recovered frozen blob. If earlier worktree/index reads differ only in demonstrated non-semantic drift, state that explicitly; otherwise redo affected analysis from the frozen object.
8. Report two separate facts: the frozen candidate verdict and a hard warning that the current index is a different candidate. List exact replacement paths and classify excluded drift separately.

## Important pitfalls

- A matching `numstat` does not mean the blob is unchanged; lint comments, path substitutions, or same-size edits can preserve counts.
- Do not assume the most recent unreachable blob is correct. Prove the complete reconstructed digest.
- `git fsck` may surface unrelated blobs from other object stores or historical work. Match by content and then by the whole-patch digest.
- Do not use this as a substitute for freezing `git ls-files -s` at audit start. It is a recovery path for an already-missed snapshot.
- Candidate-only lint fixes can explain drift without repairing architectural blockers. Keep current-index improvements out of the frozen verdict.
