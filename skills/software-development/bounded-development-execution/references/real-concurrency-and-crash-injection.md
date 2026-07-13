# Real Concurrency and Crash-Injection Tests

Use these patterns for authoritative mutation brokers, approval systems, capability stores, and other exactly-once state machines. They preserve real persistence and native behavior while making narrow race/crash windows deterministic.

## Synchronize immediately before reservation

When two requests must both pass policy before competing for one capability or reservation:

1. Wrap the real audit/event sink rather than mocking policy or persistence.
2. Persist the event through the real sink first.
3. When the event marks the post-policy/pre-reservation point, wait on a bounded two-party barrier.
4. Run the two requests with distinct request IDs but the same single-use authority.
5. Assert exactly one atomic reservation and one native mutation; the loser must fail before creating a journal row.

A barrier at the wrong point can prove only the native conflict, not reservation atomicity. Place it after both requests have passed policy but before either can reserve.

## Inject a post-native crash

To exercise the dangerous window between an authoritative native write and sidecar journal completion:

1. Wrap the real audit/event sink and continue writing real audit records.
2. Raise a deterministic exception when the post-native-result event is observed.
3. Verify that the native effect exists while the operation journal and approval remain reserved.
4. Retry through the normal runtime, not the crashing wrapper.
5. Recovery must inspect authoritative post-state and must not blindly replay the native mutation.

This is fault injection, not a fake native adapter: the test still executes the real temporary-root native implementation and real policy store.

## Recovery classifications

- **Uniquely observable/idempotent:** Recover only when exactly one authoritative record matches a broker-owned key, such as the request ID used as a native idempotency key. Persist the observed result and finish approval consumption without replay.
- **Completed journal, reserved approval:** If fingerprint, request ID, journal state, and challenge ID all match, consume the already-reserved approval and return the stored result.
- **Ambiguous/non-idempotent:** Comments, notifications, or other effects without a unique authoritative marker must remain `recovery_required`. Prove that retry does not duplicate the effect.
- **No observed effect:** Do not assume absence means safe replay unless the native contract makes the operation idempotent and the observer covers every authoritative outcome.

## Atomic terminal capabilities

For terminal worker operations, reserve the operation journal row and transition the capability to terminal in one database transaction *before* calling native mutation. Two request IDs using the same capability must have one transaction winner. If the process dies afterward, recovery may remain blocked, but duplicate authority cannot be granted.

## Required assertions

- One native effect, never merely one successful response.
- One operation-journal reservation for a single-use authority race.
- Exact challenge/capability terminal state.
- Same request replay returns the persisted result only after fingerprint/scope checks.
- Different request IDs or altered arguments are denied.
- Barrier waits have timeouts so a broken test fails instead of hanging.
- Fault-injection wrappers are removed for the recovery attempt.
