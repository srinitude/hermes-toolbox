# Transactional Repository Publishers

## Problem class

An exporter can be internally transactional while the outer publisher is still unsafe. If repository-wide tests, exact staging, commit hooks, or the remote push fail after export succeeds, the checkout may retain exported files, a dirty index, or an unpushed local commit.

## Whole-publication boundary

Require a clean, synchronized starting point before mutation:

```text
HEAD == origin/main
git status --porcelain == empty
git clean -ndx == empty
```

Capture the starting HEAD, then keep one outer transaction open across:

1. candidate export;
2. repository validators and real tests;
3. exact accepted-path staging;
4. commit;
5. push.

Mark the transaction complete only after a genuine no-op or a successful push. Every nonzero return and exception before that point restores the baseline.

With the empty-status and empty-`clean -ndx` preconditions, rollback may safely use:

```text
git reset --hard <captured-head>
git clean -fdx
```

Afterward assert baseline HEAD, empty status, empty cached diff, empty worktree diff, and unchanged remote main. If rollback itself fails, raise a hard error rather than preserving the original lower-level failure code.

## Exact path staging

Never use repository sweeps. For every accepted path:

- existing path or broken symlink: `git add -- <path>`;
- wholly removed tracked path: `git rm -r --cached --ignore-unmatch -- <path>`.

Always include inventory/manifest files explicitly. A path-existence guard that simply skips a missing destination silently loses withdrawals.

## Visibility fail-closed

Do not classify a remote as GitHub with a substring such as `*github.com*`; lookalike hosts can pass that test. Parse only exact approved prefixes, validate the resulting `owner/repo` slug, then require an authoritative API response of exactly `PUBLIC`. Unsupported schemes/hosts and API uncertainty fail closed.

When safety scanners reject an SSH URL because its `user@host` form resembles an email address, construct the `@` token from shell variables rather than weakening the scanner.

## Real regression matrix

Use disposable real Git repositories and hooks, not mocks:

- late repository-test failure after successful export;
- failing real `pre-commit` hook;
- bare-origin `pre-receive` rejection after local commit;
- exception inside the transaction;
- ignored starting residue;
- complete accepted-package deletion;
- unsupported and GitHub-lookalike origins;
- exact GitHub origin with unavailable/non-public visibility proof.

For every late failure, assert local HEAD, remote HEAD, status, cached diff, worktree diff, and publisher-created residue. Run the publisher twice from the final committed state and require silent no-op results before re-enabling automation.

## Operational sequencing

Pause scheduled publication immediately when a late audit finds a fail-open path. Implement and independently review the correction on a feature branch, merge through green CI, reconcile the canonical checkout, run two no-op publisher passes, then resume and exercise the actual scheduled wrapper once. A previous review is evidence only for its pinned tree; follow-up edits require a fresh narrow review.
