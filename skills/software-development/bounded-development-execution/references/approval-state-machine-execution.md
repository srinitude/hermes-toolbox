# Approval State-Machine Execution Checklist

Use this checklist for approval tokens, capabilities, leases, idempotency keys, or other one-use authorization state.

## Model the whole vertical contract before coding

Record the states and transitions explicitly:

```text
minted/pending -> reserved -> completed-operation -> consumed
                 |                         |
                 +-> recovery inspection <-+
```

For every transition, identify:

- exact identity source (kernel/session/server context, never caller labels alone);
- scope fields and canonical fingerprint inputs;
- transaction boundary and compare-and-swap predicate;
- durable journal writes in the same transaction;
- replay, expiry, revocation, mismatch, and concurrency behavior;
- crash state and deterministic recovery output;
- all plaintext-secret exposure channels.

## Security-channel tests belong in the first slice

Before broad verification, prove the same generated token is absent from:

1. database bytes and journal intent/result;
2. `repr()` of issue, request, reservation, grant, and error objects;
3. captured logs and audit/recovery records;
4. returned records other than the single trusted mint response.

For Python dataclasses carrying tokens, use `field(default=..., repr=False)`. Verify this with a failing test before changing the DTO; testing only the mint result can miss leakage from a later request object.

## Atomic reservation test pattern

Use a real SQLite transaction and real constraint failures:

1. CAS the approval from `pending` to `reserved` with every identity/scope/policy/expiry predicate in the `WHERE` clause.
2. Insert the operation-journal intent before committing.
3. Induce a real primary-key or uniqueness conflict in a test.
4. Verify the approval remains pending and the pre-existing journal row is unchanged.
5. Race two real connections/threads and require exactly one winner.

Do not use mocks or exception injection to claim rollback atomicity.

## Consumption and recovery

- Consume only when an exact request-id/fingerprint journal row is completed.
- Use a CAS so concurrent/repeated consumption has exactly one winner.
- Recovery should list reserved-but-unconsumed approvals in deterministic order with journal state/result.
- Recovery inspection must not replay the mutation or change state.

## Exact-value and dispatcher invariants

Treat the approved request bytes as immutable authority, not merely validated input.

- Validate bounded text with `value.strip()` only as an emptiness predicate; return and dispatch the original value. Trimming, normalizing, or rewriting after fingerprinting makes the native mutation differ from the approved operation.
- Build fingerprints only after the request has passed its fixed operation-specific schema, or preserve the exact already-fingerprinted value through every later layer. Never forward arbitrary keyword arguments.
- Reject token-bearing keys recursively before journaling. Journal bounded approved arguments, but never capability/approval tokens or caller-supplied actor labels.
- Derive actor class and principal server-side before native reads or mutations. For worker requests, authorize profile, canonical board, task, run, claim, operation, UID, and PID as one exact capability scope.
- Authenticate completed worker replays explicitly. A capability made terminal by the original completion may be accepted only for the same completed request-id/fingerprint and exact peer/scope; it must remain unusable for a new mutation.

## Mutation ordering and real fault evidence

Use one shared mutation path with this order:

```text
validate -> server-side authorize -> completed-replay check -> resolve current scope
-> evaluate policy -> durable reserve -> pre-native audit -> official native mutation
-> audit native result -> update policy sidecar -> terminalize capability / record result
-> consume human approval -> completion audit
```

Any failure after durable reserve leaves an explicit recovery state; never blind-replay a reserved operation. A completed journal row with a still-reserved approval is also recovery-required, not a successful replay.

Prove ordering with real effects rather than mocks:

- stale native CAS/run input leaves the journal and approval reserved;
- a concurrent identical request applies at most once;
- conflicting content under one request ID is denied without native change;
- an unavailable real audit sink prevents native mutation;
- completed replay returns the recorded result without reapplying native work;
- audit/journal/database bytes and DTO representations contain no raw token.

When native mutation and policy-sidecar persistence use separate transactions, update the sidecar before marking the journal completed. A crash between native success and sidecar completion must remain reserved/ambiguous so recovery cannot falsely report complete policy state.

## Ephemeral human slash-command confirmations

For process-local confirmation commands that deliberately avoid a durable journal, use a smaller but still fail-closed state machine:

```text
preview/mint -> atomic pop/reserve -> validate fresh bindings -> dispatch once
                                      |                     |
                                      +-> burned rejection  +-> success or indeterminate
```

- Keep confirmation human-only: register one slash command, never a model-callable confirm tool.
- Preflight the active profile and every tool/command/skill collision before the first registry write. Registration may initialize process-local cryptographic state, but must not contact the native service.
- Bind the token to the canonical operation, fixed absolute argv, active profile, process nonce, monotonic expiry, native client/server identity, socket/session, exact opaque target IDs, and a deterministic pre-state fingerprint. Include all fields in one integrity hash.
- Atomically remove the record before checking expiry, profile, identity, or pre-state. Exact input succeeds; malformed input containing a known token should burn it and return an ambiguity error. Replays and every rejected reserved token remain unusable.
- Re-read native identity and operation-specific pre-state immediately before mutation. Dispatch the stored allowlisted argv once with `shell=False`; never reconstruct it from slash-command text.
- Treat a transport timeout during mutation dispatch as **indeterminate**, burn the token, and instruct inspection rather than retry. Timeouts during pre-dispatch reads are ordinary service failures because no mutation was sent.
- Bound every slash-command result as valid JSON with fixed human-readable messages; never surface native free text.

Use a real plugin manager and live native service for tests. Cover success plus restoration, replay, expiry, stale pre-state after an intervening real mutation, wrong input, ambiguous-input burn, profile mismatch, and before/after proof that every rejection is mutation-free. A separate fresh process cannot prove profile mismatch for an intentionally process-local token because restart invalidation wins first; in that case, invoke a second profile-bound production handler imported from the module loaded by the real manager rather than mocking storage or dispatch.

## Iteration-budget rule

Complete this security matrix before the first full-suite/final-verification pass. A late secret-channel assertion can legitimately create a new RED and invalidate earlier final-suite evidence, consuming the rounds reserved for commit and clean-tree proof.
