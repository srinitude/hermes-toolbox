# Parallel Read-Only Audits During One-Writer TDD

Use parallel delegation to accelerate investigation without violating RED→GREEN ownership.

## Safe pattern

1. Keep exactly one writer for the active vertical slice. The parent owns every dirty path from test creation through commit.
2. Delegate only independent read-only work while the slice is dirty. High-value lanes are:
   - adversarial security review,
   - plan-to-implementation gap mapping,
   - compatibility and test-impact analysis.
3. Give every worker a pinned base HEAD and the complete current dirty-path list. State that parent-owned files may be inspected but not modified.
4. Explicitly prohibit edits, commits, installs, publication, profile/runtime mutation, and overlapping full-suite runs.
5. Continue parent work without polling or waiting. Once a worker returns, treat its report as unverified evidence and reconcile each finding against the current files and HEAD.
6. If a report does not return before the slice is sealed, do not claim its findings were used or verified. Record only that the audit was dispatched.
7. Verify report provenance before reading findings: match the requested repository/path, audit goal, pinned HEAD or candidate digest, and prohibited-action contract. A globally shared delegation cache can contain newer reports from unrelated sessions; never select a report by filename timestamp or recency alone. Prefer the result tied to the returned delegation ID. If that linkage is unavailable, reject any report whose content does not restate the expected task and candidate.
8. Once the parent full suite starts, freeze all edits and adjacent exploration. Reconcile late findings only after the checkpoint is clean, or in the next bounded slice.

## Why this works

Parallelism is spent on independent reasoning rather than concurrent mutation. It preserves witnessed RED, avoids sibling-edit races, prevents multiple agents from repairing the same intermediate failure, and still surfaces security or compatibility omissions early enough to influence the parent verification cycle.

## Handoff requirements

A delegated report should include:

- inspected HEAD and dirty-path assumptions,
- exact file and line references,
- acceptance criterion affected,
- minimal corrective recommendation,
- explicit confirmation that no writes or side effects occurred.

The parent must independently run focused tests, the complete suite when required, structural/security gates, commit verification, and drift capture. A subagent summary never substitutes for those proofs.
