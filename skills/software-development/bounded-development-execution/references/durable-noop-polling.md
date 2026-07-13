# Durable No-Op Polling at Broker Boundaries

Use this pattern for launch checkout, queue polling, lease acquisition, health polling, and similar high-frequency broker requests.

## Contract split

Classify the result before writing durable state:

- **True no-op:** no eligible record and no state transition. Return the empty result without reserving an exactly-once journal row, appending a mutation audit event, or retaining the request ID as completed replay state.
- **Successful handoff:** reserve the selected record before CAS, persist the result, and audit the transition. Identical replay returns the stored result without another state-transition audit.
- **Stale-state cleanup:** reserve the selected stale record before terminalizing it, then persist and audit the transition. Never mutate stale state while merely searching, before durable reservation.

Do not solve journal exhaustion by evicting completed exactly-once records on admission. That silently restores replay authority. Separate observational traffic from mutation traffic instead.

## Minimal implementation shape

1. Search read-only for the first matching candidate.
2. If no candidate exists, return `(empty, changed=False)`.
3. If a candidate exists, reserve its identifier and request fingerprint.
4. Perform authoritative validation and CAS/terminalization.
5. Persist the result and return `(result, changed=True)`.
6. At the outer handler, append an event only when `changed=True`.

Keep the `changed` marker internal; do not alter the public response schema solely to control auditing.

## Public RED

Exercise the real socket/handler boundary with more unique idle request IDs than every configured durable capacity, then create a real eligible record and prove:

- every idle result is empty;
- representative idle request IDs are absent from the operation journal;
- no idle mutation events accumulate in the audit chain;
- the subsequent handoff succeeds;
- identical replay returns the same stored result;
- a different request cannot win the same record.

Use a stable or sufficiently long-lived test clock. A finite iterator clock can exhaust during a capacity stress test and surface a misleading generic audit/availability error. When a boundary masks the exception, invoke the same handler directly to recover the underlying traceback before changing production logic.

## Load-oracle discipline

A rapid thousands-of-connections test may measure thread/socket churn rather than a one-poll-per-second production contract. First measure durable row counts after a bounded sample. If durable counts remain zero, distinguish transport-load testing from durability testing rather than weakening either contract.
