# Public repo PR cleanup and focused upload pattern

Use this when a public toolbox/config/profile repo has leftover dirty state after a PR/merge and the user asks what should be uploaded or says to upload only the best subset.

## Pattern

1. Snapshot the current dirty state before cleanup:
   - `git status --porcelain=v1 > /tmp/<repo>-status-<ts>.txt`
   - `git diff > /tmp/<repo>-dirty-<ts>.patch`
   - `git diff --cached > /tmp/<repo>-staged-<ts>.patch`
2. Reset stale branch/worktree state only after the patch backup exists.
3. Start from clean `origin/main`, then create a focused branch for the intended change.
4. Reapply only the public-safe, in-scope edits. Do not carry over unrelated generated files, deletions, cache artifacts, or stale branch residue.
5. If a broad ignore rule hides a legitimate public artifact, verify it is safe and intentional, then use `git add -f <path>` rather than weakening the ignore rule globally.
6. Re-run the repo validators and fingerprint/inventory updates for every tracked artifact being uploaded.
7. Stage only the intended files, commit with the configured repo identity, push, open a PR, and wait for checks.

## Pitfalls

- Do not upload from a stale feature branch after it has already been merged and deleted remotely; create a new branch from fresh `origin/main`.
- Do not confuse "ignored" with "unsafe". An ignore glob like `**/*secret*` can hide legitimate educational files such as `secret-safety/SKILL.md`; safety must be verified by content and validators.
- Do not run broad `git add .` in a repo that recently generated artifacts. Use explicit path staging, plus `git add -f` only for reviewed ignored files.
- Keep the final response grounded in actual PR/check output and mention any backup patch path if dirty local work was discarded.
