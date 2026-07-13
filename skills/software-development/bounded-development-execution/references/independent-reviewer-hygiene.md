# Independent Reviewer Hygiene and Verdict Reconciliation

Use this when a long implementation run delegates pre-commit or pre-merge review to another agent or an external coding CLI.

## Pin the reviewed tree

- Record the exact staged diff or `parent..HEAD` range before dispatch.
- A review applies only to that range. Any amend, rebase, merge, follow-up fix, or newly staged file invalidates the verdict for the changed delta.
- After fixes, re-review the delta or the complete final range; never stretch an old pass over a newer tree.

## Recompute the verdict locally

Do not trust `passed` alone. Treat the review as failed when any of these is true:

- `security_concerns` contains a concrete issue.
- `logic_errors` contains a concrete issue.
- The payload is truncated, malformed, timed out, or cannot identify its baseline.
- The reviewer says `passed: true` while also describing a real blocker.

Suggestions are non-blocking only when they are genuinely optional. If a suggestion exposes incorrect semantics, a missing fail-closed boundary, stale identity acceptance, or untested sensitive output, promote it to a required fix.

## Contain reviewer side effects

External coding CLIs may initialize project metadata even in plan/read-only mode.

1. Prefer an isolated clean worktree for review.
2. Snapshot `git status --porcelain` before dispatch.
3. Recheck status immediately afterward, including timeout paths.
4. Remove only artifacts proven to be newly reviewer-generated (for example, a newly created `.serena/` directory). Preserve all inherited untracked files.
5. Stage explicit reviewed paths; do not use `git add -A` after a reviewer has run.
6. Require a clean-status proof after commit.

A reviewer timeout is **no verdict**, not a negative claim about the tool and not permission to self-approve. Retry with a fresh independent reviewer or leave the gate pending.

## Live-contract corrections found during rollout

When live acceptance disproves a validator assumption, treat the live failure as RED:

- Verify the identifier grammar or protocol detail against the pinned upstream source.
- Add a focused regression using a real observed shape plus invalid near-misses.
- Patch the shared validator, run the full affected suite, and re-review the new delta.

Do not weaken a validator generically just to accept one observed value. For encoded public IDs, pin the exact upstream alphabet rather than using broad alphanumeric regexes.
