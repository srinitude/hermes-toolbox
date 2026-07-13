# Operator CLI, daemon config, and migration-test remediation

Use this note when a read-only phase audit spans a privileged operator shim, broker-backed human CLI, strict daemon config, and schema migrations.

## Smallest contract checks

### Seal the launcher without overconstraining the broker CLI

A registrar-side shim must not accept an arbitrary executable merely because it is absolute and executable. Require the exact internal prefix:

`sys.executable -m <package>.cli _operator`

Keep the argv count and element lengths bounded. Let the strict internal parser validate the suffix. This removes generic code execution while preserving the intended broker operation surface.

When this seal is introduced, rewrite failure-path tests that previously used `python -c`: those commands now fail at argv validation and no longer exercise enrollment or cleanup. Use canonical internal argv for failed-enrollment cleanup tests, and rely on full CLI E2E for successful release.

### Optional board versus broker canonicalization

Reads may carry `board=None` directly to the broker. Mutations may also omit a board when preview resolution is authoritative: the preview can return the canonical board selected from the single visible board or an approved Project binding.

Preview verification should therefore enforce:

- explicit proposed board: returned board must be identical;
- omitted proposed board: returned board must be non-null and is shown to the human before confirmation;
- profile, actor, project reference, operation, request ID, arguments, fingerprint, and token constraints remain exact.

Do not “fix” a preview mismatch by requiring an explicit mutation board if the broker contract intentionally canonicalizes omitted scope.

### Bound operational errors at the public CLI

The parent CLI denial boundary should normalize expected startup failures—broker errors, validation errors, `OSError`, subprocess errors, and enrollment identity mismatches—to one generic machine-readable denial. This includes pipe, spawn, descriptor cleanup, kill, and wait failures. Tests should assert exit status and exact JSON, not exception implementation details.

### Version strict config schemas

Adding required security fields to a closed daemon schema is a schema-version change. Increment the exact accepted config version and update every producer, especially inert installer/bundle rendering. Keep unrelated envelope or manifest versions unchanged. Test current acceptance plus rejection of both the previous version and an unknown future version.

### Remove client fakes without losing adversarial proof

If real subprocess/broker E2E already covers normal read, mutation, and cancellation paths, remove recording-client duplicates. Preserve a hidden-capability or response-tampering guard with a real Unix-socket adversarial relay:

1. start the real broker;
2. forward a genuine preview through a one-frame relay;
3. inject the forbidden field while preserving the genuine fingerprint;
4. call the public operator function through the real transport client;
5. assert denial occurs before confirmation and no mutation is created.

This tests the security invariant without a fake client or fake broker.

### Keep migration expectations independent

Never derive expected migration versions or the next broken migration number from the production `MIGRATIONS` collection. Hard-code the reviewed version sequence and next version in tests, and assert key columns introduced by recent migrations. A new migration should force an intentional expectation update rather than silently moving the oracle.

## Concurrent parent-owned work

During delegated read-only design, the parent may add RED tests or partial production fixes. Record HEAD, staged hash, unstaged hash, and status; re-read any relevant file after hash drift. In the final plan, distinguish already-present partial fixes from remaining changes, and call out newly added tests that assert the opposite of the requested contract.
