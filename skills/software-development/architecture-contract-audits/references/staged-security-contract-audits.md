# Staged security-contract audits

Use this reference when independently reviewing a staged diff that claims to close process-launch, sanitization, schema, caller-binding, or destructive-test blockers.

## Evidence boundary

- Freeze `HEAD`, staged names/stat, staged-vs-unstaged status, and recheck status at the end.
- Also freeze the index object map (`git diff --cached --raw`) and a hash of the complete staged patch. Names and line counts are insufficient: another writer can restage different bytes under the same paths while an audit is running.
- Read staged blobs rather than worktree files whenever unstaged changes exist. For a large review, record each staged path's blob OID so every finding remains attributable to immutable objects.
- Recompute the object map and patch hash before reporting. If either changed, do not approve the currently staged candidate. Distinguish findings proved against the original frozen patch from unreviewed concurrent drift; never silently combine evidence from both generations.
- Treat a changed final hash as a scope-integrity blocker even when `HEAD`, staged paths, `--stat`, and `--numstat` are unchanged. Recompute the hash repeatedly to rule out a transient renderer issue and report both initial and final digests. If no frozen blob map exists, restart from a newly frozen snapshot rather than inferring which same-sized blob changed. If the map was preserved, compare every OID, read drifted replacements separately, and keep two verdicts: findings against the immutable original candidate, and rejection/non-approval of the current index until it receives its own complete review. Test-only or lint-only drift does not erase source findings, but it still changes the exact candidate. This blocker is repository-scope evidence, so explicitly mark file/line as not applicable instead of inventing a source location.
- Keep a frozen raw object map or exported index tree if the audit must survive concurrent restaging; a patch digest proves drift but cannot reconstruct the earlier candidate after the index changes.
- Inspect the complete staged implementation, not only newly added happy-path tests.
- In a read-only review, do not run suites that create services, sessions, temporary homes, or other resources. State which reported test result was supplied rather than observed.
- Pure probes must avoid bytecode/cache artifacts (`PYTHONDONTWRITEBYTECODE=1` or equivalent). If a probe creates an incidental artifact, remove only that exact artifact and verify status again.

## Exact operation-to-argv checks

For every sealed operation, derive the only accepted vector and compare every position, including the child after `--`. Verify:

- the operation record and argv are sealed together;
- dispatch revalidates argv against the canonical operation;
- argv is a fixed list and subprocess execution explicitly uses `shell=False`;
- required literal children remain literal, such as `['hermes', '-p', profile, '--resume', session]`;
- unrelated verbs and tampered child/session values are rejected.

Do not accept a generic basename/length allowlist as operation-specific grammar. Also distinguish grammar integrity from executable replacement/TOCTOU guarantees.

## Incremental process-output checks

Trace both stdout and stderr from pipe creation through completion. Require:

- incremental reads, not `communicate()` followed by a size check;
- an aggregate byte ceiling enforced during capture;
- timeout based on a monotonic deadline;
- kill and wait/reap on timeout, output overflow, and parsing/capture exceptions;
- bounded sanitized error projection rather than native free text.

A cap-only test does not prove timeout kill/reap. Verify source control flow or require a focused timeout/reap test.

## Sanitizer adversarial matrix

Do not infer “full ANSI” from representative CSI or OSC coverage. Build a Cartesian synthetic, non-secret matrix covering:

- ESC and C1 introducers for every CSI, OSC, DCS, SOS, PM, and APC family;
- every supported terminator (ESC ST, C1 ST, and BEL where applicable);
- a separately executed unterminated case for every ESC and C1 family;
- all C0/C1 controls and Unicode `Cf` characters;
- unquoted and single/double-quoted Basic/Bearer values;
- quoted assignments with spaces/escapes;
- folded authorization and cookie headers;
- multipart cookie and set-cookie field values, including quoted and folded forms.

Assert exact surviving text, not just absence of ESC/C1 bytes. In particular, an unterminated CSI sanitizer that strips `ESC [` or C1 CSI but leaves parameters such as `31` is still a concrete payload leak. Run unterminated string controls independently because an unterminated DCS/OSC-like construct legitimately consumes the remainder of its input and would hide later cases in a concatenated probe.

Assert that every control-string payload disappears, not merely the introducer/terminator bytes. Test every model-facing native field, including identity metadata such as socket paths; a shared sanitizer is insufficient if one projection bypasses it. A green remediation suite does not override a failing independent matrix; report the missing matrix row as both a blocker and a test-coverage gap.

## Caller and binding order

Separate three claims:

1. caller identifier presence/shape validation;
2. live caller-to-pane resolution;
3. operation-specific filesystem, executable, and service discovery.

Verify the intended ordering explicitly. A test for a missing caller does not prove stale-caller ordering. Bind and seal profile, canonical socket identity, named session, caller, operation, precondition, argv, process domain, and expiry; confirm must re-read identity/preconditions after atomically consuming the token.

## Closed schemas

For every `oneOf` branch, verify exact required fields, `additionalProperties: false`, and operation-specific properties. Check the real schema engine semantics or a complete validator; a hand-written test evaluator that ignores pattern/min/max constraints is only partial evidence.

## Fail-closed test resources

Random names plus a collision check solve only creation collisions. Also inspect failure paths:

- establish cleanup immediately after process/resource creation, before readiness waits and fixture setup;
- place collision detection before the ownership `try/finally`, so a detected pre-existing resource produces no stop or delete action;
- cleanup must survive partial setup;
- teardown should attempt later cleanup steps even if native stop, terminate, wait, kill, or a second reap fails;
- compare protected topology after normal and recoverable failure paths;
- temporary homes should be uniquely scoped and cleaned where practical.

Use test doubles only when the repository contract permits them. If mocks, stubs, fakes, or spies are forbidden, prove cleanup ordering with real bounded subprocesses/resources and observable public effects instead; do not satisfy this checklist by violating the repository's test policy. When doubles are allowed, event-recording fakes can supplement happy-path fixture execution with traces equivalent to:

- collision: no `Popen`, stop, reap, or delete events;
- setup failure after `Popen`: `Popen -> stop/reap -> delete`;
- native stop failure: terminate plus wait/reap still attempted;
- first wait timeout: kill plus a second wait/reap attempted;
- teardown stop/reap exception: exact owned-resource deletion still attempted.

A `try/finally` beginning after several setup operations can still leak a live test service. Conversely, unconditional deletion outside a proven ownership boundary can destroy a pre-existing collision.

## Reporting

Return the requested machine-readable shape exactly. Set `passed=false` for any demonstrated bypass. Keep unresolved prior blockers separate from newly introduced regressions, cite exact files/lines and probe output, and state tests observed versus merely reported.
