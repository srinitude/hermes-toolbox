# Security review remediation for local control plugins

Use this checklist after an independent review finds fail-closed or test-realism gaps in a local Hermes plugin.

## Dispatch boundaries

- Validate a stored command against the **complete canonical operation**, not merely an executable prefix or broad subcommand family.
- For every operation, compare the full fixed-list argv, including argument order and the complete child argv after `--`.
- Keep `shell=False`; reject extra, missing, reordered, or operation-inconsistent arguments before spawning.
- If an integration requires a literal child command form, test the entire vector. Example profile-aware resume contract:
  `['hermes', '-p', profile, '--resume', session]`.

## Output and timeout bounds

- A size check after `subprocess.run(capture_output=True)` is not a memory bound: the child output has already been buffered.
- Use `Popen` with incremental reads from stdout and stderr, enforce an aggregate byte ceiling while reading, and kill/reap immediately on overflow or timeout.
- Test the boundary with a real child process that writes beyond the limit; do not substitute a mocked process.

## Native-string sanitation

Treat every model-facing native string as untrusted, not only terminal text. Apply one shared sanitizer to:

- agent metadata and status fields;
- caller and service identity fields;
- topology labels and native error codes;
- terminal/pane text.

The sanitizer must remove both ESC and C1 forms of CSI, OSC, DCS, SOS, PM, and APC, including terminated and end-of-input/truncated sequences. Unterminated CSI needs an explicit end-of-input alternative before a generic two-byte ESC fallback; otherwise an input such as `prefix + ESC[31` or `prefix + C1-CSI + 31` can leak `prefix31`. Redact complete credential shapes, including quoted and unquoted Basic/Bearer values, folded Authorization/Cookie headers, Cookie/Set-Cookie assignments, multiple semicolon-separated values, and common token prefixes. Bound the result only after sanitation/redaction.

Use a synthetic non-secret adversarial matrix over every CSI parameter byte (`0x30–0x3f`), intermediate byte (`0x20–0x2f`), and final byte (`0x40–0x7e`), plus terminated and truncated string-control forms. A representative happy case is not enough.

## Validation order

Validate the exact profile, socket, live service identity, and caller pane before filesystem checks, executable discovery, or operation construction. This prevents malformed operation inputs from becoming an oracle when the caller is absent or stale.

Exercise absent and stale caller contexts across every public inspect and preview operation, not only one representative path.

## Public schemas

Use closed operation-specific schemas:

- `oneOf` branches with an operation `const`;
- exact `required` fields per branch;
- `additionalProperties: false` per branch;
- bounded enums, strings, and integers.

Validate representative valid and invalid payloads through a fresh real PluginManager registration path.

## Real-test resource hygiene

- Generate unique session/resource names per test process.
- Probe for collision and abort; never delete a pre-existing fixed-name resource during setup.
- Enter the teardown-protected `try/finally` immediately after collision checks and before process launch. Track partial setup (`process=None`, bootstrap caller identity) so failures in `Popen`, readiness, snapshot, or fixture-agent creation still attempt cleanup.
- Nest cleanup so native stop failure cannot prevent terminate/kill-and-reap, session deletion cannot be skipped by wait failure, and protected-resource comparison still runs.
- Use framework-private temporary paths for command-injection sentinels.
- Teardown only resources whose exact generated identity belongs to the test.
- Launch fresh probes with `sys.executable` **without calling `Path.resolve()`**. Resolving a virtualenv interpreter can follow its symlink to the base Python and silently drop the virtualenv dependency context.

## Review-to-commit gate

1. Translate every concrete review blocker into a focused real test.
2. Implement the smallest coherent fix and run focused tests.
3. Run the complete suite, structural limits, compilation, diff checks, prohibited-pattern scan, and generated-cache cleanup.
4. Stage the complete coherent diff.
5. Request a fresh independent review against the staged diff and the earlier blocker list.
6. Do not commit or install until that review passes and the staged tree remains quiescent.
