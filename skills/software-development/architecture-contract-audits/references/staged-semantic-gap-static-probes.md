# Staged semantic-gap static probes

Use these probes when an exact staged candidate has a supplied green suite but acceptance depends on exhaustive registries, public compatibility surfaces, durable liveness, or test quality. Read staged blobs (`git show :path`) and run Python with `-B`/`PYTHONDONTWRITEBYTECODE=1`; do not import the live worktree without first sealing the index.

## 1. Prove separate set equations

Do not accept one broad “coverage” test. Compute and report these independently:

- protocol operations = argument-schema operations;
- protocol operations = native-ledger operations + explicit non-native operations;
- native mutation operations = dispatch mappings;
- unsupported operations ∩ dispatch mappings = empty;
- registered model tools = pinned native tool set;
- dashboard reads/mutations = eligible ledger reads/mutations;
- pinned public native callables = ledger callables + explicit exclusions;
- every mutating CLI parser path = broker route or explicit hold/exclusion.

Inspect what each existing test actually compares. A test can call itself exhaustive while comparing the ledger only to a hand-selected subset of a larger pinned `public_callables` inventory. Report both cardinalities and representative unclassified mutators.

Treat a currently unreachable unsupported dispatch mapping as stale pseudo-native surface: earlier guards may make behavior fail closed today, but the registry/dispatch equation is still non-exact and future metadata drift can activate dead code.

## 2. Audit durable polling amplification

Trace request-ID generation through every polling loop. For each iteration ask:

1. Is a fresh request ID generated?
2. Is a journal row reserved/completed for an empty/no-op result?
3. What deletes completed rows?
4. What happens at the exact cap?
5. Can a public administrative action restore admission while preserving the replay/conflict horizon?

A fixed cap plus fresh idle polling is a deterministic outage, not bounded storage. Calculate time-to-cap from the configured interval with a tool and cite the complete call chain. Required public proof: many idle polls, bounded durable rows, then newly available work is still discovered.

## 3. Distinguish internal from deployable readiness

An in-process `threading.Event` proves only library readiness. For service acceptance, trace readiness to the actual executable and service manager. `Type=simple` generally reports active before an internal launcher/control-plane probe completes. Record when the public socket becomes reachable relative to control listener, launcher enrollment, post-exec initialization, and authenticated health. Require a real daemon subprocess or service-manager boundary test when deployable readiness is claimed.

## 4. Check published schema/runtime parity

Parse the published JSON Schema and compare it with runtime decoding/validation, not just JSON syntax. Check:

- operation enum/set;
- required versus optional fields;
- non-empty token constraints;
- top-level and nested size/depth/list bounds;
- unknown-field behavior;
- response error/result exclusivity and bounds.

A test that only asserts `additionalProperties: false` or the presence of `oneOf` does not establish schema parity. If the schema is intentionally envelope-only, require that limitation to be explicit in its documentation and identifier.

## 5. Classify test doubles precisely

Static-scan staged tests for `monkeypatch`, `mock`, `MagicMock`, `skip`, `xfail`, TODO markers, and fake client/service classes. Then inspect each match; exception-cleanup `pass` and a caught `NotImplementedError` are not delivery gaps by themselves.

For acceptance races and ambiguous transport recovery, replacement seams are weaker than the public boundary:

- fake client response loss does not prove real Unix-socket replay;
- monkeypatched listener failure does not prove daemon supervision;
- monkeypatched process liveness does not prove PID/pidfd transaction behavior;
- monkeypatched filesystem publication does not prove the real race/rollback path.

Name the smallest real RED needed rather than treating every test-double token as an automatic defect.

## 6. Report supplied versus observed evidence

Keep these separate:

- supplied full-suite/wheel/structure results;
- independently executed static equations and syntax checks;
- focused tests actually run;
- tests deliberately not run to preserve a read-only boundary.

A green supplied suite cannot close a missing semantic equation or public-boundary proof. Final sealing should repeat the exact staged digest producer, index-manifest hash, staged path count, and zero unstaged/untracked counts, and state the repository boundary rather than claiming no files anywhere changed.
