# Native Kanban Operation-Parity Slices

Use this reference when a saved plan extends a broker around pinned Hermes Kanban behavior. It captures the vertical-slice shape; live pinned source and the saved plan remain authoritative.

## Reconcile before writing

A delegated audit is valid only for its pinned commit. Compare every claimed gap with current `HEAD`, current native contract data, and the live pinned Hermes callable before selecting work. Remove gaps already closed by later commits.

Before treating a native tool as parity-compatible, classify every observable native action—not only its nominal verb. A list operation that recomputes readiness contains a write; an aggregate show operation may invoke several callables and return a different schema than a simple read. Never smuggle those behaviors under an existing read ledger ID, expose a caller-selectable “native envelope” flag, or bypass ordinary approval/journal policy through an internal adapter. Either model the exact composite contract with truthful operation/approval/journal semantics and board-scale tests, or keep the broker-owned override on an explicit fail-closed compatibility hold so callers cannot bypass it.

## One mutation slice

1. Inspect the exact native callable signature and upstream behavior tests.
2. Write a public broker-boundary RED test first. For CAS-sensitive operations, also prove stale-run rejection leaves native state unchanged.
3. Update every contract layer that applies:
   - pinned native callable contract;
   - immutable operation ledger and expected-operation compatibility test;
   - protocol operation allowlist;
   - bounded argument schema;
   - fixed native callback body;
   - structurally bounded native operation mixin;
   - broker native dispatcher;
   - policy decision/status mapping;
   - durable binding/journal/approval result behavior.
4. Keep worker eligibility, human approval class, retry class, and idempotency/CAS behavior explicit in the ledger.
5. Use real native temporary roots and real Unix sockets. Do not replace boundary behavior with mocks or synthetic broker success.
6. Run focused broker/native/contract tests, then parser-based structural checks, then the full suite. Commit only from a clean GREEN checkpoint.

## Structural pressure

Operation aggregators tend to exceed the 30-line class gate as new methods accumulate. Prefer a new narrowly named mixin module over growing an existing state class past the limit. If a dispatcher or argument/protocol registry is near 200 lines, split a coherent helper module before adding the operation rather than compressing unrelated logic after the fact.

Patch aggregator inheritance lists and operation registries minimally: preserve every existing mixin/call entry, then run the operation-coverage compatibility test immediately. Broad line replacements can silently drop an existing mixin or mapping while the new focused behavior still passes. Re-run parser-based structure checks during REFACTOR, not only after the full suite.

## Auxiliary-model proposal boundaries

When an auxiliary model must propose native Kanban changes without giving the authority service model credentials:

1. Issue a bounded, token-digest-only lease tied to peer UID, profile, board, task, policy version, task fingerprint, expiry, and one idempotency key.
2. Run the unmodified pinned native proposer in a user-side subprocess against an online-backup compatibility snapshot. Pass only an explicit bounded profile environment; reserve and overwrite `HOME`, `PATH`, `PYTHON*`, loader variables, `HERMES_HOME`, `HERMES_PROFILE`, `HERMES_KANBAN_DB`, and `PYTHONPATH` so profile data cannot replace the executable or module path.
3. Derive a deterministic candidate from the snapshot mutation. Permit only current native shapes: a bounded `specify` field delta or a bounded `decompose` sibling graph whose parents are local child indices. Reject caller-supplied idempotency keys, external/cross-board parent selectors, unknown fields, unknown assignees, cycles, empty graphs, and oversized text before consuming the lease.
4. Revalidate profile roster, board/task scope, policy version, and live task fingerprint before `pending → submitted`. Model output is never authority.
5. Apply only through a fixed native callback using the pinned atomic native callable. Maintain `pending → submitted → applied`; an identical applied replay returns the stored terminal state without another native call.
6. Treat the broker database and native Kanban database as separate crash domains. A submitted replay may recover a native write only when the native transaction left a pinned authoritative event/result marker and current native state is congruent with every candidate field and graph edge. Never infer success merely because the root left triage. If the pinned callable lacks a recoverable marker, keep that operation on compatibility hold rather than claiming exactly-once behavior.
7. Pin both callable signatures/body digests and complete proposer-module digests when the launcher depends on adjacent outcome dataclasses or parser helpers; a function-only digest does not protect those shapes.

Test with real snapshots, Unix sockets, and subprocesses. Prove no-credential failure without ambient credential inheritance. For timeout behavior, a real local endpoint that accepts a connection and deliberately does not respond is a valid failure dependency; it tests cancellation without fabricating model success. Also exercise the crash window by reserving `submitted`, completing the real native transaction, and replaying through the public broker boundary to verify congruent recovery and terminalization.

## Late delegated-audit reconciliation

A delegated audit can return after the parent has already reached or committed a GREEN checkpoint. Treat its summary as unverified evidence, then compare every finding with the current committed source—not the dirty base the child observed. If a current high-severity finding invalidates the public contract, reopen the checkpoint immediately under a new RED test and corrective commit; do not defer it merely because the earlier commit was clean. Preserve both commits in history unless the user explicitly requested history rewriting. Record which findings were confirmed, superseded, or deferred behind a later explicit gate.

## Replay-safe launcher checkout

A read-only launcher poll that repeatedly returns the same pending lease is not a safe handoff: different request IDs or response loss can spawn duplicate workers. For a real launcher consumer, use an authenticated checkout contract:

1. Validate canonical board, known profile, enforce-mode policy/registry state, selector shape, and absence of unrelated approval/capability tokens.
2. Re-read authoritative native task state immediately before handoff: exact running status, run ID, assignee/profile, `launch:<lease-id>` claim, claim expiry, and unexpired lease.
3. Validate the launcher principal and CAS `pending → launching` in one sidecar-store transaction. Bind and revalidate the complete kernel process identity: UID, PID, Linux process start time, primary GID, and canonical supplementary groups; PID alone is reusable after process exit, and same-UID siblings need not have the same group authority.
4. Journal the authenticated request fingerprint and chosen lease before CAS. On same-request replay, recover the stored result or the exact reserved lease; a different request ID must not receive an already checked-out lease.
5. If the in-memory request registry normally rejects duplicate IDs, bypass it only for this durable checkout path after frame decoding and kernel peer extraction. The durable journal—not process memory—must decide replay versus conflict.
6. Return a fixed DTO allowlist rather than a raw lease row. Audit non-secret principal/kernel/scope/result fields, never tokens or claim-lock material.
7. Mark expired or authoritatively stale pending leases terminal and return no launch authority.

Prove the contract over real Unix sockets and real stores: same-request replay returns the same DTO; a new request gets no second checkout; wrong profile/PID/process-start is denied; policy quarantine and native drift fail closed; expired leases are terminalized; native authority is unchanged by checkout.

## Pinned-source fixtures after protected-upstream drift

When a live protected Hermes checkout moves away from the plan-pinned commit, do not reset it and do not silently update the pin. Record the new HEAD/status as concurrent or unattributed drift and keep rollout/cutover blocked until compatibility is reviewed.

For continued contract testing, create an isolated temporary clone from the official NousResearch repository and check out the exact pinned commit. Do not derive the fixture from a shallow or grafted local checkout: it may appear to check out successfully while lacking parent/blob objects, then fail contract introspection or tests that clone the fixture. Verify the temporary clone’s object graph before use.

Set the explicit source-root override for tests that honor it. If compatibility tests intentionally inspect `Path.home()/.hermes/hermes-agent`, use an isolated temporary `HOME` whose `.hermes/hermes-agent` points to the complete pinned clone. This preserves the pinned test contract without editing tests or the protected checkout. Report comprehensive results separately from the observed upstream drift; never translate this into a blanket “no drift” claim.

## Client transport parity

A fail-closed client should prove:

- one request per Unix-socket connection;
- bounded newline-delimited frames;
- response/request identity matching;
- malformed, truncated, oversized, timeout, and wrong-version denial;
- retries only for explicitly idempotent reads, or for an explicitly replayable mutation whose identical request ID/fingerprint is protected by durable exactly-once state;
- one absolute monotonic deadline shared by connect/auth/send/receive and every retry—never reset the timeout per attempt;
- identical request ID and frame across every retry;
- no mutation retry after uncertain transport failure unless it uses the explicit durable replay path;
- no native fallback when the broker is unavailable.

Use small real local socket services for fragmented reads/writes and transport failures. They are valid integration dependencies and avoid implementation-detail test doubles.
