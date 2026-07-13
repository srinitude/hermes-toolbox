# Exact-HEAD read-only plan audits

Use this procedure when auditing numbered implementation tasks against the committed Git object while preserving a no-edit/no-live-store boundary.

## Pin the audit subject

1. Capture `git rev-parse HEAD` before reading implementation.
2. Record `git status --short` separately; working-tree state is not evidence about the committed object.
3. If the tree is dirty or changes during the audit, stop using ordinary file reads for implementation evidence. Use `git show <sha>:<path>`, `git ls-tree`, or an exported archive.
4. Re-check HEAD before the report. If it advanced, re-audit or state the exact earlier SHA covered.

## Test only the committed object

```bash
root=$(mktemp -d)
trap 'rm -rf "$root"' EXIT
git archive "$AUDIT_SHA" | tar -x -C "$root"
mkdir -p "$root/.tmp"
cd "$root"
export PYTHONPATH="$root/src:$root"
export PYTHONDONTWRITEBYTECODE=1
export TMPDIR="$root/.tmp"
python -m pytest -p no:cacheprovider -q
```

The interpreter may come from the development environment, but the exported source must come first on `PYTHONPATH`. Keep test databases, sockets, homes, and caches under the temporary root. Remove the root afterward.

## Evidence mapping

For each task:

- Extract its acceptance bullets before inspecting implementation.
- Cite committed source and committed tests separately.
- Distinguish an artifact that exists from one wired into the real enforcement path.
- Treat a green suite as supporting evidence, never proof of spec completeness.
- Use a small deterministic adversarial probe when a security or fail-closed claim is not established by existing tests.

High-value probes include:

- modifying only a disposable clone of a pinned dependency to test contract drift detection;
- preserving a function signature while changing its security-sensitive body, or preserving source markers while changing control flow, to distinguish a real behavioral contract from a signature/marker-only contract;
- comparing runtime validator bounds with checked-in schemas;
- checking response framing against request frame caps and proving the framing/duplicate guard is actually called by the socket server—not merely present as an isolated helper;
- attempting stale capability use after authoritative terminal state;
- sending caller-controlled actor metadata that claims a stronger identity class, while keeping the same real peer credentials, to prove identity is server-derived;
- exercising multi-object scope attacks: a capability valid for the child may still reference an unrelated parent, project, board, or workflow root unless every referenced object is checked;
- executing full lifecycle routes through the actual broker, including dual-authority gates such as worker/orchestrator action plus exact human approval; a pure policy decision can be correct yet unreachable;
- creating a downstream workflow object before its parent evidence is sealed, then completing it after the parent to detect stale or null context-bundle ancestry captured too early;
- exercising the actual broker/handler path instead of only a detached policy evaluator.

Temporary probes may assert that an unsafe action currently succeeds. Their purpose is audit evidence, not regression acceptance; keep them in the disposable export and report the observed bypass precisely.

## Wiring and absence claims

Before calling a requirement implemented, search production call sites from the public entry point to the helper. A correct `SO_PEERCRED` reader, request registry, policy registry, recovery comparator, or workflow evaluator with no production caller is **partial or fail**, not pass. Conversely, when a prohibited live source cannot be inspected, label that as an evidence limitation rather than inferring absence.

## Verdict meanings

Use the user's requested vocabulary. When the requested scale is only `PASS/PARTIAL/FAIL`:

- **PASS** — every criterion has current public-boundary evidence and no valid gap.
- **PARTIAL** — substantive implementation exists, but a criterion is absent from the real boundary, unreachable, insufficiently exhaustive, or insufficiently proven.
- **FAIL** — no substantive implementation exists, behavior directly contradicts the requirement, or an adversarial boundary probe demonstrates a bypass.

Do not promote a criterion because the broad suite is green. For every PARTIAL/FAIL, give the smallest strict-TDD vertical correction: one RED public-boundary reproduction, minimal GREEN wiring, focused verification, then full regression.

Report only gaps valid at the audited SHA. Governance facts that cannot be established without prohibited live-store access are evidence limitations, not invented implementation failures.

## Concurrent-writer pitfall

A worktree may change between two reads without HEAD changing. If that happens:

- pin all subsequent reads and tests to the captured SHA;
- exclude uncommitted concurrent work from verdicts;
- mention it once in the report without attributing it to the auditor;
- never claim a clean tree or current-file content based on an earlier status check.
