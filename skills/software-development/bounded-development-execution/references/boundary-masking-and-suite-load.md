# Boundary Masking and Full-Suite Load

Use this reference when a focused test passes but a long suite reports a generic transport error such as `unavailable`, `connection closed`, or `timeout`.

## Diagnostic ladder

1. **Keep the public RED.** Record the exact boundary error and failing assertion.
2. **Call beneath the mask.** Reuse the same fixture, request, peer identity, and monkeypatch, but invoke the handler directly. Capture the uncensored traceback.
3. **Classify the split.**
   - Direct call fails with a low-level exception: debug that component.
   - Direct call returns the intended domain error while the public full-suite call times out: investigate load/deadline behavior.
4. **Check order.** Use collection order to identify neighboring tests. Run the adjacent sequence before assuming global leakage.
5. **Stress the exact case.** Repeat the single test enough times to distinguish deterministic state corruption from load sensitivity.
6. **Measure duration.** Time only the public call. Compare its distribution with the fixture deadline and the real production deadline.
7. **Repair at the correct layer.** If the fixture uses a shorter deadline than production and healthy calls regularly consume most of it, align the fixture. If production is also near its deadline, fix the slow recovery path instead.

## Integrity-fixture rule

When runtime verification becomes stricter—authenticated genesis, schema seal, manifest, checkpoint, or signature—older fixtures may fail before reaching their intended assertion. Update fixture provisioning through the production initialization primitive. Never disable the verifier or synthesize an unauthenticated placeholder.

## Evidence validity

- A SIGTERM, timeout, partial test stream, or missing numeric exit status is not a pass.
- A full-suite pass from before the latest edit is stale.
- A focused GREEN proves only its changed-path closure.
- Candidate sealing requires a fresh uninterrupted suite and static/structural evidence on the exact final tree.
- Do not run overlapping stateful suites merely to satisfy an external verification marker; shared HOME, profile, daemon, database, or socket state can create false failures.

## Compact evidence record

```text
PUBLIC RED: <command> -> <generic boundary symptom>
DIRECT TRACE: <command> -> <underlying domain/low-level exception>
ADJACENT ORDER: <command> -> <result>
STRESS: <N runs> -> <pass/fail distribution>
TIMING: <range> vs fixture <deadline> vs production <deadline>
FIXED GREEN: focused regression command -> passing result
EXACT TREE: <digest/commit> -> <fresh uninterrupted suite>
```
