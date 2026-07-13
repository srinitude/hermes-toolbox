# Remaining-Phase Traceability Matrices

Use this when an implementation plan is only partly represented in the repository and the user wants exact traceability for every remaining phase without writes.

## Evidence boundaries

Keep these layers separate in every row:

1. **Frozen committed object** — behavior and tests present at the literal audited SHA.
2. **Parent-owned worktree** — inspect staged/unstaged/untracked work, but never attribute it to the commit.
3. **Pinned external consumer** — inspect the exact source revision named by the compatibility contract, not an adjacent current checkout.
4. **Live or installed state** — report only when explicitly inspected; source-copy tests are not installation proof.
5. **Approval provenance** — a phase label, plan sentence, or earlier approval cannot authorize a later live gate.

If the authoritative plan file is unavailable but the user supplied phase names and goals, preserve those labels and say that acceptance wording was reconstructed from supplied context. Do not invent semantics for opaque task IDs. Mark an identifier such as `p3a` as externally blocked/untraceable when it has no repository artifact, and name the exact prerequisite needed to resolve it.

## Matrix row contract

For each remaining phase, record:

- phase and preserved goal;
- state: `pass`, `partial`, `fail`, `blocked`, or `not started`;
- committed evidence with exact file:line locations;
- worktree-only evidence, clearly labeled;
- public tests present versus tests actually run;
- concrete missing acceptance criteria;
- blockers in dependency order;
- the smallest coherent next slice;
- whether the next step is repository-local, installed-state, privileged, live, or publication-gated.

A concise table can summarize the result, but put enough exact evidence in each row that the decision is reproducible.

## False-friend checks

### Kernel-bound operator CLI

Do not accept process-binding primitives as an operable CLI by themselves. Check:

- kernel peer PID/UID/GID and process start time;
- direct-child and pidfd liveness validation;
- atomic binding generation and expiry;
- approval fingerprint binding to the exact process generation;
- a production registrar path capable of spawning the configured operator identity;
- real separated-identity proof, not a same-UID E2E or monkeypatched process identity;
- absolute frame deadlines, bounded connection saturation, drain, and shutdown;
- exhaustive ledger/dispatch coverage and, when parity is claimed, native parser verb/path/alias/flag semantics.

A daemon test that pre-seeds the test process as the human principal bypasses enrollment and is not operator-path proof.

### Dashboard posture

A ledger-derived list of reads and mutations is not an exact dashboard posture. AST-inventory the pinned backend by HTTP method, path, and WebSocket route. Include mutation routes outside the native operation ledger, such as attachments, bulk edits, run termination, dispatch, profile changes, orchestration settings, board switching, and auxiliary specify/decompose operations.

Report separately:

1. declarative manifest exactness;
2. runtime route disablement/unmounting;
3. replacement broker-backed read fidelity;
4. real-process dashboard identity and socket authorization.

### Shadow mode

A stored `shadow` string or constructor acceptance is not shadow behavior. Trace mutation policy checks and dispatch gates: if they require exact `enforce`, shadow is quarantine. Require an append-only idempotent decision record, exact policy identity/version, would-allow/would-deny, decision code, observed native outcome, digest, timestamp, replay behavior, redaction, and measurable acceptance thresholds.

### Rollout and rollback

Treat these as blockers, not documentation gaps:

- socket-path absence used as service-quiescence proof;
- database-only backup inventories;
- fresh-staging restore presented as exact live-target restore;
- source-copy/PYTHONPATH plugin tests presented as installed-wheel proof;
- broker-spawned launcher/workers sharing the database-owner UID presented as sole-writer isolation;
- a dirty candidate used as release provenance.

## Smallest-slice ordering

Default dependency order:

1. seal the current dirty phase and commit it;
2. add one strict inert deployment-posture envelope;
3. perform isolated exact-object review and repair findings;
4. implement real shadow semantics;
5. generate the environment-specific exact cutover manifest;
6. stop for separately reviewed approval;
7. execute live cutover only from the approved manifest.

Do not begin later-phase code merely because its files are independent when acceptance depends on a clean earlier commit.

## Read-only reporting discipline

- Do not run tests when the requested boundary forbids cache or fixture writes.
- Static AST parsing, Git-object inspection, and route inventory are probes, not test results.
- Recheck every audited repository and pinned consumer at the end.
- State both `tests present` and `tests executed`.
- Confirm repository writes separately from incidental tool-managed temporary output. If a retrieval tool stores oversized results under `/tmp`, disclose it as outside-repository tool output rather than claiming literally zero filesystem writes.
