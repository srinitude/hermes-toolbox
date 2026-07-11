# Large-plan live-state reconciliation and raw validation

Use this reference when a user supplies a large “canonical” architecture/spec that mixes desired behavior, pinned contracts, and claims about the current environment.

## Classify every claim

| Class | Authority |
|---|---|
| Desired outcome or explicit safety rule | Current user request, reconciled with existing non-superseded gates |
| Pinned release behavior | Followed tag/commit plus first-party docs or generated schema |
| Current host/version/config state | Safe live read from the named host or product CLI |
| Private remote resource state | Authenticated direct source; otherwise an explicit access gate/blocker |
| Historical baseline | Preserve as history only when newer live evidence differs |

“Canonical” means the artifact is an important source; it does not make a stale version, setting, or availability claim current forever.

## Reconciliation sequence

1. Read the complete existing plan before editing.
2. Partition the supplied artifact into desired requirements, release contracts, live-state claims, and historical/audit statements.
3. Recheck mutable live-state claims with safe CLI/config-key probes. Do not read secret stores or unrelated runtime content.
4. Follow release tags to target commits and use tagged source/generated schemas for protocol or hook contracts.
5. Create a discrepancy ledger. Put the live value in current-state sections, retain the supplied value only as historical input, and explain the correction in the audit record.
6. Preserve the strictest non-contradictory operational boundary. If the new source describes a generic primitive while the existing plan allows only approved workflows, classify the generic primitive as maintenance/certification-only rather than exposing it operationally.
7. Patch only the approved artifact and keep external side effects behind their existing gates.
8. Re-read large files in explicit chunks and run a deterministic raw-file validator after the last patch.

## Raw-file validation pattern

Record at least:

- raw byte count and physical line count
- SHA-256 digest
- balanced Markdown code fences
- required headings, IDs, capability names, approval gates, and source URLs
- banned legacy terms and stale-current assertions
- conflict/patch markers
- malformed Markdown patterns
- secret-like material
- final newline

A rendered `read_file` preview can be truncated or visually ambiguous. It is useful for semantic review, but byte-level claims must come from the canonical file bytes. If a validator reports that nearly every unrelated requirement is missing while raw size/stat probes look normal, inspect the validator input source first; an empty, wrapped, truncated, or wrongly parsed input can create a false mass failure.

## Pitfalls

- Do not overwrite live evidence with a pasted “current state” table.
- Do not remove stricter approval, privacy, cost, or workflow gates merely because a broader architecture document mentions a generic capability.
- Do not treat anonymous `404`/login results as absence of a private resource.
- Do not claim the file failed validation until the scanner itself is proven to have read the canonical artifact.
- Keep audit wording exact: plan-only edits are different from integration/configuration mutations, while normal retrieval caches may still change.
